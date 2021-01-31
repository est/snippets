# coding: utf-8

from gevent import monkey

monkey.patch_all()

import random

from gevent.pool import Pool

p = Pool(3)


def rand_exc(_):
    r = random.random()
    if r > 0.9:
        raise Exception('2333')
    return r


r = list(p.imap_unordered(rand_exc, range(100)))
print(r)
