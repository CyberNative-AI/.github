import random, sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent))
from score import lev, lev_sg, norm, cer, cer_sg, bigram_f1

def naive(a, b):
    prev = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return prev[-1]

rng = random.Random(1)
alpha = "abcকখগ্া"
for _ in range(3000):
    a = "".join(rng.choice(alpha) for _ in range(rng.randrange(0, 90)))
    b = "".join(rng.choice(alpha) for _ in range(rng.randrange(0, 90)))
    assert lev(a, b) == naive(a, b), (a, b)
def naive_sg(a, b):
    prev = [0] * (len(b) + 1)
    for i, ca in enumerate(a, 1):
        cur = [i]
        for j, cb in enumerate(b, 1):
            cur.append(min(prev[j] + 1, cur[j - 1] + 1, prev[j - 1] + (ca != cb)))
        prev = cur
    return min(prev)

for _ in range(3000):
    a = "".join(rng.choice(alpha) for _ in range(rng.randrange(1, 60)))
    b = "".join(rng.choice(alpha) for _ in range(rng.randrange(0, 120)))
    assert lev_sg(a, b) == naive_sg(a, b), (a, b)
assert lev_sg("body", "HEAD 12 body FOOT") == 0 and cer_sg("xx body yy", "body")[0] == 0.0
assert cer_sg("bod", "body")[0] == 0.25
assert norm("a b‌\nc­") == "abc"
assert cer("abc", "abc") == (0.0, 0.0)
assert cer("", "abcd") == (1.0, 1.0)
assert cer("abcdabcdab", "abcd")[0] == 1.0 and cer("abcdabcdab", "abcd")[1] == 1.5
assert bigram_f1("ab cd", "abcd") == 1.0 and bigram_f1("", "abcd") == 0.0
long_a = "".join(rng.choice(alpha) for _ in range(3000)); long_b = long_a[::-1]
import time; t = time.time(); lev(long_a, long_b); print("3000x3000 s", round(time.time() - t, 3))
print("OK")
