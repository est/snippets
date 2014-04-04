import time

import redis

now = time.time

r = None
t = now()
for x in xrange(10000):
	r = redis.Redis()
	r.set('wtf', 'haha')


print '%ss with 10k loops' % (now() - t)
print r.get('wtf')