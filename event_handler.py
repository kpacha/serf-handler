#!/usr/bin/env python 

import logging
import handler
import consumer
import configurator
import sys


class WebHandler(consumer.ConsumerHandler):
    def deploy(self, payload):
        print "DEPLOY ME! " + payload


class DatabaseHandler(handler.SerfHandler):
    def backup(self, payload):
        print "BACKUP TIME! " + payload

if __name__ == '__main__':
    logging.basicConfig(filename='/tmp/serf_event_handler.log',
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        datefmt='%Y/%m/%d %H:%M:%S', level=logging.INFO)
    handler = handler.SerfHandlerProxy()
    handler.register('web', WebHandler(['product2', 'product3'], "conf/"))
    handler.register('mysql', DatabaseHandler())
    handler.register('default', configurator.ConfigHandler())
    handler.run(sys.stdin)