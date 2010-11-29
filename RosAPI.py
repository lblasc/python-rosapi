#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
#       RosAPI.py
#       
#       Copyright 2010 David Jelić <djelic@buksna.net>
#       Copyright 2010 Luka Blašković <lblasc@znode.net>
#       

"""Python binding for Mikrotik RouterOS API"""
__all__ = ["RosAPICore", "Networking"]

class Core:
	"""Core part of Router OS API
	
	It contains methods necessary to extract raw data from the router.
	If object is instanced with DEBUG = True parameter, it runs in verbosity mode.
	
	Core part is taken mostly from http://wiki.mikrotik.com/wiki/Manual:API#Example_client."""

	def __init__(self, hostname, port=8728, DEBUG=False):
		import socket
		self.DEBUG = DEBUG
		self.hostname = hostname
		self.port = port
		self.currenttag = 0
		self.sk = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.sk.connect((self.hostname, self.port))

	def login(self, username, pwd):
		import binascii
		from hashlib import md5

		for repl, attrs in self.talk(["/login"]):
			chal = binascii.unhexlify(attrs['=ret'])
		md = md5()
		md.update('\x00')
		md.update(pwd)
		md.update(chal)
		self.talk(["/login", "=name=" + username, "=response=00" + binascii.hexlify(md.digest())])

	def talk(self, words):
		if self.writeSentence(words) == 0: return
		r = []
		while 1:
			i = self.readSentence();
			if len(i) == 0: continue
			reply = i[0]
			attrs = {}
			for w in i[1:]:
				j = w.find('=', 1)
				if (j == -1):
					attrs[w] = ''
				else:
					attrs[w[:j]] = w[j+1:]
			r.append((reply, attrs))
			if reply == '!done': return r

	def writeSentence(self, words):
		ret = 0
		for w in words:
			self.writeWord(w)
			ret += 1
		self.writeWord('')
		return ret

	def readSentence(self):
		r = []
		while 1:
			w = self.readWord()
			if w == '': return r
			r.append(w)
			
	def writeWord(self, w):
		if self.DEBUG:
			print "<<< " + w
		self.writeLen(len(w))
		self.writeStr(w)

	def readWord(self):
		ret = self.readStr(self.readLen())
		if self.DEBUG:
			print ">>> " + ret
		return ret

	def writeLen(self, l):
		if l < 0x80:
			self.writeStr(chr(l))
		elif l < 0x4000:
			l |= 0x8000
			self.writeStr(chr((l >> 8) & 0xFF))
			self.writeStr(chr(l & 0xFF))
		elif l < 0x200000:
			l |= 0xC00000
			self.writeStr(chr((l >> 16) & 0xFF))
			self.writeStr(chr((l >> 8) & 0xFF))
			self.writeStr(chr(l & 0xFF))
		elif l < 0x10000000:
			l |= 0xE0000000
			self.writeStr(chr((l >> 24) & 0xFF))
			self.writeStr(chr((l >> 16) & 0xFF))
			self.writeStr(chr((l >> 8) & 0xFF))
			self.writeStr(chr(l & 0xFF))
		else:
			self.writeStr(chr(0xF0))
			self.writeStr(chr((l >> 24) & 0xFF))
			self.writeStr(chr((l >> 16) & 0xFF))
			self.writeStr(chr((l >> 8) & 0xFF))
			self.writeStr(chr(l & 0xFF))

	def readLen(self):
		c = ord(self.readStr(1))
		if (c & 0x80) == 0x00:
			pass
		elif (c & 0xC0) == 0x80:
			c &= ~0xC0
			c <<= 8
			c += ord(self.readStr(1))
		elif (c & 0xE0) == 0xC0:
			c &= ~0xE0
			c <<= 8
			c += ord(self.readStr(1))
			c <<= 8
			c += ord(self.readStr(1))
		elif (c & 0xF0) == 0xE0:
			c &= ~0xF0
			c <<= 8
			c += ord(self.readStr(1))
			c <<= 8
			c += ord(self.readStr(1))
			c <<= 8
			c += ord(self.readStr(1))
		elif (c & 0xF8) == 0xF0:
			c = ord(self.readStr(1))
			c <<= 8
			c += ord(self.readStr(1))
			c <<= 8
			c += ord(self.readStr(1))
			c <<= 8
			c += ord(self.readStr(1))
		return c

	def writeStr(self, str):
		n = 0;
		while n < len(str):
			r = self.sk.send(str[n:])
			if r == 0: raise RuntimeError, "connection closed by remote end"
			n += r

	def readStr(self, length):
		ret = ''
		while len(ret) < length:
			s = self.sk.recv(length - len(ret))
			if s == '': raise RuntimeError, "connection closed by remote end"
			ret += s
		return ret

	def response_handler(self, response):
		"""Handles API response and remove unnessesary data"""

		# if respons end up successfully
		if response[-1][0] == "!done":
			r = []
			# for each returned element
			for elem in response[:-1]:
				# if response is valid Mikrotik returns !re, if error !trap
				# before each valid element, there is !re
				if elem[0] == "!re":
					# take whole dictionary of single element
					element = elem[1]
					# with this loop we strip equals in front of each keyword
					for att in element.keys():
						element[att[1:]] = element[att]
						element.pop(att)
					# collect modified data in new array
					r.append(element)
		return r

	def run_interpreter(self):
		import select, sys
		inputsentence = []

		while 1:
			r = select.select([self.sk, sys.stdin], [], [], None)
			if self.sk in r[0]:
				# something to read in socket, read sentence
				x = self.readSentence()

			if sys.stdin in r[0]:
				# read line from input and strip off newline
				l = sys.stdin.readline()
				l = l[:-1]

				# if empty line, send sentence and start with new
				# otherwise append to input sentence
				if l == '':
					self.writeSentence(inputsentence)
					inputsentence = []
				else:
					inputsentence.append(l)
		return 0

class Networking(Core):
	"""Handles network part of Mikrotik Router OS
	
	Contains functions for pulling informations about interfaces,
	routes, wireless registrations, etc."""
	
	def get_all_interfaces(self):
		"""Pulls out all available data related to network interfaces"""

		word = ["/interface/print"]
		response = Core.talk(self, word)
		response = Core.response_handler(self, response)
		return response

def test():
	tik = Core("172.16.1.1", DEBUG=True)
	tik.login("admin", "")
	tik.run_interpreter()

if __name__ == "__main__":
	test()

