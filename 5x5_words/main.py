import string, time
from itertools import combinations


words = [w[:-1] for w in open('words_alpha.txt') if len(w) == 6 == len(set(w))]
anagrams = {}
for x in words:
    anagrams.setdefault(''.join(sorted(x)), []).append(x)
candidates = [v[0] for v in anagrams.values()]
print('candidates: %d' % (len(candidates)))

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
        # letters.add(c1)
        for c2, b2 in b1.items():
            if c2 in letters:
                continue
            # letters.add(c2)
            for c3, b3 in b2.items():
                if c3 in letters:
                    continue
                # letters.add(c3)
                for c4, b4 in b3.items():
                    if c4 in letters:
                        continue
                    # letters.add(c4)
                    for c5, b5 in b4.items():
                        if c5 in letters:
                            continue
                        # letters.add(c5)
                        yield ''.join((c1, c2, c3, c4, c5))


t = time.time()
for i, w1 in enumerate(candidates):
    print('%.1fs %s' % ((time.time() - t) / (i + 1), w1))
    for w2 in choose_without(set(w1)):
        for w3 in choose_without(set(w1+w2)):
            for w4 in choose_without(set(w1+w2+w3)):
                for w5 in choose_without(set(w1+w2+w3+w4)):
                    print(w1+w2+w3+w4+w5)
