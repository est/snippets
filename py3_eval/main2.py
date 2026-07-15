#!/usr/bin/env python

def safe_eval(code):
    return eval(code.replace('__', ''), {'__builtins__': None}, {}) 

