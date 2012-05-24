import math

EOC = "\0"

def to_numeric(identifier):
	return ((ord(identifier[:1]) - 1) * 255) + (ord(identifier[1:]) - 1)

def to_identifier(numeric):
	return chr(int(math.floor(numeric / 255) + 1)) + chr((numeric % 255) + 1)

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
	def process(self, chunk):
		pass
		
class EchoHandler(Handler):
	def process(self, chunk):
		print "Received %s" % chunk
