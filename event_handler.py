#!/usr/bin/env python 

from handler import SerfHandler, SerfHandlerProxy, ConfigHandler, BalancedConsumerHandler
import logging
import sys


class WebHandler(BalancedConsumerHandler):
    def deploy(self, payload):
        print "DEPLOY ME! " + payload


class DatabaseHandler(SerfHandler):
    def backup(self, payload):
        print "BACKUP TIME! " + payload

if __name__ == '__main__':
    logging.basicConfig(filename='/tmp/serf_event_handler.log',
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
    handler = SerfHandlerProxy()
    handler.register('web', WebHandler(['product4', 'product3'], "conf/"))
    handler.register('mysql', DatabaseHandler())
    handler.register('default', ConfigHandler("conf/"))
    handler.run(sys.stdin)