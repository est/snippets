import mmap, codecs
from collections import Counter

def word_count(filepath):
    feq = Counter()
    decoder = codecs.getincrementaldecoder('utf-8')()
    with open(filepath, 'rb') as f, mmap.mmap(f.fileno(), 0, access=mmap.ACCESS_READ) as mm:
        for chunk in iter(lambda: mm.read(65536), b''):
            freq.update(decoder.decode(chunk).split())
        freq.update(decoder.decode(b'', final=True).split())
        return freq
