# coding: utf-8

import time
import sys
import threading
import logging

from .app import app, rpc, balance
from .database import db
from .model import Queue, QUEUE_STATE
from .VIPSrpc import VIPSRPCException

logger = app.logger
#logging.basicConfig(format = '%(asctime)s %(name)s: %(levelname)s: %(message)s')
#logger = logging.getLogger(__name__)
#logger.setLevel(logging.DEBUG)

MIN_CONFIRM = 3
INITIAL_LIMIT = 32

class SenderThread(threading.Thread):
    def __init__(self):
        super(SenderThread, self).__init__()
        self.stop_event = threading.Event()
        self.limit = INITIAL_LIMIT

    def stop(self):
        self.stop_event.set()

    def run(self):
        logger.info("sender started.")
        with app.app_context():
            while True:
                try:
                    #==============================================================================
                    # 未送信Queueの送信処理
                    #   送信が成功したらtxidをセットしてstate=CONFIRMにする。
                    #==============================================================================
                    queue = Queue.query.filter(Queue.state == QUEUE_STATE.INIT).limit(self.limit).all()

                    # sendmany用のToAddrSetを作る。
                    if len(queue) > 0:
                        data = {}
                        for q in queue:
                            logger.debug("send data: %s %s %s", q.date, q.amount, q.address)
                            if data.has_key(q.address):
                                data[q.address] += q.amount
                            else:
                                data[q.address] = q.amount
                        
                        try:
                            #送信！
                            txid = rpc.sendmany("", data, minconf = MIN_CONFIRM)
                            logger.info("txid=%s", txid)

                            #Transaction ID更新
                            for q in queue:
                                q.transaction = txid
                                q.state = QUEUE_STATE.CONFIRM
                            db.session.commit()

                            # エラーがないなら処理制限数をもとに戻す
                            self.limit = INITIAL_LIMIT

                        except VIPSRPCException as e:
                            logger.error("VIPS error: %s", e)
                            # エラー時、処理したQueue数が1個ならそのQueueをエラー状態とする。
                            if len(queue) == 1:
                                queue[0].state = QUEUE_STATE.ERROR
                                db.session.commit()
                            # エラーが出たら次は1個ずつ処理する
                            self.limit = 1

                    #==============================================================================
                    # 送信済みQueueの処理
                    #   confirmationsがMIN_CONFIRM以上になったらなら、state=DONEにする。
                    #==============================================================================
                    queue = Queue.query.filter(Queue.state == QUEUE_STATE.CONFIRM).all()

                    modified = False
                    for q in queue:
                        if q.transaction == "":
                            continue
                        tx = rpc.gettransaction(q.transaction)
                        if tx["confirmations"] >= MIN_CONFIRM:
                            logger.info("tx %s done" % q.transaction)
                            q.state = QUEUE_STATE.DONE
                            modified = True
                    if modified:
                        db.session.commit()

                    #==============================================================================
                    # 残高を得る
                    #==============================================================================
                    balance = rpc.getbalance()

                except KeyboardInterrupt:
                    logger.error("keyboard interrupt! sender terminated.")
                    break
                except:
                    logger.error("exception: %s", sys.exc_info()[1])
                
                time.sleep(5)

sender = SenderThread()
sender.setDaemon(True)
sender.start()
