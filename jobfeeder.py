'''jobfeeder
    A Python bot for getting job updates. Used primarily on ##jobfeed on Freenode.
    Copyright (c) 2013 Jesse Horne (jessehorne.github.io)
'''

from twisted.words.protocols import irc
from twisted.internet.task import LoopingCall
from twisted.internet import reactor, protocol

from twitter import *

from config import *

import re
import requests
import json
import os
import datetime

# https://github.com/sixohsix/twitter/blob/master/twitter/oauth.py#L78
auth = OAuth(access_key, access_secret, consumer_key, consumer_secret)

# https://github.com/sixohsix/twitter/blob/master/twitter/api.py#L241
t = Twitter(auth = auth)

class Bot(irc.IRCClient):
	def __init__(self):
		self.nickname = nickname # irc nick
		self.channels = channels	# irc channels

		# variable to hold old results in checkTwitter
		self.oldresults = ""

	def connectionMade(self):
		irc.IRCClient.connectionMade(self)

	def connectionLost(self, reason):
		irc.IRCClient.connectionLost(self, reason)
		print "DISCONNECTED for " + reason

	def signedOn(self):
		for i in self.channels:
			self.join(i)

	def joined(self, channel):
		print "JOINED " + channel
		lc = LoopingCall(self.checkTwitter)
		lc.start(70)

	def privmsg(self, user, channel, msg):
		user = user.split("!", 1)[0]

		if channel == self.nickname:
			print user + " says: " + msg
			return

		if msg.startswith(self.nickname + ":"):
			print user + " says: " + msg
			return

		if msg.startswith("!monster"):
			end = " ".join(msg.split(" ")[1:])
			url = "http://rss.jobsearch.monster.com/rssquery.ashx?q=" + end
			msg = self.shortener(url)
			print msg
			self.sendMessage(msg)

	def checkTwitter(self):
		self.results = t.statuses.home_timeline(screen_name=user) # variable to hold twitter timeline

		if self.oldresults != "":

			if self.oldresults != "" and self.oldresults[0]["text"] != self.results[0]["text"]:
				msg = self.results[0]["text"]
				self.sendMessage(msg)

		else:
			msg = self.results[0]["text"]
			self.sendMessage(msg)

		self.oldresults = self.results

	def match(self, msg, reg): # used to test if a regex is in a string
		reg = re.compile(reg)
		match = reg.match(msg)

		if match:
			return True
		else:	
			return False

	def shortener(self, url):
		post_url = 'https://www.googleapis.com/urlshortener/v1/url'
		payload = {"longUrl": url}
		headers = {"content-type": "application/json"}
		r = requests.post(post_url, data=json.dumps(payload), headers=headers)
		open("tmp", "w").write(r.text)
		data = json.load(open("tmp"))
		os.remove("tmp")
		return data["id"]

	def sendMessage(self, msg, reg=""):
		# used to send text to the IRC channels in self.channels
		# sendMessage can take a message, and regex argument. If the regex arg is not included
		# the message is sent without being filtered. Else, msg is ran through match.

		msg = msg.encode("ascii", "ignore") # encode ascii

		if reg != "":
			if match(msg, reg) == False:
				for i in self.channels:
					self.sendLine("PRIVMSG %s :%s" % (i, msg))

			log(msg)
		else:
				for i in self.channels:
					self.sendLine("PRIVMSG %s :%s" % (i, msg))


	def log(self, msg):
		open(logfile, "w+").write(datetime.utcnow() + ":" + msg)

class BotFactory(protocol.ClientFactory):
	#def __init__(self):
		# self.channel = "##jobfeed"

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
