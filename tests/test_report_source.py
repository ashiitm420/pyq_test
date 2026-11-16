from backend.models import db,Question,ContentReport,IngestionFile,IngestionBatch,User
from backend.storage import write_asset
from conftest import login
from test_engine import seed
from test_storage_r2 import remote


def setup_source():
    paper=seed();q=Question.query.filter_by(paper_id=paper.id).first()
    batch=IngestionBatch(user_id=User.query.filter_by(role='ADMIN').first().id)
    db.session.add(batch);db.session.flush()
    old=IngestionFile(batch_id=batch.id,paper_id=paper.id,filename='original.pdf',path='sources/original.pdf',status='AVAILABLE')
    db.session.add(old);db.session.flush();q.ingestion_file_id=old.id
    db.session.add(IngestionFile(batch_id=batch.id,paper_id=paper.id,filename='replacement.pdf',path='sources/replacement.pdf',status='AVAILABLE'))
    report=ContentReport(question_id=q.id,guest_hash='a'*64,issue='OTHER',status='OPEN')
    db.session.add(report);db.session.commit()
    return paper,q,report


def test_report_source_is_admin_only_and_opens_exact_complete_pdf_inline(app,client):
    paper,q,r=setup_source();write_asset('sources/original.pdf',b'%PDF-original complete document')
    url=f'/api/admin/content-reports/{r.id}/source'
    assert client.get(url).status_code==401
    login(client,True);res=client.get(url)
    assert res.status_code==200 and res.mimetype=='application/pdf'
    assert res.data==b'%PDF-original complete document'
    assert res.headers['Content-Disposition'].startswith('inline;')
    assert 'no-store' in res.headers['Cache-Control']


def test_r2_report_pdf_redirects_inline_without_downloading_or_copying(app,client,remote):
    paper,q,r=setup_source();login(client,True)
    res=client.get(f'/api/admin/content-reports/{r.id}/source')
    assert res.status_code==302 and 'sources/original.pdf' in res.headers['Location']
    assert remote.last_presign['ResponseContentDisposition']==f'inline; filename="paper-{paper.id}.pdf"'
    assert remote.last_presign['ResponseContentType']=='application/pdf'
    assert remote.puts==0 and not remote.objects
    # The public download remains an attachment, not changed by this option.
    res=client.get(f'/api/papers/{paper.id}/source')
    assert res.status_code==302 and 'sources/replacement.pdf' in res.headers['Location']
    assert remote.last_presign['ResponseContentDisposition'].startswith('attachment;')


def test_manual_question_falls_back_to_its_paper_pdf_and_missing_report_is_404(app,client,remote):
    paper,q,r=setup_source();q.ingestion_file_id=None;db.session.commit();login(client,True)
    assert 'sources/replacement.pdf' in client.get(f'/api/admin/content-reports/{r.id}/source').headers['Location']
    assert client.get('/api/admin/content-reports/999999/source').status_code==404
    IngestionFile.query.filter_by(paper_id=paper.id).update({'path':None});db.session.commit()
    assert client.get(f'/api/admin/content-reports/{r.id}/source').status_code==404
