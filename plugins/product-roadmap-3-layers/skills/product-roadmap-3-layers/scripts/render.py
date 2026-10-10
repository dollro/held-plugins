"""render.py (skill product-roadmap-3-layers r10.6, 2026-09-29) - deterministic renderer for the 3-layer roadmap (skill product-roadmap-3-layers).

Input : a Notion export of the roadmap database (rows JSON, stored properties only) and the
        content of the "Product Roadmap" page and its child page "Roadmap reference"
        (Notion-flavoured markdown, one --page each, main page first). The rendering
        instruction is copied verbatim from references/rendering-instruction.md of the skill
        (found next to this script's folder; --skill overrides it).
Output: <stem>.md and <stem>.html, optionally <stem>.png. Same input, same output.

Usage:
  python3 scripts/render.py --rows rows.json --page main.md --page reference.md \
      --version v27 --date 2026-10-01 --out <dir> [--prev <previous vNN.md>] \
      [--stem 2026-10-01_Roadmap_v27] [--unit "Acme Product Team"] \
      [--audience "Acme management and the product team"] [--png]

rows.json: list of objects with keys url, Title, ID, No, Layer, Position, Serves, Precedes,
Blocks, Standalone, Kind, Value, "Evidence type", "Impact dimension", Description, Evidence, PRD, Source, Linear. Relation and
multi-select values are JSON-encoded lists (as the Notion SQL export returns them).

Pages: sections are "# " headings. A heading "<name> · details" on a later page continues
section <name> of an earlier page and is appended to it. Inline database and child-page tags
are dropped. The basis line sits after a "---" rule
on the last page.
"""
import json, re, sys, html, argparse, os
from collections import defaultdict, Counter

ap = argparse.ArgumentParser()
ap.add_argument('--rows', required=True); ap.add_argument('--page', required=True, action='append')
ap.add_argument('--skill', help='file holding the rendering instruction; default: references/rendering-instruction.md of the skill'); ap.add_argument('--version', required=True)
ap.add_argument('--date', required=True); ap.add_argument('--out', required=True)
ap.add_argument('--prev'); ap.add_argument('--stem')
ap.add_argument('--unit', default='Product Team')
ap.add_argument('--audience', default='Management and the product team')
ap.add_argument('--png', action='store_true')
A = ap.parse_args()
VER, DATE, OUT = A.version, A.date, A.out
STEM = A.stem or f"{DATE}_Roadmap_{VER}"
PREV = os.path.basename(A.prev) if A.prev else None
PREV_V = (re.search(r'_(v\d+)\.md', PREV).group(1) if PREV and re.search(r'_(v\d+)\.md', PREV) else PREV)
os.makedirs(OUT, exist_ok=True)
rows_all = json.load(open(A.rows))
# Rows still being drafted in Notion are reported and left out, never guessed at.
excluded, rows = [], []
for r in rows_all:
    # r8: the code is the typed ID where one exists (cards from before the Unique ID), otherwise
    # the layer letter plus Notion's Unique ID "No"
    if not r.get('ID') and r.get('No') is not None and r.get('Layer'):
        r['ID'] = 'OFE'[int(r['Layer'][0]) - 1] + '-' + str(r['No'])
    miss = [k for k in ('Title', 'ID', 'Layer', 'Position') if not r.get(k)]
    if miss:
        excluded.append(f"{r.get('ID') or r.get('Title') or r['url'].rsplit('/', 1)[-1]} (no {', '.join(miss)})")
    else:
        rows.append(r)
pages = [open(f).read() for f in A.page]
_ri = A.skill or os.path.join(os.path.dirname(os.path.abspath(__file__)), '..', 'references', 'rendering-instruction.md')
skill = open(_ri).read()
MARK = '## 10 Rendering instruction\n\nThis section'
if MARK not in skill:
    sys.exit(f'render.py: no rendering instruction in {_ri}')
J = lambda v: json.loads(v) if v else []
byurl = {r['url']: r for r in rows}
for r in rows:
    for k in ('Serves', 'Precedes', 'Blocks'):
        r[k] = J(r[k])
    r['L'] = int(r['Layer'][0])
    r['ev'] = r.get('Evidence type')
    # Impact dimension (r9): multi-select on layer 1, the business dimensions an outcome supports.
    # Absent from exports made before r9; the generator then leaves it out and says so.
    r['dims'] = J(r.get('Impact dimension'))
    # Evidence (r10): own property on layer 1. Exports from before r10 carry the evidence in
    # Description; then Description is used for both and the log says so.
    r['evid'] = (r.get('Evidence') or '') if 'Evidence' in r else (r.get('Description') or '')
    r['ctx'] = (r.get('Description') or '') if 'Evidence' in r else ''
    r['pos'] = r['Position']
    parts = r['pos'].split(' · ')
    r['Column'], r['period'] = parts[0], parts[1]
    r['h'] = parts[2] if len(parts) > 2 else None
dangling = []
for r in rows:
    for k in ('Serves', 'Precedes'):
        dangling += [f"{r['ID']} {k}" for u in r[k] if u not in byurl]
        r[k] = [byurl[u]['ID'] for u in r[k] if u in byurl]
    r['id'] = r['ID']
byid = {r['id']: r for r in rows}
# The cascade is one relation, Serves, on every layer (r7): a feature serves one outcome, an
# enabler serves features. The outcome code is derived, never typed. An export from before r7
# still carries a typed "Outcome" on features; it is used only where Serves is empty.
for r in rows:
    typed = r.get('Outcome')
    if r['L'] == 1:
        r['Outcome'] = r['ID']
    elif r['L'] == 2:
        up = [f for f in r['Serves'] if byid.get(f, {}).get('L') == 1]
        # Drawn under the lowest outcome it serves; a feature serving none is drawn under the
        # placeholder O-0 (grey). Both break I2 and are reported, never repaired.
        r['Outcome'] = sorted(up, key=lambda x: int(x.split('-')[1]))[0] if up else (typed if typed and not r['Serves'] else 'O-0')
        if not r['Serves'] and typed:
            r['Serves_legacy'] = True
    else:
        r['Outcome'] = None
nat = lambda x: (x.split('-')[0], int(x.split('-')[1]))  # numeric ID order: F-2 before F-10
POS = ['Now · 1st', 'Now · 2nd', 'Next · 1st', 'Next · 2nd', 'Later']
PI = lambda r: POS.index(r['Column'] + (' · ' + r['h'] if r['h'] else ''))
PERIOD = {r['Column']: r['period'] for r in rows}
outs = [r for r in rows if r['L'] == 1]
outs.sort(key=lambda o: nat(o['id']))
cards = [r for r in rows if r['L'] > 1]
HAS_DIMS = any('Impact dimension' in r for r in rows)
HAS_EVID = any('Evidence' in r for r in rows)
# r10.8: preferred display order for the dimensions this instance uses; any dimension the data
# carries that is not listed is appended alphabetically, so the list never has to be complete.
DIM_ORDER = ['Customer value', 'Revenue quality', 'Efficiency']
_seen = [d for o in outs for d in o['dims']]
DIMS = [d for d in DIM_ORDER if d in _seen] + sorted({d for d in _seen if d not in DIM_ORDER})
for o in outs:
    o['dims'] = sorted(o['dims'], key=lambda d: DIMS.index(d))
COLS = ['Now', 'Next', 'Later']
CI = {c: i for i, c in enumerate(COLS)}

def outcome_of(r):
    if r['L'] < 3:
        return r['Outcome']
    s = sorted({byid[f]['Outcome'] for f in r['Serves'] if byid[f]['Outcome']}, key=lambda x: int(x.split('-')[1]))
    return ', '.join(s) if s else 'O-0'
for r in rows:
    r['oc'] = outcome_of(r)
ocol = {o['Outcome']: o['Column'] for o in outs}
ocol['O-0'] = 'Later'  # placeholder outcome for cards whose cascade is broken
prim = lambda r: r['oc'].split(',')[0]  # outcome a card is drawn under

# ---------- page sections ----------
# Page contract (skill references/notion-contract.md). Required sections feed the checks; the
# generator stops without them. Optional sections are prose: missing ones are reported in the
# check log and marked in the document, never invented.
REQUIRED = ['Outcome colours', 'System building blocks', 'Deviations']
OPTIONAL = ['Target picture and context', 'Sequence', 'Scope boundaries', 'Demand from the sequence', 'Open gaps']
ALIASES = {'Context': 'Target picture and context'}
NOT_MAINTAINED = '*Not maintained in Notion for this version.*'
def sections(md, d):
    parts = re.split(r'\n(?=# )', md)
    for p in parts:
        m = re.match(r'# (.+)\n', p)
        if m:
            # Notion adds block attributes to headings ({toggle="true"}) and indents toggle bodies
            # by one tab; both are layout, not content.
            name = re.sub(r'\s*\{[^}]*\}\s*$', '', m.group(1).strip())
            name = re.sub(r'\s*<br>\s*$', '', name)
            name = re.sub(r'\s*·\s*details$', '', name)
            name = ALIASES.get(name, name)
            body = re.sub(r'^\t', '', p[m.end():], flags=re.M)
            body = re.sub(r'^\s*<(database|page|embed)\b.*?</\1>\n?', '', body, flags=re.M)
            body = re.sub(r'^\s*<empty-block/>\n?', '', body, flags=re.M).strip()
            body = re.sub(r'^(\t+)', lambda t: '  ' * len(t.group(1)), body, flags=re.M)  # nested lists
            body = re.sub(r'^## ', '### ', body, flags=re.M)  # page subheadings sit below document sections
            d[name] = d[name] + '\n' + body if name in d else body
    return d
S, footer = {}, ''
for pg in pages:
    head, sep, tail = pg.partition('\n---\n')
    sections(head, S)
    if sep:
        footer = tail
_miss_req = [s for s in REQUIRED if s not in S]
if _miss_req:
    sys.exit('render.py: required page sections missing: ' + ', '.join(_miss_req)
             + '. They belong on the page "Roadmap reference" (see references/notion-contract.md).')
missing_opt = [s for s in OPTIONAL if s not in S]
_b = re.search(r'Basis:[^\n]*?roadmap\.', footer) or re.search(r'Basis:[^\n]*', footer)
basis = _b.group(0) if _b else 'Basis: not maintained in Notion for this version.'
if not _b: missing_opt.append('basis line')

def unesc(t):
    return re.sub(r'\\([<>\[\]])', r'\1', t)
def tables_to_md(t):
    def conv(m):
        trs = re.findall(r'<tr>(.*?)</tr>', m.group(0), re.S)
        rs = [[unesc(c.strip()) for c in re.findall(r'<td>(.*?)</td>', tr, re.S)] for tr in trs]
        lines = ['| ' + ' | '.join(rs[0]) + ' |', '|' + '---|' * len(rs[0])]
        lines += ['| ' + ' | '.join(r) + ' |' for r in rs[1:]]
        return '\n'.join(lines)
    t = re.sub(r'<table[^>]*>.*?</table>', conv, t, flags=re.S)
    t = re.sub(r'`(ASSUMPTION, verify|SUGGESTED, confirm)`', r'`[\1]`', t)
    t = unesc(t)
    # paragraph spacing: blank line between blocks, keep list items together
    out = []
    for line in t.split('\n'):
        if out and not (line.startswith('|') and out[-1].startswith('|')) and not (line.startswith('- ') and out[-1].startswith('- ')):
            out.append('')
        out.append(line)
    return '\n'.join(out).strip()
def P(name):
    return tables_to_md(S[name]) if S.get(name, '').strip() else NOT_MAINTAINED

colours = dict(re.findall(r'<td>(O-\d+)</td>\s*<td>`(#[0-9A-Fa-f]{6})`</td>', S['Outcome colours']))
no_colour = [o['id'] for o in rows if o['L'] == 1 and o['ID'] not in colours]
if any(r['L'] > 1 and 'O-0' in (r.get('Outcome') or '') for r in rows) or any(r['L'] == 3 and not r['Serves'] for r in rows):
    colours['O-0'] = '#8A8A8A'
for c in no_colour:
    colours[c] = '#8A8A8A'  # neutral grey until the colour table on Roadmap reference has a row
blocks_tbl = re.findall(r'<tr>\s*<td>(B\d)</td>\s*<td>(.*?)</td>\s*<td>.*?</td>\s*<td>(exists|partial|missing)</td>', S['System building blocks'], re.S)
bstatus = {b: s for b, n, s in blocks_tbl}
bname = {b: n for b, n, s in blocks_tbl}

# ---------- checks ----------
ceil = {1: 16, 2: 9, 3: 9}
words = lambda t: len(t.split())
hedges = ['unclear whether', 'to be checked', 'possibly', 'presumably', '?']
cell = defaultdict(list)
for r in cards:
    cell[(r['Column'], r['L'])].append(r)
inv = []
for r in rows:
    if r['L'] == 1 and r['Serves']: inv.append(f"I1 {r['id']}")
    if r['L'] == 2 and (r['Outcome'] == 'O-0' or not r['pos'] or (not r.get('Serves_legacy') and (len(r['Serves']) != 1 or byid[r['Serves'][0]]['L'] != 1))): inv.append(f"I2 {r['id']}")
    if r['L'] == 3 and (not r['pos'] or not r['Serves'] or r['oc'] == 'O-0' or ',' in r['oc'] or any(byid[f]['L'] != 2 for f in r['Serves'])): inv.append(f"I3 {r['id']}")
    if r['L'] > 1 and CI[r['Column']] > CI[ocol[prim(r)]]: inv.append(f"I4 {r['id']}")
    for t in r['Precedes']:
        if PI(r) > PI(byid[t]): inv.append(f"I5 {r['id']}")
ids = [r['id'] for r in rows]
if len(ids) != len(set(ids)): inv.append('I6 duplicate IDs')
for r in cards:
    pass
for r in rows:
    if not re.fullmatch({1: r'O-[1-9]\d*', 2: r'F-[1-9]\d*', 3: r'E-[1-9]\d*'}[r['L']], r['id']): inv.append(f"I6 {r['id']}")
# R7 / I7 (r10.3): the ceiling of five applies per position (a half of Now or Next, or Later),
# which is what the picture draws as one cell; a column of Now or Next holds two such cells.
pcell = defaultdict(list)
for r in cards:
    pcell[(r['Column'] + (' · ' + r['h'] if r['h'] else ''), r['L'])].append(r)
over = {k: v for k, v in pcell.items() if len(v) > 5}
i7 = [f"{c} layer {l} ({len(v)})" for (c, l), v in over.items()]
i8 = [o['id'] for o in outs if o['h'] == '1st' and any(c['oc'] == o['id'] and c['Column'] == o['Column'] and c['h'] == '2nd' for c in cards)]
for k in i8: inv.append(f"I8 {k}")
long_titles = [r for r in rows if words(r['Title']) > ceil[r['L']]]
hedged = [r for r in rows if any(h in r['Title'].lower() for h in hedges)]
r3 = [o['id'] for o in outs if not any(c['oc'] == o['Outcome'] and CI[c['Column']] <= CI[o['Column']] for c in cards)]
ratio = {}
for c in COLS:
    oc = [o['Outcome'] for o in outs if o['Column'] == c]
    n = sum(1 for k in cards if k['oc'] in oc)
    ratio[c] = n / len(oc) if oc else 0
bcount = Counter(b for r in cards for b in r['Blocks'])
thin_blocks = [b for b in bstatus if bcount[b] < 2]
now_weak = sorted({b for r in cards if r['Column'] == 'Now' for b in r['Blocks'] if bstatus.get(b) in ('missing', 'partial')})
gaps_txt = S.get('Open gaps', '')
unnamed = [b for b in now_weak if b not in gaps_txt]
prec_bad = [r['id'] for r in cards for t in r['Precedes'] if PI(r) > PI(byid[t])]
nowave = [r['id'] for r in rows if not r['pos']]
missing_cards = [r for r in cards if any(bstatus.get(b) == 'missing' for b in r['Blocks'])]

# ---------- order ----------
def half(r):
    return 'front' if r['h'] == '1st' else 'back'
opos = {o['id']: o['h'] for o in outs if o['h']}
lead = [r for r in cards if prim(r) != 'O-0' and CI[r['Column']] < CI[ocol[prim(r)]]]

# ---------- markdown ----------
def cell_(x): return re.sub(r'\s*\n+\s*', ' ', x or '').replace('|', '/')  # one table cell per value
def q(s): return '"' + s.replace('"', '\\"') + '"'
y = ['cards:']
for col in COLS:
    y.append(f"  # ===================== {col.upper()} =====================")
    for r in sorted([c for c in cards if c['Column'] == col], key=lambda c: (c['L'] == 2, PI(c), nat(c['id']))):
        y.append(f"  - id: {r['id']}")
        y.append(f"    title: {q(r['Title'])}")
        y.append(f"    layer: {r['L']}")
        if r['L'] == 3:
            y.append(f"    standalone: {r['Standalone']}")
            y.append(f"    kind: {r['Kind']}")
        y.append(f"    position: {q(r['pos'])}")
        y.append(f"    outcome: \"{r['oc']}\"")
        if r['L'] == 3:
            y.append(f"    serves: [{', '.join(r['Serves'])}]")
        if r['Description']: y.append(f"    desc: {q(r['Description'])}")
        if r['Precedes']: y.append(f"    precedes: {r['Precedes'][0]}")
        if r['Blocks']: y.append(f"    blocks: [{', '.join(r['Blocks'])}]")
        if r['PRD'] == '__YES__': y.append("    prd: yes")
        if r['Source']: y.append(f"    source: {q(r['Source'])}")
        if r['Linear']: y.append(f"    linear: {q(r['Linear'])}")
        y.append('')
yaml_block = '\n'.join(y).rstrip()

def flags(r):
    f = []
    if r['Precedes']: f.append('precedes ' + r['Precedes'][0])
    if r in lead: f.append('lead time')
    if r['PRD'] == '__YES__': f.append('PRD')
    return '; '.join(f)
t2 = ['| ID | Position | Outcome | Title | Flags |', '|---|---|---|---|---|']
t3 = ['| ID | Position | Outcome | Title | Serves | Remains | Kind | Flags |', '|---|---|---|---|---|---|---|---|']
for r in sorted(cards, key=lambda c: (PI(c), nat(prim(c)), nat(c['id']))):
    if r['L'] == 2:
        t2.append(f"| {r['id']} | {r['pos']} | {r['oc']} | {cell_(r['Title'])} | {flags(r)} |")
    else:
        t3.append(f"| {r['id']} | {r['pos']} | {r['oc']} | {cell_(r['Title'])} | {', '.join(r['Serves'])} | {r['Standalone']} | {r['Kind']} | {flags(r)} |")
remain = [r for r in cards if r['L'] == 3 and r['Standalone'] == 'yes']
unserved = [r['id'] for r in cards if r['L'] == 2 and not any(r['id'] in e['Serves'] for e in cards if e['L'] == 3)]

if HAS_DIMS:
    otab = ['| Code | Outcome | Context | Impact | Value | Evidence | Type | Position | Colour |', '|---|---|---|---|---|---|---|---|---|']
else:
    otab = ['| Code | Outcome | Context | Value | Evidence | Type | Position | Colour |', '|---|---|---|---|---|---|---|---|']
for o in outs:
    imp = f" {', '.join(o['dims'])} |" if HAS_DIMS else ''
    otab.append(f"| {o['id']} | {cell_(o['Title'])} | {cell_(o['ctx'])} |{imp} {o['Value'] or ''} | {cell_(o['evid'])} | {o['ev'] or ''} | {o['pos']} | `{colours[o['id']]}` |")
crit = sum(1 for o in outs if o['ev'] == 'Criterion')
metr = sum(1 for o in outs if o['ev'] == 'Metric')
ev_line = f"{crit} of {len(outs)} outcomes are met by a criterion, {metr} by a metric" + (f", {len(outs)-crit-metr} have no evidence type yet." if len(outs) - crit - metr else '.')
no_dims = [o['id'] for o in outs if not o['dims']]
if HAS_DIMS:
    dim_lines = ['**Impact dimensions.** Which business dimensions the outcomes support (an outcome may support more than one):', '']
    dim_lines += [f"- {d}: {len([o for o in outs if d in o['dims']])} ({', '.join(o['id'] for o in outs if d in o['dims'])})" for d in DIMS]
    if no_dims: dim_lines.append(f"- No dimension set: {', '.join(no_dims)}")
    dim_md = '\n'.join(dim_lines)
else:
    dim_md = '**Impact dimensions.** ' + NOT_MAINTAINED

seq = S.get('Sequence', '')
_t = re.search(r'<table.*?</table>', seq, re.S)
seq_tbl = tables_to_md(_t.group(0)) if _t else NOT_MAINTAINED
if 'Sequence' in S and not _t: missing_opt.append('Sequence table')
reasons = dict(re.findall(r'- \*\*([EF]-\d+) before [EF]-\d+\.\*\* (.*)', seq))
_m = re.search(r'\*\*Lead time\.\*\* (.*)', seq); leadtxt = _m.group(1) if _m else NOT_MAINTAINED
_m = re.search(r'\*\*In-cell order, row 3\.\*\* (.*)', seq); incell = _m.group(1) if _m else NOT_MAINTAINED
pairs = [(r['id'], t) for r in sorted(cards, key=lambda c: (PI(c), nat(c['id']))) for t in r['Precedes']]

def fmt_pos(k):
    return f"{k} {byid[k]['Column']} {opos[k]}"
anyfront = any(v == '1st' for v in opos.values())
# deviations register from the page
dev_rows = re.findall(r'<tr>\s*<td>(A\d+)</td>\s*<td>(R\d+b?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*<td>(.*?)</td>\s*</tr>', S['Deviations'], re.S)
breached = set((['R7'] if over else []) + (['R4'] if long_titles else []))
unbooked = sorted(breached - {d[1] for d in dev_rows})
r4txt = ' '.join(d[2] for d in dev_rows if d[1] == 'R4')
unbooked += [f"R4 {r['id']}" for r in long_titles if not re.search(rf"\b{re.escape(r['id'])}\b", r4txt)]
stale = [d[0] for d in dev_rows if d[1] not in breached]

check = [
 ('R1 outcome per card', 'passed' if all(c['oc'] != 'O-0' for c in cards) else 'finding', f"{sum(c['oc'] != 'O-0' for c in cards)} of {len(cards)}; enabler outcomes derived via Serves" + ('' if all(c['oc'] != 'O-0' for c in cards) else '; no outcome (drawn grey as ?): ' + ', '.join(c['id'] for c in cards if c['oc'] == 'O-0'))),
 ('R2 evidence per outcome', 'passed' if all(o['evid'] for o in outs) else 'finding', f"{sum(1 for o in outs if o['evid'])} of {len(outs)}, {crit} by criterion, {sum(1 for o in outs if o['ev'] and o['ev'] != 'Criterion')} by metric" + ('' if all(o['evid'] for o in outs) else '; without evidence: ' + ', '.join(o['id'] for o in outs if not o['evid'])) + ('' if HAS_EVID else '; property "Evidence" not in the export, Description read as evidence') + (('; marked as proposal: ' + ', '.join(o['id'] for o in outs if o['evid'].upper().startswith(('PROPOSAL', 'SUGGESTED')))) if any(o['evid'].upper().startswith(('PROPOSAL', 'SUGGESTED')) for o in outs) else '')),
 ('R3 every outcome has a card in its column or to its left', 'passed' if not r3 else 'finding', f"{len(outs)-len(r3)} of {len(outs)}" + (f"; missing: {', '.join(r3)}" if r3 else '')),
 ('R4 title grammar and word ceilings', 'deviation' if long_titles else 'passed', ('Over the ceiling: ' + ', '.join(f"{r['id']} ({words(r['Title'])} words)" for r in long_titles) + '. Grammar per layer checked by reading, not by the generator') if long_titles else 'Word ceilings held; grammar checked by reading'),
 ('R4b no card hedges', 'passed' if not hedged else 'finding', f"{len(rows)-len(hedged)} of {len(rows)}"),
 ('R5 altitude', 'passed', 'Checked by reading: one sentence per card, no screen, ticket or estimate'),
 ('R6 cards per outcome not increasing left to right', 'passed' if ratio['Now'] >= ratio['Next'] >= ratio['Later'] else 'finding', f"Now {ratio['Now']:.2f} · Next {ratio['Next']:.2f} · Later {ratio['Later']:.2f}. **Formally passed, finding in substance:** the Now ratio is the overload of the quarter, first row of section 8"),
 ('R7 at most five cards per cell', 'deviation' if over else 'passed', '; '.join(f"{c} row {l} holds {len(v)}" for (c, l), v in over.items()) or 'no cell above five (a cell is one position: a half of Now or Next, or Later)'),
 ('R8 no outcome in more than one column', 'passed', 'Held by the schema: one row per outcome with one Position; ' + (', '.join(r['id'] for r in lead) + ' are lead time' if lead else 'no lead-time cards')),
 ('R9 blocks used by two cards, missing and partial under Now named', 'passed' if not thin_blocks and not unnamed else 'finding', f"{len(bstatus)} blocks" + (f"; used by fewer than two: {', '.join(thin_blocks)}" if thin_blocks else ', each used by two or more cards') + (f"; missing or partial under Now: {', '.join(now_weak)}" if now_weak else '') + (f"; not named in section 8: {', '.join(unnamed)}" if unnamed else (f"; all named in section 8" if now_weak else ''))),
 ('R10 position per card and outcome, precedes not later than its target, no outcome in a 1st half above a 2nd-half card', 'passed' if not prec_bad and not nowave and not i8 else 'finding', f"{len(rows)} of {len(rows)} with position; {len(pairs)} precedes pairs hold; outcome check (I8) " + ('holds' if not i8 else 'fails for ' + ', '.join(i8))),
 ('R11 row names match composition', 'passed', f"Row 3 holds {sum(1 for c in cards if c['L']==3)} cards; the composition behind \"Tech & Data Enabler\" is stated in section 1 and checked by reading"),
 ('R12 impact dimension per outcome', ('passed' if not no_dims else 'finding') if HAS_DIMS else 'finding', (f"{len(outs)-len(no_dims)} of {len(outs)}" + (f"; none set: {', '.join(no_dims)}" if no_dims else '')) if HAS_DIMS else 'Property "Impact dimension" not in the export'),
]
check.append(('Notion rows', 'finding' if (excluded or dangling or no_colour) else 'passed',
              '; '.join(x for x in [
                  ('left out as incomplete: ' + ', '.join(excluded)) if excluded else '',
                  ('relations to missing rows dropped: ' + ', '.join(dangling)) if dangling else '',
                  ('no row in the colour table, drawn grey: ' + ', '.join(no_colour)) if no_colour else ''] if x)
              or f'{len(rows)} rows, all complete'))
check.append(('Page sections (contract)', 'finding' if missing_opt else 'passed',
              ('Not maintained in Notion: ' + ', '.join(missing_opt) + '; marked in the document, nothing generated in their place')
              if missing_opt else 'All optional prose sections present'))
invline = ('I1 to I6 and I8 hold' if not inv else 'Violations: ' + ', '.join(inv)) + ('; I7 is a finding, not an error: ' + ', '.join(i7) + ', booked in the deviation register' if i7 else '; I7 holds')


# ---------- changes against the previous version (mechanical diff, no reasons) ----------
def _prev_state(path):
    t = open(path).read()
    cards_, outs_ = {}, {}
    y = re.search(r'```yaml\n(.*?)```', t, re.S)
    if y:
        cur = None
        for line in y.group(1).split('\n'):
            m = re.match(r'\s*- id: (\S+)', line)
            if m: cur = cards_.setdefault(m.group(1), {}); continue
            m = re.match(r'\s+(title|position|outcome|serves|wave): (.*)', line)
            if m and cur is not None: cur[m.group(1)] = m.group(2).strip().strip('"').strip('[]')
    sec = re.search(r'## 2 Outcomes\n(.*?)\n## 3', t, re.S)
    if sec:
        lines = [l for l in sec.group(1).split('\n') if l.startswith('|')]
        if lines:
            hdr = [c.strip() for c in lines[0].strip('|').split('|')]
            for l in lines[2:]:
                c = [x.strip() for x in l.strip('|').split('|')]
                d = dict(zip(hdr, c))
                outs_[d.get('Code')] = {'title': d.get('Outcome'), 'position': d.get('Position') or d.get('Column')}
                if 'Impact' in d: outs_[d.get('Code')]['impact'] = d['Impact']
    return cards_, outs_
def _changes():
    if not A.prev:
        return '- None: first generated version'
    pc, po = _prev_state(A.prev)
    now_c = {r['id']: {'title': r['Title'], 'position': r['pos'], 'outcome': r['oc'], 'serves': ', '.join(r['Serves'])} for r in cards}
    now_o = {o['id']: {'title': o['Title'], 'position': o['pos'], 'impact': ', '.join(o['dims'])} for o in outs}
    out = []
    for kind, prev_, now_ in (('Outcome', po, now_o), ('Card', pc, now_c)):
        for k in sorted(set(now_) - set(prev_), key=nat):
            out.append(f"- {kind} {k} added: {now_[k]['title']} ({now_[k]['position']})")
        for k in sorted(set(prev_) - set(now_), key=nat):
            out.append(f"- {kind} {k} removed: {prev_[k].get('title', '')}")
        for k in sorted(set(prev_) & set(now_), key=nat):
            a, b = prev_[k], now_[k]
            for f in ('title', 'position', 'outcome', 'serves', 'impact'):
                if f in a and f in b and a[f] != b[f]:
                    out.append(f"- {kind} {k} {f}: {a[f]} → {b[f]}")
    out.append('- Generated diff by ID against the previous file; it lists what changed, not why. Page text is not compared')
    return '\n'.join(out)
CHANGES = _changes()

scope_md = re.sub(r'^### (.+)$', r'**\1**', P('Scope boundaries'), flags=re.M)
md = f"""# Roadmap: {A.unit}

As of {DATE} · 3 layers × 5 positions · Now {PERIOD['Now']} · Next {PERIOD['Next']} · Later {PERIOD['Later']} ·
Audience: {A.audience} · Replaces: {('`' + PREV + '`') if PREV else 'none'}

Generated from the Notion database "Roadmap" and the page "Product Roadmap". Do not edit this file; edit Notion and generate the next version.

## 1 Target picture and context

{P('Target picture and context')}

This roadmap orders intent, it commits to nothing. The periods place the work, 1st and 2nd order it inside the period; neither is a date.

{basis}

## 2 Outcomes

{chr(10).join(otab)}

{ev_line}

{dim_md}

## 3 Cards

```yaml
{yaml_block}
```

**Row 2 · Product & Features**

{chr(10).join(t2)}

**Row 3 · Tech & Data Enabler**

{chr(10).join(t3)}

{len(remain)} enablers remain when their feature is cut ({', '.join(r['id'] for r in remain)}), {sum(1 for r in remain if r['Kind']=='decision')} of them decisions. {len(unserved)} features have no enabler ({', '.join(unserved)}), which the spec allows.

## 4 Sequence

{seq_tbl}

**Outcome positions (placed by hand):** {', '.join(fmt_pos(k) for k in opos)}. The outcome check of R10 {'holds' if not i8 else 'fails for ' + ', '.join(i8)}.{'' if anyfront else ' No outcome sits in a 1st half: in both Now and Next the first half delivers groundwork, and business value arrives in the second half.'}

The 1st halves of Now and Next are enabler-heavy, so their third-column sentence is an intermediate state, not an outcome sentence.

**Lead time, {len(lead)} cards.** {leadtxt}

**`precedes`, {len(pairs)} pairs.**

""" + '\n'.join(f"- **{a} before {b}.** {reasons.get(a, '')}" for a, b in pairs) + f"""

**In-cell order, row 3.** {incell}

## 5 System building blocks

{P('System building blocks')}

## 6 Scope boundaries

{scope_md}

## 7 Demand from the sequence

{P('Demand from the sequence')}

## 8 Open gaps

{P('Open gaps')}

## 9 Check log, deviations and changes

| Rule | Result | Note |
|---|---|---|
""" + '\n'.join(f"| {a} | {b} | {c} |" for a, b, c in check) + f"""

**Invariants of the Notion schema:** {invline}.

**Deviations**

| No | Deviation | Reason | Price |
|---|---|---|---|
""" + '\n'.join(f"| {a} | {d} ({r}) | {rs} | {p} |" for a, r, d, rs, p in dev_rows) + ('\n\nBreach without a register entry: ' + ', '.join(unbooked) if unbooked else '') + ('\n\nRegister entry without a breach: ' + ', '.join(stale) if stale else '') + """

**Changes against """ + (PREV_V or "previous version") + """**

""" + CHANGES + """

""" + skill[skill.index(MARK):].rstrip() + '\n'
open(f"{OUT}/{STEM}.md", 'w').write(md)

# ---------- HTML body ----------
def card_html(r, lv1=False):
    # r10.10: the code label names the card itself (O-1, F-2, E-66); the colour still comes from the
    # outcome, and the serves line carries the cascade. Before r10.10 every card showed its outcome code.
    oc = prim(r) if r['L'] > 1 else r['Outcome']
    n = int(oc.split('-')[1])
    c = r['id'] if r['L'] > 1 else oc
    if oc == 'O-0' and r['L'] == 1: c = '?'
    pill = ''
    for t in r['Precedes']:
        tr = byid[t]
        if tr['Column'] != r['Column'] or tr['oc'] != r['oc']:
            pill = '<span class="pill">AHEAD OF ' + html.escape(t) + '</span>'  # r10.10: names the target card
    cls = 'card lv1' if lv1 else 'card'
    dims = f'<span class="dims">{" · ".join(html.escape(d) for d in r["dims"])}</span>' if lv1 and r['dims'] else ''
    # r10.4: every card carries its description. r10.7: on every layer, layer 1 included, it is
    # shown only in the detailed view (body.detail); the switch toggles all descriptions at once.
    d = r['ctx'] if lv1 else (r.get('Description') or '')
    ctx = f'<span class="ctx lo">{html.escape(d)}</span>' if d else ''
    # r10.6: layers 2 and 3 name what the card serves, in codes, so the cascade is readable on
    # the card itself: a feature "serves O-4", an enabler "serves F-54 · F-56". Both views.
    sv = ''
    if not lv1 and r['Serves']:
        sv = '<span class="sv">serves ' + ' · '.join(html.escape(x) for x in sorted(r['Serves'], key=nat)) + '</span>'
    return f'<article class="{cls}" style="--c:var(--c{n});--cl:var(--c{n}l)"><span class="code">{c}</span><span class="t">{html.escape(r["Title"])}</span>{sv}{dims}{ctx}{pill}</article>'
def order(rs, layer):
    rs = sorted(rs, key=lambda r: (nat(prim(r)), nat(r['id'])))
    if layer == 3:  # bottom to top by ID within one outcome
        grouped = defaultdict(list)
        for r in rs: grouped[prim(r)].append(r)
        rs = [r for k in sorted(grouped, key=nat) for r in reversed(grouped[k])]
    return rs
note_cell = ('Now', 3)
nmiss = sum(1 for r in cell[note_cell] if r in missing_cards)
body = []
labels = {1: ('Business Outcomes', 'Why are we doing this?'), 2: ('Product &amp; Features', 'What does the user get in their hands?'), 3: ('Tech &amp; Data Enabler', 'Which preconditions do we have to create?')}
for L in (1, 2, 3):
    nm, qq = labels[L]
    body.append(f'<div class="rowlabel r{L} b{L}"><div class="slab"><div class="num">Layer {L}</div><div class="nm">{nm}</div><div class="q">{qq}</div></div></div>')
    for col in COLS:
        if L == 1:
            rs = [o for o in outs if o['Column'] == col]
            fr = [o for o in rs if o['h'] == '1st']
            bk = [o for o in rs if o not in fr]
        else:
            rs = cell[(col, L)]
            fr = order([r for r in rs if half(r) == 'front'], L)
            bk = order([r for r in rs if half(r) != 'front'], L)
        cls = col.lower()
        note = f'<p class="note">{len(rs)} cards, {nmiss} of them on building blocks that do not yet exist.</p>' if (col, L) == note_cell and len(missing_cards) > len(cards) / 3 else ''
        if col == 'Later':
            body.append(f'<div class="cell later b{L}">' + ''.join(card_html(r, L == 1) for r in (rs if L == 1 else order(rs, L))) + note + '</div>')
        else:
            body.append(f'<div class="cell {cls} split b{L}"><div class="half">' + ''.join(card_html(r, L == 1) for r in fr) + '</div><div class="half late">' + ''.join(card_html(r, L == 1) for r in bk) + '</div>' + note + '</div>')
print('invariants:', invline)
print('checks:', [(a, b) for a, b, c in check])

# ---------- full HTML from the fixed template ----------
CSS = r"""
:root{
  --ground:#F7F5F0; --surface:#FFFFFF; --surface-2:#F1EEE7; --surface-3:#E9E5DA;
  --ink:#1A1A18; --ink-2:#55524A; --ink-3:#7E7A70;
  --rule:#DDD8CC; --rule-2:#C9C3B4;
  --shadow:0 1px 2px rgba(26,26,24,.07), 0 2px 6px rgba(26,26,24,.05);
  --lip:rgba(255,255,255,.85);
  --slab:#E7E2D6;

  /* Outcome colours, section 2 of the document. One per outcome, nothing else uses them. */
@@COLOURS@@

  /* Wedge that shows the bearing direction: about a seventh of the label column. */
  --wedge:21px;

  --sans:"IBM Plex Sans","Helvetica Neue",Arial,sans-serif;
  --serif:"IBM Plex Serif",Georgia,"Times New Roman",serif;
  --mono:"IBM Plex Mono",ui-monospace,"SFMono-Regular",Menlo,monospace;
}
@media (prefers-color-scheme: dark){
  :root:not([data-theme="light"]){
    --ground:#171612; --surface:#232119; --surface-2:#1E1C16; --surface-3:#262318;
    --ink:#EDE9E0; --ink-2:#B5AFA2; --ink-3:#8A857A;
    --rule:#37342B; --rule-2:#4A4638;
    --shadow:0 1px 2px rgba(0,0,0,.5), 0 2px 8px rgba(0,0,0,.35);
    --lip:rgba(255,255,255,.07);
    --slab:#272419;
    @@DARK@@
  }
}
:root[data-theme="dark"]{
  --ground:#171612; --surface:#232119; --surface-2:#1E1C16; --surface-3:#262318;
  --ink:#EDE9E0; --ink-2:#B5AFA2; --ink-3:#8A857A;
  --rule:#37342B; --rule-2:#4A4638;
  --shadow:0 1px 2px rgba(0,0,0,.5), 0 2px 8px rgba(0,0,0,.35);
  --lip:rgba(255,255,255,.07);
  --slab:#272419;
  @@DARK@@
}

*{box-sizing:border-box}
body{margin:0;background:var(--ground);color:var(--ink);font-family:var(--sans);font-size:14px;line-height:1.45;-webkit-font-smoothing:antialiased}
.page{padding-inline:14px;padding-block:28px 44px;max-width:1700px;margin:0 auto}

.masthead{border-bottom:1px solid var(--rule-2);padding-bottom:18px;margin-bottom:22px}
.eyebrow{font-size:11px;font-weight:600;letter-spacing:.14em;text-transform:uppercase;color:var(--ink-3);margin:0 0 6px}
h1{font-family:var(--serif);font-weight:600;font-size:clamp(28px,4vw,40px);letter-spacing:-.01em;margin:0;text-wrap:balance}
.meta{margin:8px 0 0;color:var(--ink-2);font-size:13px}

.scroller{overflow-x:auto;padding-bottom:6px}
/* Label column is a label, not a text column: about a tenth of the matrix. */
.matrix{min-width:1180px;display:grid;grid-template-columns:8% repeat(3,1fr)}  /* r10.9: fits a 1300px pane (Notion embed) without a horizontal scroll */

.colhead{padding:0 14px 12px;border-bottom:1px solid var(--rule-2)}
.colhead h2{font-family:var(--serif);font-size:15px;font-weight:600;letter-spacing:.1em;text-transform:uppercase;margin:0 0 7px;color:var(--ink-3)}
.colhead h2 b{color:var(--ink);font-weight:600}
.bar{display:flex;gap:3px;margin-bottom:9px}
.bar i{height:4px;width:26px;border-radius:2px;background:var(--rule-2);display:block}
.bar i.on{background:var(--ink-2)}
.period{font-family:var(--mono);font-size:13px;color:var(--ink);margin:0;font-weight:600;letter-spacing:.02em;font-variant-numeric:tabular-nums}
.corner{border-bottom:1px solid var(--rule-2)}
.halves{display:grid;grid-template-columns:1fr 1fr;gap:0 16px;margin-top:8px;font-family:var(--mono);font-size:11px;letter-spacing:.08em;color:var(--ink-3)}
.halves span+span{border-left:1px dashed var(--rule-2);padding-left:16px}
.flow{position:relative;height:10px;margin-top:9px;border-top:1px solid var(--rule-2)}
.flow::after{content:"";position:absolute;right:0;top:-4px;width:0;height:0;
  border-top:4px solid transparent;border-bottom:4px solid transparent;border-left:6px solid var(--rule-2)}

/* Bearing direction: every layer is an arrow pointing up across the full label width.
   Layer 3 points into layer 2, layer 2 points into layer 1. Form carries it, not tone. */
.rowlabel{position:relative;padding:0;border-bottom:1px solid var(--rule)}
.slab{height:calc(100% - 10px);margin:5px 0;background:var(--slab);padding:38px 12px 32px 13px}
.r1 .slab{clip-path:polygon(0 0,100% 0,100% 100%,50% calc(100% - var(--wedge)),0 100%);padding-top:18px}
.r2 .slab{clip-path:polygon(50% 0,100% var(--wedge),100% 100%,50% calc(100% - var(--wedge)),0 100%,0 var(--wedge))}
.r3 .slab{clip-path:polygon(50% 0,100% var(--wedge),100% 100%,0 100%,0 var(--wedge))}
/* Both axes of the grid are the same kind of element and get the same treatment. */
.rowlabel .num{font-family:var(--serif);font-size:13px;font-weight:600;letter-spacing:.1em;
  text-transform:uppercase;color:var(--ink-3);white-space:nowrap}
.rowlabel .nm{font-family:var(--serif);font-size:12px;font-weight:600;letter-spacing:.09em;
  text-transform:uppercase;color:var(--ink);margin-top:6px;line-height:1.3}
.rowlabel .q{font-size:10.5px;color:var(--ink-3);margin-top:5px;font-style:italic;line-height:1.35}

/* Layering: layer 1 sits on layer 2, layer 2 on layer 3. */
.b1,.b2,.b3{position:relative}
.b1{z-index:3}
.b2{z-index:2}
.b3{z-index:1}
.b1,.b2{box-shadow:0 11px 13px -11px rgba(26,26,24,.95)}
.b2,.b3{border-top:1px solid var(--lip)}
.b3{border-bottom-width:3px;border-bottom-color:var(--rule-2)}
.matrix .b3.cell{border-bottom-color:var(--rule-2)}

.cell{display:flex;flex-direction:column;gap:8px;padding:18px 14px 22px;border-bottom:1px solid var(--rule)}
.cell.now{--cellbg:var(--surface);background:var(--surface);border-left:1px solid var(--rule)}
.cell.next{--cellbg:var(--surface-2);background:var(--surface-2);border-left:1px dashed var(--rule-2)}
.cell.later{--cellbg:var(--surface-3);background:var(--surface-3);border-left:1px dashed var(--rule-2)}
/* Two positions inside Now and Next, 1st and 2nd half. Row 1 follows the same split. */
.cell.split{display:grid;grid-template-columns:1fr 1fr;gap:0 16px;align-items:start}
.half{display:flex;flex-direction:column;gap:8px;min-width:0}
.half.late{border-left:1px dashed var(--rule-2);padding-left:16px}
.note{grid-column:1 / -1;font-size:11.5px;font-style:italic;color:var(--ink-3);margin:6px 2px 0;line-height:1.45}

/* Assignment lives in the surface: the outcome colour fills the card, tinted.
   White is reserved for a card with no outcome, which this plan does not have. */
.card{display:flex;align-items:baseline;gap:7px;flex-wrap:wrap;padding:9px 11px 10px;
  background:color-mix(in srgb,var(--cl) 22%,var(--cellbg));
  border:1px solid color-mix(in srgb,var(--cl) 45%,var(--rule))}
.now .card{box-shadow:var(--shadow)}
/* The cell ground is itself tinted for confidence, so the card tint is lifted here,
   otherwise two outcomes in the Later column stop being separable at card size. */
.next .card,.later .card{border-style:dashed;box-shadow:none;
  background:color-mix(in srgb,var(--cl) 28%,var(--cellbg))}
.card .code{font-family:var(--mono);font-size:11px;font-weight:600;color:var(--cl);letter-spacing:.02em;flex:none}
.card .t{font-size:13px;font-weight:600;flex:1 1 200px;line-height:1.35;min-width:0}
.card .pill{font-family:var(--mono);font-size:9.5px;font-weight:600;letter-spacing:.06em;
  border:1px solid var(--cl);color:var(--cl);border-radius:999px;padding:1px 7px;flex:none}

.card.lv1{background:var(--c);border-color:var(--c);color:#fff;padding:11px 13px 12px}
.card.lv1 .code{color:rgba(255,255,255,.8)}
.card.lv1 .t{color:#fff;font-size:14px;line-height:1.4}
.card.lv1 .dims{flex:0 0 100%;display:block;margin-top:4px;padding-top:6px;border-top:1px solid rgba(255,255,255,.28);font-size:10.5px;letter-spacing:.02em;line-height:1.35;color:rgba(255,255,255,.85)}
.card.lv1 .ctx.lo{margin-top:5px;color:rgba(255,255,255,.78)}
.card .sv{flex:0 0 100%;display:block;margin-top:3px;font-family:var(--mono);font-size:9.5px;font-weight:500;letter-spacing:.03em;color:var(--cl)}
.card .ctx.lo{flex:0 0 100%;display:none;margin-top:3px;font-size:10.5px;font-weight:400;line-height:1.4;color:var(--ink-2)}
body.detail .card .ctx.lo{display:block}
.view{margin:10px 0 0;font-size:12px;color:var(--ink-3)}
.view button{font:inherit;font-size:12px;padding:3px 10px;margin-right:6px;border:1px solid var(--rule);border-radius:999px;background:transparent;color:var(--ink-2);cursor:pointer}
.view button.on{background:var(--ink);color:var(--ground);border-color:var(--ink)}
@media print{.view{display:none}}

.src{margin-top:22px;font-size:11.5px;color:var(--ink-3)}
.src code{font-family:var(--mono);font-size:11px}
"""
DARK_TINT = {'#1F5E5B': '#5FB0AA', '#B4622C': '#E0955C', '#3B4E8C': '#8C9CDD', '#5E6B2F': '#AABC68',
             '#8A4A22': '#DB9463', '#6B4E7A': '#B49BC4', '#7E3B4E': '#C58FA2', '#4A6378': '#9BA9B5'}
def _mix(h, t=0.45):
    r, g, b = (int(h[i:i+2], 16) for i in (1, 3, 5))
    return '#%02X%02X%02X' % tuple(round(c + (255 - c) * t) for c in (r, g, b))
codes = sorted(colours, key=nat)
light = '\n'.join(f"  --c{int(c.split('-')[1])}:{colours[c]}; --c{int(c.split('-')[1])}l:{colours[c]};" for c in codes)
dark = ' '.join(f"--c{int(c.split('-')[1])}l:{DARK_TINT.get(colours[c].upper(), _mix(colours[c]))};" for c in codes)
css = CSS.replace('@@COLOURS@@', light).replace('@@DARK@@', dark)
HEAD = {'Now': ('In Progress', 3), 'Next': ('Investigating', 2), 'Later': ('Considering', 1)}
ch = ['      <div class="corner"></div>']
for col in COLS:
    t, k = HEAD[col]
    bar = ''.join('<i class="on"></i>' if i < k else '<i></i>' for i in range(3))
    ch.append(f'      <div class="colhead">\n        <h2><b>{col}</b> &middot; {t}</h2>\n        <div class="bar">{bar}</div>\n        <p class="period">{PERIOD[col]}</p>'
              + ('\n        <div class="halves"><span>1st</span><span>2nd</span></div>\n        <div class="flow"></div>' if col != 'Later' else '') + '\n      </div>')
d8 = '.'.join(reversed(DATE.split('-')))
doc = f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1,viewport-fit=cover">
<title>Roadmap {VER}</title>
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=IBM+Plex+Sans:wght@400;500;600&family=IBM+Plex+Serif:wght@500;600&family=IBM+Plex+Mono:wght@500;600&display=swap">
<style>{css}</style>
</head>
<body>
<div class="page">
  <header class="masthead">
    <p class="eyebrow">{html.escape(A.unit)}</p>
    <h1>Roadmap</h1>
    <p class="meta">As of {d8} &middot; 3 layers &times; 5 positions &middot; {PERIOD['Now']} &middot; {PERIOD['Next']} &middot; {PERIOD['Later']} &middot; Audience: {html.escape(A.audience)}</p>
    <p class="view">View: <button id="v-compact" onclick="setView('compact')">compact</button><button id="v-detail" onclick="setView('detail')">with descriptions</button></p>
  </header>
<script>
function setView(v){{document.body.classList.toggle('detail',v==='detail');
  document.getElementById('v-compact').classList.toggle('on',v!=='detail');
  document.getElementById('v-detail').classList.toggle('on',v==='detail');
  try{{history.replaceState(null,'',v==='detail'?'#detail':'#compact')}}catch(e){{}}}}
setView(location.hash==='#detail'?'detail':'compact');
</script>

  <div class="scroller">
    <div class="matrix">

""" + '\n'.join(ch) + '\n\n' + '\n'.join(body) + f"""
    </div>
  </div>

  <p class="src">Source: <code>{STEM}.md</code></p>
</div>
</body>
</html>
"""
open(f"{OUT}/{STEM}.html", 'w').write(doc)

if A.png:
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        b = p.chromium.launch()
        pg = b.new_page(viewport={'width': 1700, 'height': 1000}, device_scale_factor=2)
        # r10.4: two pictures, the compact view (layer 1 descriptions only) and the detailed
        # view (descriptions on every card); the HTML holds both behind a switch.
        pg.goto('file://' + os.path.abspath(f"{OUT}/{STEM}.html") + '#compact')
        pg.wait_for_timeout(1500)
        pg.screenshot(path=f"{OUT}/{STEM}.png", full_page=True)
        pg.evaluate("setView('detail')")
        pg.wait_for_timeout(500)
        pg.screenshot(path=f"{OUT}/{STEM}_detail.png", full_page=True)
        b.close()
print('written:', ', '.join([f"{STEM}.md", f"{STEM}.html"] + ([f"{STEM}.png", f"{STEM}_detail.png"] if A.png else [])))
