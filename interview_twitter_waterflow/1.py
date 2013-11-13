#!/usr/env/bin python


# http://www.reddit.com/r/programming/comments/1qc8iw/a_functional_solution_to_twitters_waterflow/
# http://philipnilsson.github.io/Badness10k/articles/waterflow/


sign = lambda x:cmp(x, 0)

def get_volumn(seq):
    total = 0
    for level in xrange(max(seq)-1, -1, -1):
        row = [ 1 if row-level > 0 else 0 for row in seq]
        first = row.index(1)
        last = len(row) - row[::-1].index(1) - 1
        # print row, first, last
        if last - first > 0:
            total += row[first:last].count(0)
    return total

if '__main__' == __name__:
   testcases = [
         ([1,0,1], 1),
         ([5,0,5], 5),
         ([0,1,0,1,0], 1),
         ([1,0,1,0], 1),
         ([1,0,1,2,0,2], 3),
         ([2,5,1,2,3,4,7,7,6], 10),
         ([ 2, 5, 1, 3, 1, 2, 1, 7, 7, 6], 17),
         ([5,1,0,1],1),                 # thanks https://news.ycombinator.com/item?id=6640085
         ([2,5,1,2,3,4,7,7,6,3,5], 12), # thanks https://news.ycombinator.com/item?id=6640105
         ((5,1,0,1), 1),
         ([2,0,1], 1),
         ]
 
   for case in testcases:
      w = get_volumn(case[0])
      if w == case[1]:
         print "TRUE: %s holds %s" % (case[0], w)
      else:
         print "MISMATCH: %s holds %s (got %s)" % (case[0], case[1], w)
