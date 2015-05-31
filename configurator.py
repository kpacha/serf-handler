#!/usr/bin/env python 

import handler
import os
import json

class ConfigHandler(handler.SerfHandler):
    def __init__(self):
        super(ConfigHandler, self).__init__()
        self.suscribed = (os.environ['SERF_TAG_PRODUCTS']).split(":")

    def config_updated(self, payload):
        newConfig = json.loads(payload)
        productName = newConfig["p"]
        if productName in self.suscribed:
            # check config version (reading the current content of the config involved)
            # and if it's newer, update it, The config is at p/k.json (where p and k are properties of
            # the newConfig dict).
            self.log("ladies & gentlemen, update your configs with: " + str(newConfig) + " total: " + str(len(payload)))
            print "ok"
        else:
            self.log("ignoring config changes")