"""Bounded staging-only learner lifecycle test. Never target production."""
import argparse,concurrent.futures,http.cookiejar,json,time,urllib.request,urllib.parse

def main():
    p=argparse.ArgumentParser(description=__doc__)
    p.add_argument('--base-url',required=True)
    p.add_argument('--paper-id',type=int,required=True)
    p.add_argument('--users',type=int,default=2)
    p.add_argument('--confirm-isolated-staging',action='store_true',required=True)
    a=p.parse_args();base=a.base_url.rstrip('/')
    host=urllib.parse.urlsplit(base).hostname
    if not host or host in ('mauryahub.in','www.mauryahub.in','pyq-test-1.onrender.com'):
        p.error('Production hosts are forbidden. Use a disposable staging database and service.')
    if not 1<=a.users<=20:p.error('Use 1–20 users, increasing in small stages.')
    def learner(_):
        op=urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))
        timings={};csrf=''
        def call(path,payload=None):
            started=time.perf_counter()
            r=op.open(urllib.request.Request(base+'/api'+path,data=json.dumps(payload).encode() if payload is not None else None,
                headers={'Content-Type':'application/json','X-CSRF-Token':csrf}),timeout=45)
            with r:result=json.load(r)
            timings[path.split('?')[0]]=round((time.perf_counter()-started)*1000,1)
            return result
        try:
            csrf=call('/session')['csrf'];call('/home');call('/papers?available=true&limit=1')
            attempt=call('/attempts?bootstrap=1',{'paper_id':a.paper_id,'mode':'exam','duration_seconds':600})
            aid=attempt['id'];qid=attempt['items'][0]['question']['id']
            # Review marking exercises the durable answer-write transaction
            # without assuming a question type or inventing a correct key.
            call(f'/attempts/{aid}/answers',{'items':[{'question_id':qid,'marked':True}]})
            call(f'/attempts/{aid}/submit',{})
            return {'ok':True,'ms':timings}
        except Exception as e:return {'ok':False,'error_type':type(e).__name__,'ms':timings}
    with concurrent.futures.ThreadPoolExecutor(max_workers=a.users) as pool:
        results=list(pool.map(learner,range(a.users)))
    print(json.dumps({'users':a.users,'results':results},indent=2))
    return int(any(not r['ok'] for r in results))

if __name__=='__main__':raise SystemExit(main())
