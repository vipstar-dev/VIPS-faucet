#!/usr/bin/env python
# coding: utf8

import time
from datetime import datetime
from VIPSFaucet.VIPSrpc import VIPSRPC, VIPSRPCException, VIPS
import logging

logging.basicConfig(format = '%(asctime)s %(name)s: %(levelname)s: %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

rpcuser = "VIPSrpcuser"
rpcpass = "VIPSrpcpass"
rpc = VIPSRPC(rpcuser, rpcpass, testnet=False)

addr = "VXk3LmazNfz3zF8Sa1dtYXWBo423fDkY9q"

#shieldしてope
def shield_VIPS(addr, fee = VIPS.DEFAULT_FEE):
    try:
        r = rpc.shieldcoinbase("*", addr, fee)
        opid = r["opid"]
        amount = r["shieldingValue"]

        logger.info("shielding %f VIPS" % amount)
        logger.info("  opid=%s" % opid)

        while True:
            s = rpc.getoperationstatus([opid])[0]
            logger.debug("unshield_VIPS: status=%s", s["status"])
            if s["status"] == "success":
                break
            elif s["status"] != "executing" and s["status"] != "queued":
                logger.warning("unknown status: %s" % s["status"])
                return -1
            time.sleep(10)
        
        #getoperationresultを呼び出して、VIPSTARCOINd内のstatusを消す
        s = rpc.getoperationresult([opid])[0]

        logger.info("shielding done")
        logger.info("  txid=%s" % s["result"]["txid"])

        return amount - s["params"]["fee"]

    except VIPSRPCException as e:
        logger.error("ERROR: %s", e)
    
    return -1

# unshieldしてoperationが終わるまで待つ。
# amountのFeeはaddrから引かれるのであらかじめ引いておくこと
def unshield_VIPS(addr, amount, fee = VIPS.DEFAULT_FEE):
    try:
        opid = rpc.sendmany([{"address": addr, "amount": amount}], fee = fee)
        logger.info("unshielding %f VIPS" % amount)
        logger.info("  opid=%s" % opid)

        while True:
            s = rpc.getoperationstatus([opid])[0]
            logger.debug("unshield_VIPS: status=%s", s["status"])
            if s["status"] == "success":
                break
            elif s["status"] != "executing" and s["status"] != "queued":
                logger.warning("unknown status: %s" % s["status"])
                return False
            time.sleep(10)

        #getoperationresultを呼び出して、VIPSTARCOINd内のstatusを消す
        s = rpc.getoperationresult([opid])[0]

        logger.info("unshielding done")
        logger.info("  txid=%s" % s["result"]["txid"])

        return True

    except VIPSRPCException as e:
        logger.error("ERROR: %s", e)
    
    return False

#addrの残高がamount以上になるまで待つ。
#  amount以上になったらTrue
#  timeout(デフォルト120秒)立つとFalse
#  mincoinfを指定すると、指定したConfirm以上の残高のみ表示
def waitbalance(addr, amount, minconf = 1, timeout = 600):
    if timeout / 60 < minconf:
        timeout = (minconf + 1) * 60
    
    t = time.time()
    b = rpc.getbalance(addr, minconf)
    logger.debug("balance: %s / %s", b, amount)

    while b < amount:
        # timeout ?
        if t + timeout < time.time():
            return False
        
        time.sleep(10)
        b = rpc.getbalance(addr, minconf)
        logger.debug("balance: %s / %s", b, amount)
    
    return True

while True:
    logger.info("> start shielding")
    amount = shield_VIPS(addr)
    logger.info("> result=%f" % amount)
    if amount > 0:
        logger.info("> waiting confirm")
        r = waitbalance(addr, amount, minconf=3)
        logger.info("waitbalance: %s", r)
        amount = rpc.getbalance(addr, minconf=3)
        for i in range(0, 5):
            logger.info("> start unshielding: amount = %s", amount)
            r = unshield_VIPS(addr, amount - VIPS.DEFAULT_FEE)
            logger.info("unshield_VIPS: %s", r)
            if r:
                break
            time.sleep(60)
    logger.info("> finished")
    time.sleep(1200)
