#!/usr/bin/env python
# coding: utf8


import socket

s=socket.socket(socket.AF_INET, socket.SOCK_STREAM)
# s.setsockopt(socket.SOL_SOCKET, socket.SO_SNDBUF, 10)
# s.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 10)
s.setsockopt(socket.SOL_TCP, socket.TCP_NODELAY, 1)
s.connect(('google.com', 80))
snd = 'GET / HTTP/1.1\r\nHost: www.google.com\r\n\r\n'
for i in range(0, len(snd), 2):
    print s.send(snd[i:i+2])
print s.recv(1024)
