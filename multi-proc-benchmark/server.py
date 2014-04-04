from multiprocessing.connection import Listener
from array import array

address = ('localhost', 6000)     # family is deduced to be 'AF_INET'
listener = Listener(address)



while 1:
    conn = listener.accept()
    # print 'connection accepted from', listener.last_accepted
    conn.recv()

listener.close()
