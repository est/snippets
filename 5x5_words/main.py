import string
from itertools import combinations


candidates = [w[:-1] for w in open('words_alpha.txt') if len(w) == 6 == len(set(w))]

trie = {}
for w in candidates:
    b = trie
    for c in w:
        b = b.setdefault(c, {})

l26 = string.ascii_lowercase

results = []


def choose_without(letters):
    for c1, b1 in trie.items():
        if c1 in letters:
            continue
        letters.add(c1)
        for c2, b2 in b1.items():
            if c2 in letters:
                continue
            letters.add(c2)
            for c3, b3 in b2.items():
                if c3 in letters:
                    continue
                letters.add(c3)
                for c4, b4 in b3.items():
                    if c4 in letters:
                        continue
                    letters.add(c4)
                    for c5, b5 in b4.items():
                        if c5 in letters:
                            continue
                        letters.add(c5)
                        return ''.join((c1, c2, c3, c4, c5))


for w in candidates:
    clique = set(w)
    result = [w]
    r = True
    while len(result) < 5 and r:
        r = choose_without(clique)
        if r:
            result.append(r)
        print(' '.join(result))
