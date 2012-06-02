#!/usr/bin/python

################################
# Configuration starts here

cert_path = '/home/sven/ssl/cert'
key_path = '/home/sven/ssl/private'

# Configuration ends here
################################

from shared.core import *

version = 1.0

daemon = SSLDaemon()
daemon.start('0.0.0.0', 9151, cert_path, key_path)

print "Server socket closed, exiting..."
