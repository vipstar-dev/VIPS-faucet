# coding: utf8

from flask import Flask, render_template, session, request
from flask_wtf import FlaskForm, RecaptchaField
from wtforms import StringField, FloatField, validators
from sqlalchemy import desc
from datetime import datetime, timedelta
import uuid

from .app import app, rpc, balance
from .database import db
from .model import Queue, QUEUE_STATE
from .VIPSrpc import round_satoshi

class FaucetForm(FlaskForm):
    address = StringField(u'VIPS Address', validators=[validators.DataRequired()])
    amount = FloatField(u'Amount(VIPS)', validators=[validators.DataRequired(), validators.NumberRange(min=0.01, max=100)])
    recaptcha = RecaptchaField()

#過剰払い出しの抑制のための制限
#・同一IPに対して1日5回まで
#・同一アドレスに対して1日5回まで
def check_restriction(address, remote, sessionid):
    yesterday = datetime.now() - timedelta(days=1)
    queue = Queue.query.filter(Queue.date >= yesterday, Queue.remote == remote).all()
    app.logger.debug("check_restriction: remote: %s", len(queue))
    if len(queue) >= 5:
        return False
    
    queue = Queue.query.filter(Queue.date >= yesterday, Queue.address == address).all()
    app.logger.debug("check_restriction: address: %s", len(queue))
    if len(queue) >= 5:
        return False
    
    queue = Queue.query.filter(Queue.date >= yesterday, Queue.sessionid == sessionid).all()
    app.logger.debug("check_restriction: sessionid: %s", len(queue))
    if len(queue) >= 5:
        return False
    
    return True

@app.route('/', methods=('GET', 'POST'))
def index():
    msg = ""
    accepted = False
    form = FaucetForm()

    #セッション内にセッションIDがなければ作っておく
    if not session.has_key('sessionid') or not isinstance(session['sessionid'], str):
        session['sessionid'] = uuid.uuid4().hex
        app.logger.debug("sessionid=%s", session['sessionid'])

    #POSTデータがあって、有効な値が入っているかチェック
    if form.validate_on_submit():
        address = form.address.data
        amount = round_satoshi(form.amount.data)
        remote =  request.remote_addr

        #アドレスと送金量は正しい？
        if rpc.checkaddr(address) and amount > 0:

            #送金回数制限に引っかかっていない？
            if check_restriction(address, remote, session['sessionid']):
                q = Queue(address, amount, remote, session['sessionid'])
                db.session.add(q)
                db.session.commit()
                msg = "Successful Queued!"
                accepted = True
            else:
                msg = "Too many requests!"
        else:
            form.address.errors = ["invalid address format or amount!"]
    
    #トップページに乗せる送金履歴(30件)
    queue = Queue.query.order_by(desc(Queue.id)).limit(30).all()

    #HTML作成
    return render_template('index.html', 
        title="VIPSTARCOIN Faucet", 
        form=form, 
        accepted=accepted,
        msg=msg, 
        queue=queue, 
        label=QUEUE_STATE.LABEL,
        balance=balance)

