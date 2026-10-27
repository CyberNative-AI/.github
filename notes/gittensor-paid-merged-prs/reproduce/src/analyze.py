"""Analyzer: fixed H1/H2 rules (test-plan.md, incl. AMENDMENT-01). Writes out/results.json.

Every ruled key is computed here; nothing is defaulted. Exploratory E2/E3 counts are reported, not ruled.
"""
import json, os, re, sys
from collections import Counter, defaultdict
from datetime import timedelta
sys.path.insert(0, os.path.dirname(__file__))
from collect import frame, load, p, wins, decided90, T1, T2, search  # search used read-only via cache

OUTSIDE = {'NONE', 'FIRST_TIMER', 'FIRST_TIME_CONTRIBUTOR', 'CONTRIBUTOR'}
INSIDE = {'OWNER', 'MEMBER', 'COLLABORATOR'}
PROGRAM_START = '2025-10-29T13:21:57Z'
BAN_RE = re.compile(r'\b(ban|banned|block|blocked|spam|policy|not accept|no longer accept|close all|low[- ]quality|ai[- ]generated|slop)\b', re.I)


def merged90(r):
    return bool(r['merged_at']) and p(r['merged_at']) - p(r['created_at']) <= timedelta(days=90)


def rate(rows):
    d = [r for r in rows if decided90(r)]
    return (sum(merged90(r) for r in d) / len(d) if d else None), len(d)


def h1_rule(d):
    if d >= -0.05: return 'ACCEPTED'
    if d <= -0.15: return 'LOWER'
    return 'SIMILAR-LOWER'


def h2_rule(x):
    if x <= 0.30: return 'LOW-PERSISTENCE'
    if x >= 0.70: return 'DURABLE'
    return 'PARTIAL'


def main():
    reg, M, iv, indep, eligible, rows = frame()
    rows = [r for r in rows if not r['author'].endswith('[bot]')]
    # first PR per (miner, repo) for recruited-pair key
    first_pr = {}
    for r in rows:
        k = (r['author'].lower(), r['repo'].lower())
        first_pr[k] = min(first_pr.get(k, r['created_at']), r['created_at'])
    recruited = lambda r: first_pr[(r['author'].lower(), r['repo'].lower())] >= PROGRAM_START

    # ---------- H1 ----------
    units = [r for r in rows if indep(r['repo']) and eligible(r['repo'], r['created_at']) and r['created_at'] < T1
             and not r.get('draft') and r['assoc'] not in INSIDE]
    base_repos = json.load(open('out/baseline_repos.json'))
    def base_rows(path):
        out = defaultdict(list)
        for b in load(path):
            if b['author'] and b['author'].lower() not in M and not b['author'].endswith('[bot]') \
                    and b.get('author_type') != 'Bot' and b['assoc'] in OUTSIDE and not b.get('draft'):
                out[b['_repo_key']].append(b)
        return out
    def h1(base, subset=None, drop_repo=None, drop_miner=None):
        by = defaultdict(list)
        for r in units:
            if subset and not subset(r): continue
            if drop_miner and r['author'].lower() == drop_miner: continue
            by[r['repo'].lower()].append(r)
        ds, ws, per = [], [], {}
        for repo in base_repos:
            if repo == drop_repo: continue
            m, nm = rate(by.get(repo, []))
            b, nb = rate(base.get(repo, []))
            if m is None or nm < 3 or b is None or nb < 5: continue
            ds.append(m - b); ws.append(nm); per[repo] = (round(m, 4), nm, round(b, 4), nb)
        if not ds:
            return {'n_repos': 0}
        wd = sum(d * w for d, w in zip(ds, ws)) / sum(ws)
        sd = sorted(ds); med = (sd[(len(sd) - 1) // 2] + sd[len(sd) // 2]) / 2
        return {'n_repos': len(ds), 'weighted_d': round(wd, 4), 'median_d': round(med, 4), 'per_repo': per,
                'miner_decided': sum(ws)}
    base_pre, base_in = base_rows('raw/baseline_pre_prs.jsonl'), base_rows('raw/baseline_in_prs.jsonl')
    H1 = h1(base_pre)
    res = {'frame': {'miners_searchable_rows_authors': len({r['author'].lower() for r in rows}), 'pr_rows': len(rows),
                     'h1_units': len(units), 'baseline_repos': len(base_repos)}}
    if H1['n_repos'] >= 30:
        dec_by_repo = Counter(r['repo'].lower() for r in units if decided90(r) and r['repo'].lower() in H1['per_repo'])
        dec_by_miner = Counter(r['author'].lower() for r in units if decided90(r) and r['repo'].lower() in H1['per_repo'])
        top_repo, top_miner = dec_by_repo.most_common(1)[0][0], dec_by_miner.most_common(1)[0][0]
        lro, lmo = h1(base_pre, drop_repo=top_repo), h1(base_pre, drop_miner=top_miner)
        br = {h1_rule(H1['weighted_d']), h1_rule(lro['weighted_d']), h1_rule(lmo['weighted_d'])}
        ruling = h1_rule(H1['weighted_d']) if len(br) == 1 else 'FRAGILE'
        H1.update(leave_top_repo_out=lro['weighted_d'], leave_top_miner_out=lmo['weighted_d'],
                  top_repo_share=round(dec_by_repo[top_repo] / sum(dec_by_repo.values()), 4),
                  top_miner_share=round(dec_by_miner[top_miner] / sum(dec_by_miner.values()), 4))
    else:
        ruling = 'UNDERPOWERED'
    pooled_m = rate([r for r in units if r['repo'].lower() in H1.get('per_repo', {})])
    pooled_b = rate([b for repo in H1.get('per_repo', {}) for b in base_pre.get(repo, [])])
    res['H1'] = {'ruling': ruling, **{k: v for k, v in H1.items() if k != 'per_repo'},
                 'pooled_miner': pooled_m, 'pooled_baseline_pre': pooled_b,
                 'secondary_in_program_baseline': {k: v for k, v in h1(base_in).items() if k != 'per_repo'},
                 'recruited_pairs': {k: v for k, v in h1(base_pre, subset=recruited).items() if k != 'per_repo'},
                 'existing_pairs': {k: v for k, v in h1(base_pre, subset=lambda r: not recruited(r)).items() if k != 'per_repo'},
                 'merged90_over_all_created_miner': round(sum(merged90(r) for r in units) / len(units), 4) if units else None}

    # ---------- H2 ----------
    def counts(cut, group, t, rec_only=True, drop_repo=None, drop_miner=None, exclude=()):
        info = json.load(open(f'out/{cut}_{group}_count_repos.json'))
        w = info['windows']; repos = [r for r in info['repos'] if r != drop_repo and r not in exclude]
        rs = set(repos)
        nm = {k: 0 for k in w}; nc = {k: 0 for k in w}; miners_pre = Counter(); repos_pre = set()
        post_by_miner = Counter()
        for r in rows:
            rk = r['repo'].lower()
            if rk not in rs: continue
            if drop_miner and r['author'].lower() == drop_miner: continue
            for k, (a, b) in w.items():
                if a <= r['created_at'] <= b:
                    if not rec_only or recruited(r):
                        nm[k] += 1
                        if k == 'pre': miners_pre[r['author'].lower()] += 1; repos_pre.add(rk)
                        if k == 'post': post_by_miner[r['author'].lower()] += 1
        allm = {k: 0 for k in w}
        for repo in repos:
            for k, (a, b) in w.items():
                _, tot, _ = search(f'repo:{repo} type:pr created:{a}..{b}')
                if tot is None: raise SystemExit(f'missing count {repo} {k}')
                nc[k] += tot
        for r in rows:  # subtract ALL miner PRs (recruited or not) from the repo totals
            rk = r['repo'].lower()
            if rk in rs:
                for k, (a, b) in w.items():
                    if a <= r['created_at'] <= b: allm[k] += 1
        nc = {k: nc[k] - allm[k] for k in w}
        def ratio(a, b):
            return (nm[b] / nm[a]) / (nc[b] / nc[a]) if nm[a] and nc[a] and nc[b] else None
        stay3 = [m for m, c in miners_pre.items() if c >= 3]
        return {'N_m': nm, 'N_c': nc, 'repos': len(repos), 'repos_with_pre_miner_pr': len(repos_pre),
                'miners_pre': len(miners_pre), 'ratio': ratio('pre', 'post'), 'placebo': ratio('prepre', 'pre'),
                'top_repo': None, 'miners_ge3_pre': len(stay3),
                'miners_ge3_pre_with_post': sum(1 for m in stay3 if post_by_miner[m] > 0), 'miners_pre_counter': miners_pre}
    c1 = counts('cut1', 'dropped', T1)
    # ban screen: hits authored by non-miners are candidates; a separately written label file decides (required, no default)
    cand = defaultdict(list)
    for b in load('raw/ban_screen.jsonl'):
        if b.get('author') and b['author'].lower() not in M and not b['author'].endswith('[bot]'):
            cand[b['_repo_key']].append({'number': b['number'], 'author': b['author'], 'created_at': b['created_at']})
    json.dump(cand, open('out/ban_candidates.json', 'w'), indent=1, sort_keys=True)
    labels = json.load(open('out/ban_labels.json'))  # {repo: true|false}; missing file/keys = malformed
    missing = sorted(set(cand) - set(labels))
    if missing:
        raise SystemExit(f'ban_labels.json lacks {len(missing)} candidate repos')
    res['H2_ban_screen'] = {'candidate_repos': len(cand), 'labelled_reaction_repos': sorted(k for k, v in labels.items() if v)}
    res['H2_ban_screen_hits'] = {k: True for k, v in labels.items() if v}
    if c1['N_m']['pre'] >= 100 and c1['repos_with_pre_miner_pr'] >= 20 and c1['miners_pre'] >= 10 and c1['ratio'] is not None:
        pl = c1['placebo']
        if pl is None or not (0.70 <= pl <= 1.43):
            r2 = 'CONFOUNDED'
        else:
            info = json.load(open('out/cut1_dropped_count_repos.json'))
            w = info['windows']
            by_repo = Counter(r['repo'].lower() for r in rows if r['repo'].lower() in set(info['repos'])
                              and w['pre'][0] <= r['created_at'] <= w['pre'][1] and recruited(r))
            top_repo = by_repo.most_common(1)[0][0]; top_miner = c1['miners_pre_counter'].most_common(1)[0][0]
            lro = counts('cut1', 'dropped', T1, drop_repo=top_repo)['ratio']
            lmo = counts('cut1', 'dropped', T1, drop_miner=top_miner)['ratio']
            nob = counts('cut1', 'dropped', T1, exclude=set(res['H2_ban_screen_hits']))['ratio']
            br = {h2_rule(x) for x in (c1['ratio'], lro, lmo, nob) if x is not None}
            r2 = h2_rule(c1['ratio']) if len(br) == 1 else 'FRAGILE'
            c1.update(leave_top_repo_out=lro, leave_top_miner_out=lmo, without_ban_screen_hits=nob)
    else:
        r2 = 'UNDERPOWERED'
    c1.pop('miners_pre_counter')
    ex = counts('cut1', 'dropped', T1, rec_only=False); ex.pop('miners_pre_counter')
    st = counts('cut1', 'stayed', T1); st.pop('miners_pre_counter')
    c2 = counts('cut2', 'dropped', T2); c2.pop('miners_pre_counter')
    res['H2'] = {'ruling': r2, 'cut1_recruited': c1, 'cut1_all_pairs': ex, 'cut1_stayers': st,
                 'd1_over_stayers': (c1['ratio'] / st['ratio']) if c1['ratio'] and st['ratio'] and st['repos_with_pre_miner_pr'] >= 10 else None,
                 'cut2_recruited': c2}

    # ---------- exploratory ----------
    month = defaultdict(Counter)
    for r in rows:
        if r['merged_at'] and eligible(r['repo'], r['created_at']):
            cls = 'self' if r['repo'].split('/')[0].lower() == r['author'].lower() or r['assoc'] in INSIDE else \
                  ('independent' if indep(r['repo']) else 'ecosystem_or_later')
            month[r['merged_at'][:7]][cls] += 1
    res['E2_merged_paid_eligible_by_month'] = {k: dict(v) for k, v in sorted(month.items())}
    dec = [r for r in rows if indep(r['repo']) and eligible(r['repo'], r['created_at']) and r['created_at'] < T1 and decided90(r)]
    res['E3_inside_assoc_share_of_decided'] = round(sum(r['assoc'] in INSIDE for r in dec) / len(dec), 4) if dec else None
    os.makedirs('out', exist_ok=True)
    json.dump(res, open('out/results.json', 'w'), indent=1, sort_keys=True, default=str)
    print(json.dumps({'H1': res['H1']['ruling'], 'H2': res['H2']['ruling']}))


if __name__ == '__main__':
    main()
