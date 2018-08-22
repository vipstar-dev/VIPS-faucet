# coding: utf8

import logging

from VIPSFaucet.app import app
from VIPSFaucet.sender import SenderThread
import VIPSFaucet.view

if __name__ == '__main__':
    #app.logger.setLevel(logging.DEBUG)
    #sender = SenderThread()
    #sender.start()
    app.run()
