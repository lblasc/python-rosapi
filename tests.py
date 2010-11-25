#!/usr/bin/env python

from RosAPI import Core

def prettify(data):
	for x in data:
		for y in x.keys():
			print "%-20s: %50s" % (y, x[y])

if __name__ == "__main__":
	a = Core("172.16.1.1")
	a.login("admin", "")
	#a.run_interpreter()
	prettify(a.response_handler(a.talk(["/ip/address/print"])))
