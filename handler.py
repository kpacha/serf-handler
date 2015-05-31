#!/usr/bin/env python 

import os
import logging
import members
import json


# This class is based on the 'serf-master' project (https://github.com/garethr/serf-master)
class SerfHandler(object):
    def __init__(self):
        self.name = os.environ['SERF_SELF_NAME']
        self.roles = (os.environ.get('SERF_TAG_ROLE') or os.environ.get('SERF_SELF_ROLE')).split(":")
        self.roles.append('default')
        self.logger = logging.getLogger(type(self).__name__)
        if os.environ['SERF_EVENT'] == 'user':
            self.event = os.environ['SERF_USER_EVENT']
        elif os.environ['SERF_EVENT'] == 'query':
            self.event = os.environ['SERF_QUERY_NAME']
        else:
            self.event = os.environ['SERF_EVENT'].replace('-', '_')

    def log(self, message):
        self.logger.info(message)


class ConsumerHandler(SerfHandler):
    def __init__(self, observed, configDir):
        super(ConsumerHandler, self).__init__()
        self.observed = observed
        self.configDir = configDir

    def handleMembershipChange(self):
        members_handler = members.Members(self.configDir)
        members_handler.run()

    def member_join(self, payload):
        # self.log("NEW MEMBER HAS JOINED THE PARTY! " + payload)
        self.handleMembershipChange()

    def member_update(self, payload):
        # self.log("A MEMBER HAS UPDATED ITS STATE! " + payload)
        self.handleMembershipChange()

    def member_leave(self, payload):
        # self.log("A MEMBER HAS LEAVE THE PARTY! " + payload)
        self.handleMembershipChange()

    def member_failed(self, payload):
        # self.log("A MEMBER HAS FAILED! " + payload)
        self.handleMembershipChange()


class ConfigHandler(SerfHandler):
    def __init__(self, configDir):
        super(ConfigHandler, self).__init__()
        self.suscribed = (os.environ['SERF_TAG_PRODUCTS']).split(":")
        self.configDir = configDir

    def config_updated(self, payload):
        newConfig = json.loads(payload)
        productName = newConfig["p"]
        if productName in self.suscribed:
            configFile = "%s%s/%s.json" % (self.configDir, productName, newConfig["k"])
            receivedVersion = int(newConfig["v"])
            fp = open(configFile, "r")
            isNew = False
            try:
                stored = json.load(fp)
                isNew = stored["_version"] < receivedVersion
            except:
                isNew = True
            fp.close()
            if isNew:
                config = newConfig["c"]
                config["_version"] = receivedVersion
                tmpFile = "/tmp/%s_%s.json" % (productName, newConfig["k"])
                fp = open(tmpFile, "w")
                print>>fp, json.dumps(config, sort_keys=True, indent=4, separators=(',', ': '))
                fp.close()
                os.system("mv %s %s" % (tmpFile, configFile))
                self.log("configs update with: " + str(config))
            else:
                self.log("ignoring config changes: old version")
            print "ok"
        else:
            self.log("ignoring config changes: not interested in")


# This class is based on the 'serf-master' project (https://github.com/garethr/serf-master)
class SerfHandlerProxy(SerfHandler):

    def __init__(self):
        super(SerfHandlerProxy, self).__init__()
        self.handlers = {}

    def register(self, role, handler):
        self.handlers[role] = handler

    def get_klass(self):
        klass = []
        for role in self.roles:
            if role in self.handlers:
                klass.append(self.handlers[role])
        return klass

    def run(self, inputStream):
        klass = self.get_klass()
        if len(klass) == 0:
            self.log("no handler for the registered roles " + str(self.roles) + ". ignoring event [" + self.event + "]")
        else:
            payload = inputStream.read()
            for k in klass:
                try:
                    getattr(k, self.event)(payload)
                except AttributeError:
                    self.log("event [" + self.event + "] not supported by class " + type(k).__name__)