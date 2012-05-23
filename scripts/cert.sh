#!/bin/sh
openssl genrsa 2048 > private
openssl req -new -x509 -nodes -sha1 -days 3650 -key private > cert
