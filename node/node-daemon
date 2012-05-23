#!/usr/bin/python

################################
# Configuration starts here

allowed_certs = '/home/sven/ssl/allowed'

# Configuration ends here
################################

EOC = "\0"

import socket, ssl, time, math

def to_numeric(identifier):
	return ((ord(identifier[:1]) - 1) * 255) + (ord(identifier[1:]) - 1)

def to_identifier(numeric):
	return chr(int(math.floor(numeric / 255) + 1)) + chr((numeric % 255) + 1)

s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
ssl_sock = ssl.wrap_socket(s, cert_reqs=ssl.CERT_REQUIRED, ca_certs=allowed_certs)
ssl_sock.connect(('localhost', 9151))

ssl_sock.write(to_identifier(0) + 'test data' + EOC + to_identifier(4190) + 'SAMPLEDATA' + EOC)

print ssl_sock.read()[2:]

ssl_sock.close()
