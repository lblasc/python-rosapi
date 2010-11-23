#!/usr/bin/env python

import socket
from apitest import ApiRos

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("172.16.1.1", 8728))
a = ApiRos(s)
a.login('admin', '')

def response_handler(response):
	if response[-1][0] == "!done":
		r = []
		for ent in response[:-1]:
			if ent[0] == "!re":
				for att in ent[1].keys():
					ent[1][att[1:]] = ent[1][att]
					ent[1].pop(att)
				print ent[1]

def get_interfaces():
	word = ["/interface/print"]
	response = response_handler(a.talk(word))

def get_wireless_registration_table():
	word = ["/interface/wireless/registration-table/print"]

def main():
	get_interfaces()
	#get_wireless_registration_table()

if __name__ == '__main__':
	main()
