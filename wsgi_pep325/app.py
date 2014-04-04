#!/usr/bin/env python


# uwsgi --http 0:8002 -w app
import time

class App(object):
   def __call__(self, env, start_response):
        sr = start_response('200 OK', [
            ('Content-Type','text/plain'),
            ('Content-Length', '11'),
        ])
        print dir(sr)
        return self

   def __iter__(self):
       yield "hello world"

   def close(self):
       time.sleep(4)
       print "finished!"

application = App()



def clean_up(*args, **kwargs):
    print 'cleanup!', args, kwargs

def application1(env, start_response):
    # application1.close  = clean_up
    start_response('200 OK', [
        ('Content-Type','text/plain'),
        ('Content-Length', '11'),
    ])
    return ['Hello world']

