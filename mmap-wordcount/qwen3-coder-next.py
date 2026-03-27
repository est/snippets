import mmap
import re
from collections import Counter

def word_count(filepath):
    with open(filepath, 'rb') as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            text = mm.read().decode('utf-8', errors='ignore')
            words = re.findall(r'\S+', text)
            return Counter(words)


def word_count_v2(filepath):
    with open(filepath, 'rb') as f:
        with mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
            decoder = codecs.getincrementaldecoder('utf-8')()
            words = []
            for chunk in iter(lambda: mm.read(65536), b''):
                text = decoder.decode(chunk)
                words.extend(re.findall(r'\S+', text))
            words.extend(decoder.decode(b'', final=True))
            return Counter(words)

