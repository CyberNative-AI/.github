"""Contest-rule checkers for the four LCB-100 problems that accept more than one answer.

Written from the problem statements (LCB question_content) before reading the GVS5H
authors' checkers. Each returns True (accept) / False (reject).
  check(qid, inp, expected, got)
`expected` is the stored reference output; it decides feasibility (-1 / No) and the optimum.
"""
from decimal import Decimal, InvalidOperation

MULTI = {"abc385_f", "abc396_e", "arc190_a", "arc195_c"}


def _ints(tokens):
    return [int(t) for t in tokens]


def abc385_f(inp, expected, got):
    # "absolute or relative error of at most 10^-9"; "-1.000 or similar would be incorrect"
    e, g = expected.split(), got.split()
    if len(g) != 1 or len(e) != 1:
        return False
    if e[0] == "-1" or g[0] == "-1":
        return e[0] == g[0] == "-1"
    try:
        a, b = Decimal(g[0]), Decimal(e[0])
    except InvalidOperation:
        return False
    if not a.is_finite():
        return False
    err = abs(a - b)
    return err <= Decimal("1e-9") or err <= Decimal("1e-9") * abs(b)


def abc396_e(inp, expected, got):
    t = inp.split()
    n, m = int(t[0]), int(t[1])
    cons = [(int(t[2 + 3 * i]) - 1, int(t[3 + 3 * i]) - 1, int(t[4 + 3 * i])) for i in range(m)]
    e, g = expected.split(), got.split()
    if e == ["-1"]:
        return g == ["-1"]
    if len(g) != n:
        return False
    try:
        a = _ints(g)
    except ValueError:
        return False
    if any(v < 0 for v in a):
        return False
    if any(a[x] ^ a[y] != z for x, y, z in cons):
        return False
    return sum(a) == sum(_ints(e))


def arc190_a(inp, expected, got):
    t = inp.split()
    n, m = int(t[0]), int(t[1])
    seg = [(int(t[2 + 2 * i]), int(t[3 + 2 * i])) for i in range(m)]
    e, g = expected.split(), got.split()
    if e == ["-1"]:
        return g == ["-1"]
    if len(g) != m + 1:
        return False
    try:
        k, ops = int(g[0]), _ints(g[1:])
    except ValueError:
        return False
    if k != int(e[0]) or any(o not in (0, 1, 2) for o in ops) or sum(o != 0 for o in ops) != k:
        return False
    diff = [0] * (n + 2)
    for (l, r), o in zip(seg, ops):
        if o == 1:
            diff[l] += 1
            diff[r + 1] -= 1
        elif o == 2:
            diff[1] += 1
            diff[l] -= 1
            diff[r + 1] += 1
            diff[n + 1] -= 1
    run = 0
    for j in range(1, n + 1):
        run += diff[j]
        if run <= 0:
            return False
    return True


def arc195_c(inp, expected, got):
    t = inp.split()
    T = int(t[0])
    cases = [(int(t[1 + 2 * i]), int(t[2 + 2 * i])) for i in range(T)]
    e, g = expected.split(), got.split()
    ei = gi = 0
    LIM = 10 ** 9
    for R, B in cases:
        if ei >= len(e) or gi >= len(g):
            return False
        ev, gv = e[ei], g[gi]
        ei += 1
        gi += 1
        if ev not in ("Yes", "No") or gv != ev:
            return False
        if ev == "No":
            continue
        ei += 3 * (R + B)
        pieces = []
        for _ in range(R + B):
            if gi + 3 > len(g):
                return False
            p, r, c = g[gi], g[gi + 1], g[gi + 2]
            gi += 3
            if p not in ("R", "B"):
                return False
            try:
                r, c = int(r), int(c)
            except ValueError:
                return False
            if not (1 <= r <= LIM and 1 <= c <= LIM):
                return False
            pieces.append((p, r, c))
        if sum(p == "R" for p, _, _ in pieces) != R or sum(p == "B" for p, _, _ in pieces) != B:
            return False
        if len({(r, c) for _, r, c in pieces}) != len(pieces):
            return False
        k = len(pieces)
        for i in range(k):
            p, r, c = pieces[i]
            _, r2, c2 = pieces[(i + 1) % k]
            dr, dc = abs(r - r2), abs(c - c2)
            if p == "R" and dr + dc != 1:
                return False
            if p == "B" and not (dr == 1 and dc == 1):
                return False
    return gi == len(g) and ei == len(e)


CHECKERS = {"abc385_f": abc385_f, "abc396_e": abc396_e, "arc190_a": arc190_a, "arc195_c": arc195_c}


def check(qid, inp, expected, got):
    try:
        return bool(CHECKERS[qid](inp, expected, got))
    except Exception:  # malformed submitted output (overflow, bad tokens) is a wrong answer
        return False
