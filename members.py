#!/usr/bin/env python

import os
import logging
import json

class Members(object):
	def __init__(self, configDir):
		self.products = {}
		self.logger = logging.getLogger(type(self).__name__)
		self.configDir = configDir

	def log(self, msg):
		self.logger.info(msg)

	def trace(self, product):
		self.logger.debug(product)

	def getMemberTable(self):
		self.log("Parsing the members table")
		handle = os.popen("serf members -format=json")
		# handle = open("fixtures/serf_members_fake.json", "r")
		members = json.load(handle)
		return members["members"]
		
	def parseMemberTable(self, members):
		products = {}
		for member in members:
			if (member["status"] == "alive"):
				host = member["addr"].split(":")
				name = member["name"]
				productsInNode = member["tags"]["products"].split(":")
				for p in productsInNode:
					product = products.get(p, {})
					services = member["tags"][p + ".service_type"].split(":")
					for s in services:
						nodes = product.get(s, [])
						nodes.append({ 'addr' : host[0], 'port' : int(member["tags"][p + "." + s + ".service_port"]), 'name' : name })
						product[s] = nodes
					products[p] = product
		return products

	def render(self, products):
		self.log("Writing new config files...")
		self.trace(str(products))
		cfp = open("/tmp/services_updating.json", "w")
		hfp = open("/tmp/fakehosts_updating.txt", "w")
		sfp = open("/tmp/services_updating.yml", "w")
		print>>cfp, json.dumps(products, sort_keys=True, indent=4, separators=(',', ': '))
		for p in products:
			print>>sfp, p + " :"
			services = products[p]
			for s in services:
				node = services[s]
				size = len(node)
				for x in range(4): print>>hfp, node[x % size]["addr"] + "\tsvc-" + p + "-" + s + "-" + str(x)
				print>>sfp, "    " + s + " :"
				for n in node:
					print>>sfp, "        - name : " + n["name"]
					print>>sfp, "          port : " + str(n["port"])
					print>>sfp, "          addr : " + n["addr"]
		self.log("Replacing the old set of config files with the fresh one...")
		sfp.close()
		hfp.close()
		cfp.close()
		os.system("mv /tmp/fakehosts_updating.txt %sfakehosts.txt" % self.configDir)
		os.system("mv /tmp/services_updating.yml %sservices.yml" % self.configDir)
		os.system("mv /tmp/services_updating.json %sservices.json" % self.configDir)

	def update(self, products):
		mustUpdate = False
		try:
			handle = open("conf/services.json", "r")
			previousVersion = json.load(handle)
			mustUpdate = previousVersion != products
			handle.close()
		except:
			mustUpdate = True

		if (mustUpdate):
			self.render(products)
		else:
			self.log("Nothing to update")

	def run(self):
		self.log("Checking the membership table")
		self.update(self.parseMemberTable(self.getMemberTable()))
		self.log("Done")

if __name__ == '__main__':
	members_handler = Members("conf/")
	members_handler.run()