def merge1(left, right):
    result = []
    left_idx, right_idx = 0, 0
    while left_idx < len(left) and right_idx < len(right):
        # change the direction of this comparison to change the direction of the sort
        if left[left_idx] <= right[right_idx]:
            result.append(left[left_idx])
            left_idx += 1
        else:
            result.append(right[right_idx])
            right_idx += 1
 
    if left:
        result.extend(left[left_idx:])
    if right:
        result.extend(right[right_idx:])
    return result


from heapq import merge as merge2

def merge3(left,right):
    if not left or not right:
        return left + right
    elif left[0] <= right[0]:
        return [left[0]] + merge3(left[1:], right)
    else:
        return merge3(right,left)


def merge_sort(l):
    # Assuming l is a list, returns an
    # iterator on a sorted version of
    # the list.
    L = len(l)
    if L <= 1:
        return iter(l)
    else:
        m = L/2
        left = merge_sort(l[0:m])
        right = merge_sort(l[m:])
        return merge(left, right)

if '__main__' == __name__:
    merge = merge1
    
