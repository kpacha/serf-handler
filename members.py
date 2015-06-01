#!/usr/bin/env python

import os
import logging
import json

class Base(object):
	def __init__(self, configDir):
		self.products = {}
		self.logger = logging.getLogger(type(self).__name__)
		self.configDir = configDir

	def log(self, msg):
		self.logger.info(msg)

	def trace(self, product):
		self.logger.debug(product)


class EtcHostsRenderer(Base):
	def __init__(self, configDir):
		super(EtcHostsRenderer, self).__init__(configDir)
		self.fp = open("/tmp/fakehosts_updating.txt", "w")

	def printProduct(self, product):
		pass

	def printService(self, product, service, nodes):
		size = len(nodes)
		for x in range(4):
			print>>self.fp, nodes[x % size]["addr"] + "\tsvc-" + product + "-" + service + "-" + str(x)

	def close(self):
		self.fp.close()
		os.system("mv /tmp/fakehosts_updating.txt %sfakehosts.txt" % self.configDir)


class YamlServiceRenderer(Base):
	def __init__(self, configDir):
		super(YamlServiceRenderer, self).__init__(configDir)
		self.fp = open("/tmp/services_updating.yml", "w")

	def printProduct(self, product):
		print>>self.fp, product + " :"

	def printService(self, product, service, nodes):
		print>>self.fp, "    " + service + " :"
		for n in nodes:
			print>>self.fp, "        - name : " + n["name"]
			print>>self.fp, "          port : " + str(n["port"])
			print>>self.fp, "          addr : " + n["addr"]

	def close(self):
		self.fp.close()
		os.system("mv /tmp/services_updating.yml %sservices.yml" % self.configDir)


class HAProxyConfigRenderer(Base):
	def __init__(self, configDir):
		super(HAProxyConfigRenderer, self).__init__(configDir)
		self.fp = {}

	def printProduct(self, product):
		self.fp[product] = open("/tmp/haproxy_%s_updating.cnf" % product, "w")

	def printService(self, product, service, nodes):
		print>>self.fp[product], service + " :"
		for n in nodes:
			print>>self.fp[product], "    - name : " + n["name"]
			print>>self.fp[product], "      port : " + str(n["port"])
			print>>self.fp[product], "      addr : " + n["addr"]

	def close(self):
		for p in self.fp:
			self.fp[p].close()
			os.system("mv /tmp/haproxy_%s_updating.cnf %shaproxy_%s.cnf" % (p, self.configDir, p))


class SimpleRenderer(Base):
	def getRenderers(self):
		return [EtcHostsRenderer(self.configDir), YamlServiceRenderer(self.configDir)]

	def doRender(self, products, renderers):
		self.log("Writing new config files...")
		self.trace(str(products))
		cfp = open("/tmp/services_updating.json", "w")
		print>>cfp, json.dumps(products, sort_keys=True, indent=4, separators=(',', ': '))
		for p in products:
			for r in renderers:
				r.printProduct(p)
			services = products[p]
			for s in services:
				for r in renderers:
					r.printService(p, s, services[s])
		self.log("Replacing the old set of config files with the fresh one...")
		for r in renderers:
			r.close()
		cfp.close()
		os.system("mv /tmp/services_updating.json %sservices.json" % self.configDir)

	def render(self, products):
		self.doRender(products, self.getRenderers())


class HAProxyRenderer(SimpleRenderer):
	def render(self, products):
		renderers = self.getRenderers()
		renderers.append(HAProxyConfigRenderer(self.configDir))
		self.doRender(products, renderers)


class Members(Base):
	def __init__(self, renderer, configDir):
		super(Members, self).__init__(configDir)
		self.renderer = renderer

	def getMemberTable(self,  products):
		self.log("Parsing the members table")
		handle = os.popen("serf members -format=json -status=alive -tag products='.*(%s).*'" % "|".join(products))
		# handle = open("fixtures/serf_members_fake.json", "r")
		members = json.load(handle)
		return members["members"]

	def parseMemberTable(self, members, observed, collaborators):
		products = {}
		for member in members:
			host = member["addr"].split(":")
			name = member["name"]
			productsInNode = member["tags"]["products"].split(":")
			for p in productsInNode:
				if p not in observed:
					continue
				product = products.get(p, {})
				services = member["tags"][p + ".service_type"].split(":")
				for s in services:
					if p in collaborators and s != "public":
						continue
					nodes = product.get(s, [])
					nodes.append({ 'addr': host[0], 'port': int(member["tags"][p + "." + s + ".service_port"]), 'name': name })
					product[s] = nodes
				products[p] = product
		return products

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
			self.renderer.render(products)
		else:
			self.log("Nothing to update")
		return products

	def run(self, suscribed, observed):
		self.log("Checking the membership table")
		union = list(set(suscribed + observed))
		diff = list(set(observed) - set(suscribed))
		products = self.parseMemberTable(self.getMemberTable(union), union, diff)
		self.update(products)
		self.log("Done")
		return products

if __name__ == '__main__':
	configDir = "conf/"
	members_handler = Members(SimpleRenderer(configDir), configDir)
	members_handler.run()