import time

from multiprocessing.connection import Client

now = time.time

t = now()
for x in xrange(10000):
    conn = Client(('localhost', 6000),)
    conn.send('wtf')


print '%ss with 10k loops' % (now() - t)