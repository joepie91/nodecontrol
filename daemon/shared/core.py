import math, socket, ssl, select, time, threading, random, string
from datetime import datetime

EOC = "\0"

def to_numeric(identifier):
	return ((ord(identifier[:1]) - 1) * 255) + (ord(identifier[1:]) - 1)

def to_identifier(numeric):
	return chr(int(math.floor(numeric / 255) + 1)) + chr((numeric % 255) + 1)
	
def remove_from_list(ls, val):
	return [value for value in ls if value is not val]

class PingThread(threading.Thread):
	def __init__(self, channel):
		self.channel = channel
		threading.Thread.__init__(self)
		self.daemon = True
		
	def run(self):
		while True:
			self.pingkey = ''.join(random.choice(string.letters + string.digits) for i in xrange(5))
			self.pingtime = datetime.time(datetime.now())
			self.channel.send("PING %s" % self.pingkey)
			time.sleep(10)

class Client:
	buff = ""
	channel_map = {}
	handshake_status = 0
	
	version = 1.0
	
	def __init__(self, connstream):
		self.stream = connstream
		self.channel_map[0] = Channel(self, ControlHandler(self))
		
	def start_handshake(self):
		self.handshake_status = 1
		self.channel_map[0].send("OHAI")

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

class Channel:
	numeric = 0
	binary = False
	handler = None
	client = None
	
	def __init__(self, client, handler, binary=False):
		self.handler = handler
		self.binary = binary
		self.client = client
		
	def process_chunk(self, chunk):
		self.handler.process(chunk)
		
	def send(self, data):
		self.client.stream.send(to_identifier(self.numeric) + data + EOC)
		
class Handler:
	client = None
	channel = None
	
	def __init__(self, client):
		self.client = client
	
	def process(self, chunk):
		pass
		
class ControlHandler(Handler):
	pingthread = None
	
	def process(self, chunk):
		target = self.client.channel_map[0]
		
		if chunk == "OHAI":
			self.client.handshake_status = 1
			target.send("HITHAR")
		elif chunk == "HITHAR":
			self.client.handshake_status = 2
			target.send("VERSION %d" % self.client.version)
		elif chunk[:7] == "VERSION":
			if self.client.handshake_status == 1:
				# Version received, return own version
				self.client.handshake_status = 3
				target.send("VERSION %d" % self.client.version)
			elif self.client.handshake_status == 2:
				# Version received and already sent, version exchange complete
				self.client.handshake_status = 4
				target.send("KGO")
				print "Handshake complete!"
				self.pingthread = PingThread(target)
				self.pingthread.start()
			else:
				raise Exception("VERSION received outside version exchange.")
		elif chunk == "KGO":
			if self.client.handshake_status == 3:
				# Handshake complete
				self.client.handshake_status = 4
				print "Handshake complete!"
				self.pingthread = PingThread(target)
				self.pingthread.start()
			else:
				raise Exception("KGO received before handshake finalization.")
		elif chunk[:4] == "PING":
			command, pingkey = chunk.split(' ')
			target.send("PONG %s" % pingkey)
		elif chunk[:4] == "PONG":
			command, pingkey = chunk.split(' ')
			microseconds = (self.pingthread.pingtime.microsecond * 1.0) / 1000000
			seconds_start = self.pingthread.pingtime.second + microseconds
			current_time = datetime.time(datetime.now())
			microseconds = (current_time.microsecond * 1.0) / 1000000
			seconds_end = current_time.second + microseconds
			
			print "Latency: %f seconds" % (seconds_end - seconds_start)
		
class EchoHandler(Handler):
	def process(self, chunk):
		print "Received %s" % chunk

class SSLClient:
	hostname = ""
	port = 0
	client = None
	controlchannel = None
	controlhandler = None
	ssl_sock = None
	
	def __init__(self, hostname, port, allowed_certs):
		sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
		self.ssl_sock = ssl.wrap_socket(sock, cert_reqs=ssl.CERT_REQUIRED, ca_certs=allowed_certs)
		self.ssl_sock.connect((hostname, port))
		
		self.client = Client(self.ssl_sock)
		
		self.client.start_handshake()
		

class SSLDaemon:
	client_list = []
	client_map = {}
	select_inputs = []
	select_outputs = []
	
	def __init__(self):
		pass
		
	def start(self, interface, port, cert_path, key_path):
		bindsocket = socket.socket()
		bindsocket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
		bindsocket.bind((interface, port))
		bindsocket.listen(5)

		self.select_inputs = [ bindsocket ]

		while self.select_inputs:
			readable, writable, error = select.select(self.select_inputs, self.select_outputs, self.select_inputs)
			
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
						
						self.select_inputs.append(connstream)
						self.select_outputs.append(connstream)
						self.client_map[connstream.fileno()] = new_client
						self.client_list.append(new_client)
					else:
						data = sock.recv(1024)
						
						if data:
							cur_client = self.client_map[sock.fileno()]
							cur_client.process_data(data)
						else:
							self.select_inputs = remove_from_list(self.select_inputs, sock)
							print "NOTICE: Client disconnected"
				except ssl.SSLError, err:
					if err.args[0] == ssl.SSL_ERROR_WANT_READ:
						select.select([sock], [], [])
					elif err.args[0] == ssl.SSL_ERROR_WANT_WRITE:
						select.select([], [sock], [])
					else:
						raise
