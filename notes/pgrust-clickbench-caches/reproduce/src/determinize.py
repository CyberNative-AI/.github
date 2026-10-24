"""Write a determinized copy of the 43 queries: every ORDER BY gets the select-list positions appended as
tie-breakers (SELECT * gets positions 1-10), a query without ORDER BY gets ORDER BY 1..k. LIMIT/OFFSET kept.
Used only to adjudicate cross-mode answer differences (ties under LIMIT are legal nondeterminism)."""
import re, sys

def split_top(s):
    out, depth, cur = [], 0, ''
    for ch in s:
        if ch == '(':
            depth += 1
        elif ch == ')':
            depth -= 1
        if ch == ',' and depth == 0:
            out.append(cur); cur = ''
        else:
            cur += ch
    out.append(cur)
    return out

def determinize(q):
    q = q.strip().rstrip(';')
    sel = re.match(r'(?is)^SELECT\s+(.*?)\s+FROM\s', q).group(1)
    k = 10 if sel.strip() == '*' else len(split_top(sel))
    keys = ', '.join(str(i) for i in range(1, k + 1))
    m = re.search(r'(?is)\s(LIMIT\s.*)$', q)
    head, tail = (q[:m.start()], ' ' + m.group(1)) if m else (q, '')
    if re.search(r'(?i)\sORDER BY\s', head):
        head = head + ', ' + keys
    else:
        head = head + ' ORDER BY ' + keys
    return head + tail + ';'

if __name__ == '__main__':
    src, dst = sys.argv[1], sys.argv[2]
    with open(src, encoding='utf-8') as f, open(dst, 'w', encoding='utf-8', newline='\n') as g:
        for line in f:
            if line.strip():
                g.write(determinize(line) + '\n')
