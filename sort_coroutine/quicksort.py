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






def inplace_quick_sort(v, begin, end):  # list, int, int
    "pastebin.com/ux5rRvfn"
    if end - begin > 0:  # only perform quicksort if we are dealing with > 1 values        
        pivot = v[begin] # we set the first item as our initial pivot
        i,j = begin,end  
        while j > i:
            while v[i] <= pivot and j > i:
                i+=1
            while v[j] > pivot and j >= i:
                j-=1
            if j > i:
                v[i], v[j] = v[j], v[i]
        v[begin],v[j] = v[j],v[begin]
        inplace_quick_sort(v, begin, j-1)
        inplace_quick_sort(v, j+1, end)
 


# http://stackoverflow.com/questions/17773516/in-place-quicksort-in-python

# def sub_partition(array, start, end, idx_pivot):

#     'returns the position where the pivot winds up'

#     if not (start <= idx_pivot <= end):
#         raise ValueError('idx pivot must be between start and end')

#     array[start], array[idx_pivot] = array[idx_pivot], array[start]
#     pivot = array[start]
#     i = start + 1
#     j = start + 1

#     while j <= end:
#         if array[j] <= pivot:
#             array[j], array[i] = array[i], array[j]
#             i += 1
#         j += 1

#     array[start], array[i - 1] = array[i - 1], array[start]
#     return i - 1

# def inplace_quick_sort(array, start=0, end=None):

#     if end is None:
#         end = len(array) - 1

#     if end - start < 1:
#         return

#     idx_pivot = random.randint(start, end)
#     i = sub_partition(array, start, end, idx_pivot)
#     #print array, i, idx_pivot
#     inplace_quick_sort(array, start, i - 1)
#     inplace_quick_sort(array, i + 1, end)


def group_by_cmp1(pivot, items):
    "return (lesser, equal_or_greater)"
    l = []
    g = []
    for x in items:
        if x < pivot:
            l.append(x)
        else:
            g.append(x)
    return l, g


def group_by_cmp2(pivot, items):
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
        l, g = group_by_cmp2(p, items[1:])
        return my_qsort2(l) + [p] + my_qsort2(g)


def my_qsort3(items):
    if items == []:
        return []
    else:
        p = items.pop()
        l, g = group_by_cmp2(p, items)
        return my_qsort3(l) + [p] + my_qsort3(g)

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


        s0 = sorted(l)
        # s1 = my_qsort1(l)
        s2 = my_qsort2(l[:])
        s3 = my_qsort3(l[:])
        # inplace_quick_sort(l, 0, len(l)-1)
        # s1 = l
        if s0==s2==s3:
            print 'ok', l
        else:
            print 'false', s1, s2, l