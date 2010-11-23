#!/usr/bin/env python

import socket, tests
from apitest import ApiRos

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("192.168.56.100", 8728))
a = ApiRos(s)
a.login('admin', '')

def response_handler(response):
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

def get_interfaces():
	word = ["/interface/print"]
	response = response_handler(a.talk(word))
	return response

def get_wireless_registration_table():
	word = ["/interface/wireless/registration-table/print"]
	response = response_handler(a.talk(word))
	return response

def main():
	tests.prittify(get_interfaces())
	tests.prittify(get_wireless_registration_table())

if __name__ == '__main__':
	main()
