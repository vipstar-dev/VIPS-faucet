# coding: utf8

from datetime import datetime
from .database import db

class QUEUE_STATE:
	INIT = 0
	CONFIRM = 1
	DONE = 2
	ERROR = 3
	LABEL = [u"Queued", "Wait Confirmation", "Done", "ERROR"]

class Queue(db.Model):
	id = db.Column(db.Integer, primary_key=True)
	date = db.Column(db.DateTime, default=datetime.now())
	address = db.Column(db.String(40))
	amount = db.Column(db.Float(asdecimal=True))
	transaction = db.Column(db.String(), default="")
	state = db.Column(db.Integer, default=QUEUE_STATE.INIT)
	remote = db.Column(db.String(16))
	sessionid = db.Column(db.String(40))

	def __init__(self, address, amount, remote, sessionid):
		self.address = address
		self.amount = amount
		self.date = datetime.now()
		self.remote = remote
		self.sessionid = sessionid

	def  __repr__(self):
		return "<Queue %s:%d (%s)>" % (self.address, self.amount, self.remote)
