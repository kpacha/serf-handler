#!/usr/bin/env python 

import logging
import json
import os

class EtcdClient(object):
	def __init__(self):
		self.logger = logging.getLogger(type(self).__name__)
		self.action = os.environ['ETCD_WATCH_ACTION']
		self.actionsToWatch = ["set"]

	def handle(self):
		if self.action in self.actionsToWatch:
			keys = os.environ['ETCD_WATCH_KEY'].split("/")
			value = json.loads(os.environ['ETCD_WATCH_VALUE'])
			message = json.dumps({'p': keys[1], 'k': keys[2], 'v': int(os.environ['ETCD_WATCH_MODIFIED_INDEX']), 'c': value})
			os.system("serf event config_updated '%s'" % message)
			self.logger.debug("the event [config_updated] '%s' has been sent" % message)
			print "propagated"
		else:
			print "ignoring"


if __name__ == '__main__':
	logging.basicConfig(filename='/tmp/serf_etcd_client.log',
		format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
		datefmt='%Y/%m/%d %H:%M:%S', level=logging.DEBUG)
	client = EtcdClient()
	client.handle()
