#!/usr/bin/env python 

import os
import logging

# This module is based on the 'serf-master' project (https://github.com/garethr/serf-master)
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
