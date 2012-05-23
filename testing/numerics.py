import math

def to_numeric(identifier):
	return ((ord(identifier[:1]) - 1) * 255) + (ord(identifier[1:]) - 1)

def to_identifier(numeric):
	return chr(int(math.floor(numeric / 255) + 1)) + chr((numeric % 255) + 1)

print to_identifier(to_numeric("aa"))
print to_identifier(to_numeric("ab"))
print to_identifier(to_numeric("ac"))
print to_identifier(to_numeric("ad"))
