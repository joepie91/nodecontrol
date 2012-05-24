#!/usr/bin/python

################################
# Configuration starts here

cert_path = '/home/sven/ssl/cert'
key_path = '/home/sven/ssl/private'

# Configuration ends here
################################

import socket, ssl, select
from shared.core import *

def remove_from_list(ls, val):
	return [value for value in ls if value is not val]

client_list = []
client_map = {}
select_inputs = []
select_outputs = []

class Client:
	buff = ""
	channel_map = {}
	
	def __init__(self, connstream):
		self.stream = connstream
		self.channel_map[0] = Channel(self, EchoHandler())

	def process_data(self, data):
		self.buff += data
		stack = self.buff.split(EOC)
		self.buff = stack.pop()
		
		for chunk in stack:
			self.process_chunk(chunk)
		
	def process_chunk(self, chunk):
		if len(chunk) > 2:
			channel_identifier = chunk[:2]
			data = chunk[2:]
			
			channel_numeric = to_numeric(channel_identifier)
			
			if channel_numeric in self.channel_map:
				self.channel_map[channel_numeric].process_chunk(data)
			else:
				print "WARNING: Received data on non-existent channel %d" % channel_numeric
				


bindsocket = socket.socket()
bindsocket.bind(('0.0.0.0', 9151))
bindsocket.listen(5)

select_inputs = [ bindsocket ]

while select_inputs:
	readable, writable, error = select.select(select_inputs, select_outputs, select_inputs)
	
	for sock in readable:
		try:
			if sock is bindsocket:
				newsocket, fromaddr = bindsocket.accept()
				connstream = ssl.wrap_socket(newsocket,
						server_side=True,
						certfile=cert_path,
						keyfile=key_path,
						ssl_version=ssl.PROTOCOL_TLSv1)
				
				new_client = Client(connstream)
				
				select_inputs.append(connstream)
				client_map[connstream.fileno()] = new_client
				client_list.append(new_client)
			else:
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
			
	
print "Server socket closed, exiting..."
