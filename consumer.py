#!/usr/bin/env python 

import handler
import members

class ConsumerHandler(handler.SerfHandler):
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