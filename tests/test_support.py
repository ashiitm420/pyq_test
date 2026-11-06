import hashlib,hmac
from types import SimpleNamespace
import pytest
from backend.models import SupportOrder,db
from conftest import login

@pytest.fixture
def provider(app,monkeypatch):
    from backend import support
    app.config.update(RAZORPAY_KEY_ID='rzp_test_fake',RAZORPAY_KEY_SECRET='fake-test-secret')
    calls=[]
    payment={'order_id':'order_demo','amount':5000,'currency':'INR','status':'captured'}
    def create(data):calls.append(data);return {'id':'order_demo','amount':data['amount'],'currency':data['currency']}
    sdk=SimpleNamespace(order=SimpleNamespace(create=create),payment=SimpleNamespace(fetch=lambda _:payment))
    monkeypatch.setattr(support,'gateway',lambda action:action(sdk))
    return calls,payment

def create(client,amount=5000):
    h=login(client)
    return h,client.post('/api/create-order',json={'amount':amount,'currency':'INR'},headers=h)

def signed(order='order_demo',payment='pay_demo'):
    return dict(razorpay_order_id=order,razorpay_payment_id=payment,
                razorpay_signature=hmac.new(b'fake-test-secret',(order+'|'+payment).encode(),hashlib.sha256).hexdigest())

def test_create_and_verify_owned_order(client,provider):
    h,r=create(client)
    assert r.status_code==201 and r.json['order_id']=='order_demo' and r.json['amount']==5000
    assert r.json['test_mode'] and r.json['key_id']=='rzp_test_fake'
    assert 'secret' not in str(r.json)
    assert len(provider[0][0]['receipt'])<=40
    assert client.post('/api/verify-payment',json=signed(),headers=h).json['paid']
    assert SupportOrder.query.one().status=='captured'
    # Callback replay does not duplicate the receipt or payment ledger.
    assert client.post('/api/verify-payment',json=signed(),headers=h).json['paid']
    assert SupportOrder.query.count()==1

@pytest.mark.parametrize('amount',[None,True,99,-1,100.5,'5000',1000001])
def test_invalid_amount_never_contacts_provider(client,provider,amount):
    assert create(client,amount)[1].status_code==400
    assert provider[0]==[]

def test_minimum_amount_and_csrf(client,provider):
    assert client.post('/api/create-order',json={'amount':100}).status_code==403
    assert create(client,100)[1].status_code==201

def test_signature_missing_mismatch_unknown_and_ownership(app,client,provider):
    h,_=create(client)
    for data in [{}, {**signed(),'razorpay_signature':'0'*64},signed('order_other')]:
        assert client.post('/api/verify-payment',json=data,headers=h).status_code==400
    other=app.test_client();other_h=login(other)
    assert other.post('/api/verify-payment',json=signed(),headers=other_h).status_code==400
    assert SupportOrder.query.one().status=='created'

def test_authorized_is_not_captured_and_amount_must_match(client,provider):
    h,_=create(client);provider[1]['status']='authorized'
    result=client.post('/api/verify-payment',json=signed(),headers=h)
    assert result.status_code==200 and result.json['success'] and not result.json['paid']
    provider[1]['amount']=1
    assert client.post('/api/verify-payment',json=signed(),headers=h).status_code==400
    assert SupportOrder.query.one().status=='authorized'

def test_provider_auth_errors_and_timeouts_are_sanitized(app,client,monkeypatch):
    import requests
    from backend.support import PaymentAuthError
    app.config.update(RAZORPAY_KEY_ID='rzp_test_fake',RAZORPAY_KEY_SECRET='fake-test-secret')
    def unauthorized(*args,**kw):raise PaymentAuthError('never leak')
    monkeypatch.setattr(requests.Session,'request',unauthorized)
    h=login(client);r=client.post('/api/create-order',headers=h,json={'amount':100})
    assert r.status_code==401 and 'never leak' not in r.text
    def timeout(*args,**kw):raise requests.Timeout('never leak')
    monkeypatch.setattr(requests.Session,'request',timeout)
    r=client.post('/api/create-order',headers=h,json={'amount':100})
    assert r.status_code==500 and 'never leak' not in r.text
    assert SupportOrder.query.count()==0

def test_missing_configuration_and_private_caching(app,client):
    app.config.update(RAZORPAY_KEY_ID='',RAZORPAY_KEY_SECRET='')
    h=login(client);r=client.post('/api/create-order',headers=h,json={'amount':100})
    assert r.status_code==503 and r.headers['Cache-Control']=='no-store'
    shell=client.get('/about')
    assert 'https://checkout.razorpay.com' in shell.headers['Content-Security-Policy']
    assert 'checkout.js' not in shell.text
