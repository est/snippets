#!/usr/bin/env python
# coding: utf8

import urllib2
import time

url = 'https://www.v2ex.com/member/est/replies?p=%s'


for x in xrange(313, 0, -1):
    try:
        r = urllib2.urlopen(url % x).read()
    except:
        continue
    open('%s.html' % x, 'w').write(r)
    time.sleep(2)
