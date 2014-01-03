'''jobfeeder
    A Python bot for getting job updates. Used primarily on ##jobfeed on Freenode.
    Copyright (c) 2013 Jesse Horne (jessehorne.github.io)
'''

from twisted.words.protocols import irc
from twisted.internet.task import LoopingCall
from twisted.internet import reactor, protocol

from twitter import *

import time
import sys

consumer_key = "sHxquEvxDuX8RtPu6o9j1Q"
consumer_secret = "EZKVGKSYhcnGCJzfrP5akbpWIkXeGEhAyQRf90Bu4o"
access_key = "2273653969-yBOitB32mpo7DokMk8I8OKiQmpp8llUOCPXsfC5"
access_secret = "higVJr0yIkZr6CNd7sNdYhhVKeV6nd7AulPrOEvV8gf3v"

auth = OAuth(access_key, access_secret, consumer_key, consumer_secret)
t = Twitter(auth = auth)

user = "jobfeedirc"

class Bot(irc.IRCClient):
	def __init__(self):
		self.nickname = "JobFeeder"
		self.channel = "##jobfeed"
		self.oldresults = ""

	def connectionMade(self):
		irc.IRCClient.connectionMade(self)

	def connectionLost(self, reason):
		irc.IRCClient.connectionLost(self, reason)
		print "DISCONNECTED for " + reason

	def signedOn(self):
		self.join(self.channel)

	def joined(self, channel):
		print "JOINED " + channel
		lc = LoopingCall(self.checkTwitter)
		lc.start(60)

	def privmsg(self, user, channel, msg):
		user = user.split("!", 1)[0]

		if channel == self.nickname:
			print user + " says: " + msg
			return

		if msg.startswith(self.nickname + ":"):
			print user + " says: " + msg
			return

	def checkTwitter(self):
		self.results = t.statuses.home_timeline(screen_name=user)

		if self.oldresults != "" and self.oldresults[0]["text"] != self.results[0]["text"]:
			msg = self.results[0]["text"].encode("ascii", "ignore")
			msg = msg.replace("\r", "")
			msg = msg.replace("\n", "")
			self.sendMessage(msg)
			print msg
		self.oldresults = self.results
		
	def sendMessage(self, msg):
		self.sendLine("PRIVMSG %s :%s" % (self.channel, msg))

class BotFactory(protocol.ClientFactory):
	def __init__(self):
		self.channel = "##jobfeed"

	def buildProtocol(self, addr):
		p = Bot()
		p.factory = self
		return p

	def clientConnectionLost(self, connector, reason):
		connector.connect()

	def clientConnectionFailed(self, connector, reason):
		print "connection failed:", reason
		reactor.stop()

if __name__ == "__main__":
	f = BotFactory()
	reactor.connectTCP("chat.freenode.net", 6667, f)
	reactor.run()
