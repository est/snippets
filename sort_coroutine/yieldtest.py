import random

def g(s=1):
	if s == 6:
		yield 2
	else:
		s+=1
		for i in g(s):
			yield i


def yy():
	yield (yield 1)

def yyy():
	yield (yield (yield 1))

def incr_sorted(size=10):
	a = []
	for x in range(size):
		a.append((yield sorted(a)))


def yield_sort(l):
    a=incr_sorted()
    a.next()
    r = None
    for x in range(len(l)-1):
        r = a.send(l[x])
    print r

if 0:#'__main__' == __name__:
    print yield_sort([3,4,3,2,1,3,1,2,3,4,])



def defyield():
    for x in range(5):
        def y1():
            yield x
        def y2():
            return x
        yield y1()

if 0: #'__main__' == __name__:
    a = list(defyield())
    print a


def oe_splitter(s):
    "given integer list `s`, return (odd_generator, even_generator)"
    o, e = [], []
    for x in s:
        o.append(x) if x%2==0 else e.append(x)
    return iter(o), iter(e)

if '__main__' == __name__:
    l = [random.randint(0,10) for x in range(5)]
    o, e = oe_splitter(l)
    print l, list(o), list(e)