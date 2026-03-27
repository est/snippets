#!/usr/bin/env python3
import mmap
import sys
from collections import Counter

def words_from_mm(mm):
    buf = bytearray()
    for c in iter(lambda: mm.read(1), b''):
        if c.isspace():
            if buf:
                yield buf.decode('utf-8', 'ignore')
                buf.clear()
        else:
            buf.extend(c)



def main():
    path = sys.argv[1] if len(sys.argv) > 1 else "input.txt"
    with open(path, "rb") as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        freq = Counter(words_from_mm(mm))
    for w, c in freq.most_common():
        print(f"{c}\t{w}")

if __name__ == "__main__":
    main()

#########

import mmap, sys, codecs
from collections import Counter

def gen(mm):
    d = codecs.getincrementaldecoder('utf-8')(errors='ignore')
    b = bytearray()
    for c in iter(lambda: mm.read(8192), b''):
        b += d.decode(c, False)
        while b:
            i = b.find(32)
            n = b.find(10)
            if -1 == i and -1 == n: break
            i = i if -1 != i and (n == -1 or i < n) else n
            yield bytes(b[:i]).decode()
            del b[:i+1]
    if b: yield bytes(b).decode()

with open(sys.argv[1] if len(sys.argv) > 1 else "input.txt", "rb") as f:
    mm = mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ)
    for w, c in Counter(gen(mm)).most_common(): print(f"{c}\t{w}")
