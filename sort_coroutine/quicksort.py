import random, functools, itertools

def qsort1(list):
    """Quicksort using list comprehensions"""
    if list == []: 
        return []
    else:
        pivot = list[0]
        lesser = qsort1([x for x in list[1:] if x < pivot])
        greater = qsort1([x for x in list[1:] if x >= pivot])
        return lesser + [pivot] + greater


def groupby(func, items):
    r = {}
    for x in items:
        k = func(x)
        r.setdefault(k, []).append(x)
    return r

def my_qsort1(items):
    if items == []:
        return []
    else:
        pivot = items.pop()
        p = groupby( functools.partial(cmp, pivot), items )
        return my_qsort1(p[-1]) + [p[0]] + my_qsort1(p[1])

def partition(items, l, e, g):
    print 'ha', items, l, e, g
    if items == []:
    	return (l, e, g)
    else:
        head = items[0]
        if head < e[0]:
            return partition(items[1:], l + [head], e, g)
        elif head > e[0]:
            return partition(items[1:], l, e, g + [head])
        else:
            return partition(items[1:], l, e + [head], g)

def qsort2(items):
    """Quicksort using a partitioning function"""
    if items == []: 
        return []
    else:
        pivot = items[0]
        lesser, equal, greater = partition(items[1:], [], [pivot], [])
        return qsort2(lesser) + equal + qsort2(greater)



"""
True [2, 6, 1, 9, 8, 5, 4, 3, 0, 7] [0, 1, 2, 3, 4, 5, 6, 7, 8, 9]
ha [6, 1, 9, 8, 5, 4, 3, 0, 7] [] [2] []
ha [1, 9, 8, 5, 4, 3, 0, 7] [] [2] [6]
ha [9, 8, 5, 4, 3, 0, 7] [1] [2] [6]
ha [8, 5, 4, 3, 0, 7] [1] [2] [6, 9]
ha [5, 4, 3, 0, 7] [1] [2] [6, 9, 8]
ha [4, 3, 0, 7] [1] [2] [6, 9, 8, 5]
ha [3, 0, 7] [1] [2] [6, 9, 8, 5, 4]
ha [0, 7] [1] [2] [6, 9, 8, 5, 4, 3]
ha [7] [1, 0] [2] [6, 9, 8, 5, 4, 3]
ha [] [1, 0] [2] [6, 9, 8, 5, 4, 3, 7]

ha [0] [] [1] []
ha [] [0] [1] []
ha [] [] [0] []

ha [9, 8, 5, 4, 3, 7] [] [6] []
ha [8, 5, 4, 3, 7] [] [6] [9]
ha [5, 4, 3, 7] [] [6] [9, 8]
ha [4, 3, 7] [5] [6] [9, 8]
ha [3, 7] [5, 4] [6] [9, 8]
ha [7] [5, 4, 3] [6] [9, 8]
ha [] [5, 4, 3] [6] [9, 8, 7]

ha [4, 3] [] [5] []
ha [3] [4] [5] []
ha [] [4, 3] [5] []
ha [3] [] [4] []
ha [] [3] [4] []
ha [] [] [3] []
ha [8, 7] [] [9] []
ha [7] [8] [9] []
ha [] [8, 7] [9] []
ha [7] [] [8] []
ha [] [7] [8] []
ha [] [] [7] []
"""

if '__main__' == __name__:
	for _ in range(10):
 		l = range(1000)
 		random.shuffle(l)
 		s1 = my_qsort1(l)
 		s2 = sorted(l)
 		print s1==s2