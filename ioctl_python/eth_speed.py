# http://stackoverflow.com/a/4789267/41948

SIOCETHTOOL = 0x8946


import fcntl, socket, struct



import os,time
import array,fcntl,struct,socket
def check_net():
    data =  'eth4'
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    SIOCETHTOOL = 0x8946
    print repr(data)
    print repr(fcntl.ioctl(sock.fileno(), SIOCETHTOOL, data))
    sock.close()
print check_net()
