#!/usr/bin/env python

def prittify(data):
	for x in data:
		for y in x.keys():
			print repr("%s" % y).ljust(10), repr("%s" % x[y]).rjust(50)
