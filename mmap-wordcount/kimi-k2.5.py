import mmap
import sys
from collections import Counter

def wordcount(path):
    with open(path, 'rb') as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            text = mm.decode('utf-8', errors='ignore')
            words = text.split()
            return Counter(words)

if __name__ == '__main__':
    for word, count in wordcount(sys.argv[1]).most_common():
        print(f"{count}\t{word}")
