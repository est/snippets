# http://shell909090.com/blog/2013/07/%E4%B8%80%E7%A7%8D%E6%96%B0%E7%9A%84python%E5%B1%80%E9%83%A8%E8%B0%83%E8%AF%95%E6%89%8B%E6%B3%95/


import socket, pdb

s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
s.connect('1.sock')
f = s.makefile()
pdb.Pdb(stdin=f, stdout=f).set_trace()

raise wtf