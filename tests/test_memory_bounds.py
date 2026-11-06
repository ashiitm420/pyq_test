import threading,time
from types import SimpleNamespace
import pytest
from backend import content_cache as cache


@pytest.fixture
def small_cache(app):
    cache._local_clear()
    app.config.update(CONTENT_CACHE_URL='',LOCAL_CONTENT_CACHE_BYTES=25000)
    yield
    cache._local_clear()


def test_cache_evicts_by_bytes_and_skips_oversized_values(app,small_cache):
    cache._local_put('a','a'*10000)
    cache._local_put('b','b'*10000)
    assert cache._local_get('a') is not None  # a is most recently used.
    cache._local_put('c','c'*10000)
    assert cache._local_get('b') is None
    assert cache._local_get('a') is not None
    assert cache.local_cache_usage()['estimated_bytes']<=25000
    calls=[]
    def large():calls.append(1);return 'x'*30000
    assert len(cache.cached('large',large))==30000
    assert len(cache.cached('large',large))==30000
    assert len(calls)==2
    cache.forget('a')
    assert cache.local_cache_usage()['entries']==1
    cache._local_clear()
    assert cache.local_cache_usage()=={'entries':0,'estimated_bytes':0}


def test_expired_cache_entries_release_bytes_without_another_lookup(app,small_cache,monkeypatch):
    clock=[1.0];monkeypatch.setattr(cache.time,'monotonic',lambda:clock[0])
    app.config['CONTENT_CACHE_TTL']=5
    cache._local_put('expired','a'*10000)
    clock[0]=7
    cache._local_put('new','b'*10000)
    assert cache.local_cache_usage()['entries']==1
    assert 'expired' not in cache._local_cache


def test_analytics_saturation_uses_backpressure_without_extra_threads(app,monkeypatch):
    from backend import analytics
    app.config['TESTING']=False
    entered=threading.Event();release=threading.Event();finished=threading.Event();calls=[]
    def write(*args):
        calls.append(threading.current_thread().name)
        if threading.current_thread().name=='pyq-analytics':
            entered.set();release.wait(5);finished.set()
    monkeypatch.setattr(analytics,'_write_analytics',write)
    context=dict(paper_key='paper',paper_name='paper',course_key='course',course_name='course',device='desktop',browser_key='browser',initial_mode='practice')
    attempt=SimpleNamespace(id=1,started_at=time.time(),submitted_at=None,expires_at=time.time()+3600,analytics_context=context,mode='practice')
    try:
        analytics.record(attempt,post_commit=True)
        assert entered.wait(2)
        analytics.record(attempt,post_commit=True)
        assert calls==['pyq-analytics',threading.current_thread().name]
    finally:
        release.set();assert finished.wait(2)


def test_processing_gate_rejects_overlap_and_releases_on_error(app):
    entered=threading.Event();release=threading.Event();result=[]
    endpoint='admin.upload_pyq'
    def busy():
        entered.set();release.wait(5);return {'ok':True}
    original=app.view_functions[endpoint];app.view_functions[endpoint]=busy
    def first():
        with app.test_client() as c:
            h={'X-CSRF-Token':c.get('/api/session').json['csrf']}
            result.append(c.post('/api/admin/upload-pyq',headers=h).status_code)
    thread=threading.Thread(target=first)
    thread.start()
    try:
        assert entered.wait(2)
        with app.test_client() as c:
            h={'X-CSRF-Token':c.get('/api/session').json['csrf']}
            response=c.post('/api/admin/upload-pyq',headers=h)
            assert response.status_code==409 and response.json['code']=='PROCESSING_BUSY'
            assert response.headers['Retry-After']=='5'
    finally:
        release.set();thread.join(3);app.view_functions[endpoint]=original
    assert result==[200]
    def invalid():raise ValueError('invalid test upload')
    app.view_functions[endpoint]=invalid
    try:
        with app.test_client() as c:
            h={'X-CSRF-Token':c.get('/api/session').json['csrf']}
            assert c.post('/api/admin/upload-pyq',headers=h).status_code==400
            app.view_functions[endpoint]=lambda:{'ok':True}
            assert c.post('/api/admin/upload-pyq',headers=h).status_code==200
    finally:app.view_functions[endpoint]=original


def test_ocr_caps_pixels_and_frees_pixmap_before_tesseract(tmp_path,monkeypatch):
    import fitz
    from backend import visual_pdf
    matrices=[];freed=[]
    class Pixmap:
        def save(self,path):path.write_bytes(b'placeholder')
        def __del__(self):freed.append(True)
    class Page:
        rect=fitz.Rect(0,0,3000,3000)
        def get_text(self,*args):return {'blocks':[]}
        def get_drawings(self):return []
        def get_pixmap(self,**kw):matrices.append(kw['matrix']);return Pixmap()
    monkeypatch.setattr(visual_pdf.shutil,'which',lambda *args:True)
    def ocr(*args,**kw):
        assert freed  # Do not retain the parent raster during subprocess OCR.
        return SimpleNamespace(stdout='')
    monkeypatch.setattr(visual_pdf.subprocess,'run',ocr)
    visual_pdf.layout_document([Page()],tmp_path,'large')
    assert len(matrices)==1
    assert 3000*3000*matrices[0].a*matrices[0].d<=8000001


def test_marker_color_analysis_uses_small_arrays(monkeypatch):
    import io,numpy as np
    from PIL import Image
    from backend import visual_pdf
    data=io.BytesIO();Image.new('RGB',(512,512),(0,180,0)).save(data,format='PNG')
    original=np.asarray;sizes=[]
    def bounded(image,**kw):sizes.append(image.size);return original(image,**kw)
    monkeypatch.setattr(visual_pdf.np,'asarray',bounded)
    assert visual_pdf.pixels_kind(data.getvalue())=='green'
    assert sizes==[(256,256)]
