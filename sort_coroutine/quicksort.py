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



def group_by_cmp(pivot, items):
    "return (lesser, equal_or_greater)"
    l = []
    g = []
    [ l.append(x) if x < pivot else g.append(x) for x in items ]
    return l, g

def my_qsort2(items):
    if items == []:
        return []
    else:
        p = items[0]
        l, g = group_by_cmp(p, items[1:])
        return my_qsort2(l) + [p] + my_qsort2(g)


def groupby(func, items):
    r = {}
    for x in items:
        k = func(x)
        r.setdefault(k, []).append(x)
    print items, r
    return r

def my_qsort1(items):
    if items == []:
        return []
    else:
        pivot = items[0]
        p = groupby( lambda x:-cmp(pivot, x), items[1:] )
        return my_qsort1(p.get(-1, [])) + [pivot] + my_qsort1(p.get(0, [])+p.get(1, []) )

# @ToDo: use .pop()


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


if '__main__' == __name__:
    for _ in range(10):
        # l = range(10)
        # random.shuffle(l)
        l = [random.randint(0, 5) for x in range(10)]
        s1 = my_qsort2(l)
        s2 = sorted(l)
        print s1==s2, s1, l