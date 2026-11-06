"""Voluntary contributions; never unlock content or create student accounts."""
import hashlib,hmac,re,uuid
from flask import Blueprint,current_app,jsonify,g,abort
from . import limiter
from .api import body,require_visitor
from .client_ip import ip_key
from .models import db,SupportOrder

support=Blueprint('support',__name__,url_prefix='/api')

class PaymentAuthError(Exception):pass

def credentials():
    key=current_app.config.get('RAZORPAY_KEY_ID','').strip()
    secret=current_app.config.get('RAZORPAY_KEY_SECRET','').strip()
    if not key or not secret:abort(503,description='Support payments are not configured yet.')
    return key,secret

def gateway(action):
    # Import only on payment requests. Do not occupy the DB pool during I/O.
    import requests,razorpay
    class PaymentSession(requests.Session):
        def request(self,*args,**kwargs):
            kwargs.setdefault('timeout',(3,12))
            r=super().request(*args,**kwargs)
            if r.status_code in (401,403):raise PaymentAuthError()
            return r
    with PaymentSession() as session:
        try:return action(razorpay.Client(auth=credentials(),session=session,max_retries=0))
        except PaymentAuthError:
            abort(401,description='Payment provider authentication failed. Please contact MauryaHub.')
        except (requests.RequestException,razorpay.errors.BadRequestError,razorpay.errors.GatewayError,razorpay.errors.ServerError,ValueError):
            # Provider exceptions may contain identifiers or request details.
            current_app.logger.warning('razorpay_request_failed')
            abort(500,description='Payment provider is temporarily unavailable. Please retry.')

@support.post('/create-order')
@limiter.limit('5 per minute')
@limiter.limit('60 per hour',key_func=ip_key)
@require_visitor
def create_order():
    payload=body();amount=payload.get('amount');currency=payload.get('currency','INR')
    if type(amount) is not int or not 100<=amount<=1000000:
        abort(400,description='Choose a support amount from ₹1 to ₹10,000 (integer paise).')
    if currency!='INR':abort(400,description='Support payments use INR.')
    key,_=credentials();receipt='mh_'+uuid.uuid4().hex
    db.session.remove()
    result=gateway(lambda c:c.order.create(data={'amount':amount,'currency':currency,'receipt':receipt}))
    if not isinstance(result,dict):abort(500,description='Could not prepare your support payment. Please retry.')
    order_id=result.get('id','')
    if not re.fullmatch(r'order_[A-Za-z0-9]+',order_id) or result.get('amount')!=amount or result.get('currency')!=currency:
        abort(500,description='Could not prepare your support payment. Please retry.')
    db.session.add(SupportOrder(order_id=order_id,receipt=receipt,guest_hash=g.guest_hash,
                               key_id=key,amount=amount,currency=currency,status='created'))
    db.session.commit()
    return jsonify(order_id=order_id,amount=amount,currency=currency,key_id=key,test_mode=key.startswith('rzp_test_')),201

@support.post('/verify-payment')
@limiter.limit('20 per minute')
@require_visitor
def verify_payment():
    payload=body()
    order_id=payload.get('razorpay_order_id');payment_id=payload.get('razorpay_payment_id');signature=payload.get('razorpay_signature')
    if not isinstance(order_id,str) or not re.fullmatch(r'order_[A-Za-z0-9]+',order_id) or not isinstance(payment_id,str) or not re.fullmatch(r'pay_[A-Za-z0-9]+',payment_id) or not isinstance(signature,str) or not re.fullmatch(r'[a-fA-F0-9]{64}',signature):
        abort(400,description='Payment ID, order ID and signature are required.')
    order=SupportOrder.query.filter_by(order_id=order_id,guest_hash=g.guest_hash).first()
    if order is None:abort(400,description='Unknown support order for this browser.')
    key,secret=credentials()
    if order.key_id!=key:abort(400,description='Payment configuration changed. Please contact support about this order.')
    expected=hmac.new(secret.encode(),(order.order_id+'|'+payment_id).encode(),hashlib.sha256).hexdigest()
    if not hmac.compare_digest(expected,signature):abort(400,description='Payment signature verification failed.')
    if order.status=='captured' and order.payment_id==payment_id:
        return jsonify(success=True,paid=True,status='captured')
    amount,currency=order.amount,order.currency
    db.session.rollback()
    payment=gateway(lambda c:c.payment.fetch(payment_id))
    if not isinstance(payment,dict) or payment.get('order_id')!=order_id or payment.get('amount')!=amount or payment.get('currency')!=currency:
        abort(400,description='Payment details do not match this support order.')
    status=payment.get('status')
    if status not in ('authorized','captured'):abort(400,description='Payment has not been completed.')
    # Concurrent status checks must never downgrade captured -> authorized.
    SupportOrder.query.filter_by(order_id=order_id,guest_hash=g.guest_hash).filter(SupportOrder.status!='captured').update(
        {'payment_id':payment_id,'status':status},synchronize_session=False)
    db.session.commit()
    saved=SupportOrder.query.filter_by(order_id=order_id,guest_hash=g.guest_hash).one()
    return jsonify(success=True,paid=saved.status=='captured',status=saved.status)
