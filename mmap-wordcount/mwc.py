import mmap, codecs
from collections import Counter

def word_count(filepath):
    freq = Counter()
    decode = codecs.getincrementaldecoder('utf-8')().decode
    with open(filepath, 'rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        for chunk in iter(lambda: mm.read(65536), b''):
            freq.update(decode(chunk).split())
        freq.update(decode(b'', final=True).split())
        return freq
