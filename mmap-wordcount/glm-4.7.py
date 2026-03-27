import mmap
import re
from collections import Counter

def wordcount(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            text = mm.read().decode('utf-8')
            words = re.split(r'\s+', text.strip())
            return Counter(words)

if __name__ == '__main__':
    import sys
    if len(sys.argv) < 2:
        print('Usage: python mwc.py <file_path>')
        sys.exit(1)
    
    counter = wordcount(sys.argv[1])
    for word, count in counter.most_common():
        print(f'{word}: {count}')
