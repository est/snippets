import codecs, re
from collections import Counter

def word_count(path):
    freq = Counter()
    dec = codecs.getincrementaldecoder("utf-8")().decode
    w = re.compile(r'\w+')
    tail = ""

    with open(path, "rb") as f:
        while chunk := f.read(65536):
            s = tail + dec(chunk)
            parts = w.finditer()
            tail = parts.pop() if parts and not s[-1].isspace() else ""
            freq.update(parts)
        s = tail + dec(b"", final=True)
        freq.update(s.split())

    return freq
