#!/usr/bin/python

################################
# Configuration starts here

allowed_certs = '/home/sven/ssl/allowed'

# Configuration ends here
################################

import socket, ssl, time, math
from shared.core import *

select_inputs = []
select_outputs = []
client_map = {}

client = SSLClient("localhost", 9151, allowed_certs)
select_inputs.append(client.ssl_sock)
select_outputs.append(client.ssl_sock)
client_map[client.ssl_sock.fileno()] = client.client

while True:
	readable, writable, error = select.select(select_inputs, select_outputs, select_inputs)
	
	for sock in readable:
		try:
			data = sock.recv(1024)
			
			if data:
				cur_client = client_map[sock.fileno()]
				cur_client.process_data(data)
			else:
				select_inputs = remove_from_list(select_inputs, sock)
				print "NOTICE: Client disconnected"
		except ssl.SSLError, err:
			if err.args[0] == ssl.SSL_ERROR_WANT_READ:
				select.select([sock], [], [])
			elif err.args[0] == ssl.SSL_ERROR_WANT_WRITE:
				select.select([], [sock], [])
			else:
				raise

