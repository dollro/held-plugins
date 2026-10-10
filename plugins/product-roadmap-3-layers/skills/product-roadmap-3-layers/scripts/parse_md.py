"""parse_md.py (skill product-roadmap-3-layers r8, 2026-09-24) - read a roadmap markdown (skill product-roadmap-3-layers, current format with five
positions and O-/F-/E- IDs) and write a payload for building the Notion database and page.

Usage:
  python3 scripts/parse_md.py --md 2026-09-23_Roadmap_v26.md --out payload.json

The payload holds everything the Notion build needs, in build order:
  schema      property DDL for the new database (no Outcome property: the outcome follows Serves)
  ddl_after   statements run after creation (self-relations, formula); {DS} = data source id
  rows        one object per outcome and card, stored properties only
  relations   Serves and Precedes by ID, set in a second pass once every row has a URL
  page        the "Product Roadmap" page (read by humans) in Notion-flavoured markdown;
              {{DATABASE}} marks where the inline database goes
  page_reference  its child page "Roadmap reference" (looked up, and read by render.py)
  views       view DSL for Grid, By outcome, All
  findings    invariant violations found in the markdown itself (reported, never repaired)
Deterministic: same markdown, same payload. Needs only the standard library.
"""
import json, re, argparse

ap = argparse.ArgumentParser()
ap.add_argument('--md', required=True)
ap.add_argument('--out', required=True)
A = ap.parse_args()
t = open(A.md).read()

# ---------- sections ----------
def section(n):
    m = re.search(rf'^## {n} [^\n]*\n(.*?)(?=^## \d+ |\Z)', t, re.S | re.M)
    return m.group(1).strip() if m else ''

def md_table(block):
    """First markdown table in block -> (header, rows)."""
    lines = [l for l in block.split('\n') if l.strip().startswith('|')]
    if len(lines) < 2:
        return [], []
    cells = lambda l: [c.strip() for c in l.strip().strip('|').split('|')]
    return cells(lines[0]), [cells(l) for l in lines[2:]]

def esc(s):
    """Escape angle brackets outside code spans for Notion markdown."""
    parts = re.split(r'(`[^`]*`)', s)
    return ''.join(p if p.startswith('`') else p.replace('<', '\\<').replace('>', '\\>') for p in parts)

def to_notion_tables(block):
    """Markdown pipe tables -> Notion <table> markup; markers [X, y] -> `X, y`."""
    out, lines, i = [], block.split('\n'), 0
    while i < len(lines):
        l = lines[i]
        if l.strip().startswith('|') and i + 1 < len(lines) and re.match(r'^\s*\|[-| :]+\|\s*$', lines[i + 1]):
            rows = [l]; i += 2
            while i < len(lines) and lines[i].strip().startswith('|'):
                rows.append(lines[i]); i += 1
            out.append('<table header-row="true">')
            for r in rows:
                cs = [c.strip() for c in r.strip().strip('|').split('|')]
                out.append('\t<tr>\n' + '\n'.join(f'\t\t<td>{esc(c)}</td>' for c in cs) + '\n\t</tr>')
            out.append('</table>')
            continue
        out.append(esc(l)); i += 1
    s = '\n'.join(out)
    s = re.sub(r'`\[(ASSUMPTION, verify|SUGGESTED, confirm|NEEDS DECISION[^\]]*)\]`', r'`\1`', s)
    return re.sub(r'\n{2,}', '\n', s).strip()

# ---------- outcomes (section 2) ----------
hdr, orows = md_table(section(2))
col = {h: i for i, h in enumerate(hdr)}
TAG = {'#1F5E5B': 'green', '#B4622C': 'orange', '#3B4E8C': 'blue', '#5E6B2F': 'yellow',
       '#8A4A22': 'brown', '#6B4E7A': 'purple', '#7E3B4E': 'red', '#4A6378': 'gray'}
SPARE = ['pink', 'default']
outcomes, colours = [], []
for r in orows:
    g = lambda k: r[col[k]] if k in col and col[k] < len(r) else ''
    code, hexv = g('Code'), g('Colour').strip('`').upper()
    tag = TAG.get(hexv) or (SPARE.pop(0) if SPARE else 'default')
    colours.append({'code': code, 'hex': hexv, 'tag': tag})
    outcomes.append({'ID': code, 'Title': g('Outcome'), 'Layer': '1 Business Outcome', 'Position': g('Position'),
                     'Outcome': code, 'Value': g('Value') or None,
                     'Evidence type': (g('Type') or '').capitalize() or None, 'Description': g('Evidence'),
                     'Impact dimension': [d.strip() for d in g('Impact').split(',') if d.strip()] or None,
                     'Source': 'Roadmap ' + re.sub(r'^.*/', '', A.md)})

# ---------- cards (section 3 YAML) ----------
y = re.search(r'```yaml\n(.*?)```', section(3), re.S).group(1)
cards, cur = [], None
for line in y.split('\n'):
    m = re.match(r'\s*- id: (\S+)', line)
    if m:
        cur = {'id': m.group(1)}; cards.append(cur); continue
    m = re.match(r'\s+([a-z_]+): (.*)$', line)
    if m and cur is not None:
        v = m.group(2).strip()
        if v.startswith('"') and v.endswith('"'):
            v = v[1:-1].replace('\\"', '"')
        elif v.startswith('[') and v.endswith(']'):
            v = [x.strip() for x in v[1:-1].split(',') if x.strip()]
        cur[m.group(1)] = v
card_rows, relations = [], []
for c in cards:
    L = int(c.get('layer', 2))
    card_rows.append({'ID': c['id'], 'Title': c.get('title', ''), 'Layer': '2 Product Feature' if L == 2 else '3 Tech & Data Enabler',
                      'Position': c.get('position'), 'Outcome': c.get('outcome') if L == 2 else None,
                      'Standalone': c.get('standalone') if L == 3 else None, 'Kind': c.get('kind') if L == 3 else None,
                      'Blocks': c.get('blocks') or [], 'Description': c.get('desc'), 'PRD': c.get('prd') == 'yes',
                      'Source': c.get('source'), 'Linear': c.get('linear')})
    if L == 2 and c.get('outcome'):
        relations.append({'from': c['id'], 'property': 'Serves', 'to': [c['outcome']]})
    if L == 3 and c.get('serves'):
        relations.append({'from': c['id'], 'property': 'Serves', 'to': c['serves'] if isinstance(c['serves'], list) else [c['serves']]})
    if c.get('precedes'):
        relations.append({'from': c['id'], 'property': 'Precedes', 'to': [c['precedes']]})
rows = outcomes + card_rows

# ---------- schema ----------
positions = []
for r in rows:
    if r['Position'] and r['Position'] not in positions:
        positions.append(r['Position'])
order = {'Now': 0, 'Next': 1, 'Later': 2}
positions.sort(key=lambda p: (order.get(p.split(' · ')[0], 9), p))
blocks = sorted({b for r in card_rows for b in r['Blocks']}, key=lambda b: int(b[1:]))
# r10.8: the impact dimensions are the roadmap's own set (section 1), read from the outcome table
# in order of first appearance; nothing is hardcoded. Colours cycle through a fixed list.
dims = []
for o in outcomes:
    for d in (o['Impact dimension'] or []):
        if d not in dims: dims.append(d)
DIM_COLOURS = ['blue', 'orange', 'green', 'gray', 'pink', 'purple', 'yellow', 'brown', 'red']
q = lambda xs: ', '.join(f"'{x}':{c}" for x, c in xs)
schema = ', '.join([
    '"Title" TITLE', '"ID" RICH_TEXT', '"No" UNIQUE_ID',
    '"Layer" SELECT(' + q([('1 Business Outcome', 'gray'), ('2 Product Feature', 'gray'), ('3 Tech & Data Enabler', 'gray')]) + ')',
    '"Position" SELECT(' + q([(p, 'default') for p in positions]) + ')',
    '"Blocks" MULTI_SELECT(' + q([(b, 'gray') for b in blocks]) + ')',
    '"Standalone" SELECT(' + q([('yes', 'default'), ('no', 'default')]) + ')',
    '"Kind" SELECT(' + q([('build', 'default'), ('decision', 'default')]) + ')',
    '"Value" SELECT(' + q([('outside', 'default'), ('inside', 'default')]) + ')',
    '"Evidence type" SELECT(' + q([('Criterion', 'default'), ('Metric', 'default')]) + ')',
    '"Impact dimension" MULTI_SELECT(' + q([(d, DIM_COLOURS[i % len(DIM_COLOURS)]) for i, d in enumerate(dims)]) + ')',
    '"Description" RICH_TEXT', '"PRD" CHECKBOX', '"Source" RICH_TEXT', '"Linear" URL'])
formula = ('lets(l, substring(format(prop("Layer")), 0, 1), '
           'codes, ifs(l == "1", [prop("Code")], '
           'l == "2", prop("Serves").map(current.prop("Code")).unique(), '
           'prop("Serves").map(current.prop("Serves")).flat().map(current.prop("Code")).unique()), '
           'palette, ["gray", "brown", "orange", "yellow", "green", "blue", "purple", "pink", '
           '"gray_background", "brown_background", "orange_background", "yellow_background", '
           '"green_background", "blue_background", "purple_background", "pink_background", "red_background"], '
           'if(codes.length() != 1, style(codes.join(", "), "b", "red"), '
           'lets(c, codes.first(), n, toNumber(replace(c, "^[A-Z]-", "")), '
           'style(c, "b", palette.at(mod(n, 17))))))')  # r10.5: colour derived from the code number, red reserved
code_formula = ('let(l, substring(format(prop("Layer")), 0, 1), if(empty(prop("ID")), '
                'ifs(l == "1", "O", l == "2", "F", "E") + "-" + format(prop("No")), prop("ID")))')
ddl_after = ["ADD COLUMN \"Code\" FORMULA('" + code_formula.replace("'", "\\'") + "')","ADD COLUMN \"Serves\" RELATION('{DS}', DUAL 'Served by' 'served_by')",
             "ADD COLUMN \"Precedes\" RELATION('{DS}')",
             "ADD COLUMN \"Outcome code\" FORMULA('" + formula.replace("'", "\\'") + "')",
             "ADD COLUMN \"Serves (ID)\" FORMULA('prop(\"Serves\").map(current.prop(\"Code\")).sort().join(\", \")')",
             "ADD COLUMN \"Served by (ID)\" FORMULA('prop(\"Served by\").map(current.prop(\"Code\")).sort().join(\", \")')"]

# ---------- page ----------
s1 = section(1)
basis = re.search(r'^Basis:.*$', s1, re.M)
basis = basis.group(0) if basis else ''
ctx = '\n'.join(l for l in s1.split('\n') if not l.startswith('This roadmap orders intent') and not l.startswith('Basis:')).strip()

s4 = section(4)
seq_tbl = to_notion_tables('\n'.join(l for l in s4.split('\n') if l.startswith('|')))
lead = re.search(r'\*\*Lead time[^*]*\*\* ?(.*)', s4)
reasons = re.findall(r'^- \*\*([EF]-\d+ before [EF]-\d+)\.\*\* (.*)$', s4, re.M)
incell = re.search(r'\*\*In-cell order, row 3\.\*\* (.*)', s4)
seq = ['The position of each card is a property in the database. This section holds only what the data cannot say: '
       'what each position brings into being. Why each hard prerequisite comes first is on the reference page.', seq_tbl]
seq_ref = []
if lead: seq_ref.append('**Lead time.** ' + esc(lead.group(1)))
if reasons:
    seq_ref.append('**Why each prerequisite comes first**')
    seq_ref += [f'- **{a}.** {esc(b)}' for a, b in reasons]
if incell: seq_ref.append('**In-cell order, row 3.** ' + esc(incell.group(1)))
k = ctx.find('**Row names')
ctx_main, ctx_ref = (ctx[:k].strip(), ctx[k:].strip()) if k >= 0 else (ctx, '')

scope = re.sub(r'^\*\*(Too granular|Deliberately not|Deliberately postponed)\*\*:?\s*$', r'### \1', section(6), flags=re.M)

s9 = section(9)
dev = re.search(r'\*\*Deviations\*\*\n\n(.*?)(?:\n\n[^|]|\Z)', s9, re.S)
dev_rows = []
if dev:
    _, drs = md_table(dev.group(1))
    for r in drs:
        if len(r) >= 4:
            m = re.match(r'(.*) \((R\d+b?)\)$', r[1])
            dev_rows.append([r[0], m.group(2) if m else '', m.group(1) if m else r[1], r[2], r[3]])
dev_md = ('Deliberate departures from the format\'s rules, with reason and price. The generator detects a breach; '
          'the reason and the price come from here.\n'
          + to_notion_tables('| No | Rule | Deviation | Reason | Price |\n|---|---|---|---|---|\n'
                             + '\n'.join('| ' + ' | '.join(r) + ' |' for r in dev_rows)))

colour_md = ('The outcome sentences and evidence are rows in the database (layer 1). This table only maps codes to the '
             'exact roadmap colours used for the picture; the Notion tag colour on the board is derived by the '
             '"Outcome code" formula from the code number (palette index n mod 17, red reserved for a card that '
             'resolves to no outcome or to two).\n'
             + to_notion_tables('| Code | Roadmap colour |\n|---|---|\n'
                                + '\n'.join(f"| {c['code']} | `{c['hex']}` |" for c in colours)))

callout = '''<callout icon="🧭" color="gray_bg">
	**Roadmap.** The board below is the source of truth; cards are moved and edited there. Each version is generated from it as md, html and png and is never edited by hand.
	Background that is looked up rather than read is on the child page Roadmap reference. Agents start at the spec.
</callout>'''
# main page, read by humans; the reference page carries what is looked up (spec section 5)
page = '\n'.join([
    callout,
    '# Target picture and context', to_notion_tables(ctx_main), '{{DATABASE}}',
    '# Sequence', '\n'.join(seq),
    '# Demand from the sequence', to_notion_tables(section(7)),
    '# Open gaps', to_notion_tables(section(8))])
page_reference = '\n'.join([
    'Background to the roadmap page that is looked up rather than read. A heading "… · details" continues the section of the same name there.',
    '# Target picture and context · details', to_notion_tables(ctx_ref),
    '# Outcome colours', colour_md,
    '# Sequence · details', '\n'.join(seq_ref),
    '# System building blocks', to_notion_tables(section(5)),
    '# Scope boundaries', to_notion_tables(scope),
    '# Deviations', dev_md,
    '---', esc(basis)])

views = [
    {'name': 'Grid', 'type': 'board', 'configure': 'GROUP BY "Position"; SORT BY "Layer" ASC, "No" ASC; SHOW "Title", "Code", "Outcome code"',
     'by_hand': 'sub-group by Layer; drag the columns into position order (the API cannot set either)'},
    {'name': 'By outcome', 'type': 'table', 'configure': 'SORT BY "Layer" ASC, "No" ASC; SHOW "Title", "Code", "Layer", "Outcome code", "Impact dimension", "Serves (ID)", "Served by (ID)", "Precedes"',
     'by_hand': 'group by Outcome code'},
    {'name': 'All', 'type': 'table', 'configure': 'SORT BY "Layer" ASC, "No" ASC'}]

# ---------- invariants on the markdown itself ----------
byid = {r['ID']: r for r in rows}
PI = lambda p: positions.index(p) if p in positions else -1
findings = []
ids = [r['ID'] for r in rows]
if len(ids) != len(set(ids)): findings.append('I6 duplicate IDs')
for r in rows:
    pref = 'OFE'[int(r['Layer'][0]) - 1]
    if not re.fullmatch(pref + r'-[1-9]\d*', r['ID']): findings.append(f"I6 {r['ID']}")
    if not r['Position']: findings.append(f"I2/I3 {r['ID']} has no position")
served = {x['from']: x['to'] for x in relations if x['property'] == 'Serves'}
for c in card_rows:
    if c['Layer'][0] == '3':
        oc = {byid[f]['Outcome'] for f in served.get(c['ID'], []) if f in byid}
        if len(oc) != 1: findings.append(f"I3 {c['ID']} serves outcomes {sorted(oc)}")
        c['_oc'] = next(iter(oc)) if len(oc) == 1 else None
    else:
        c['_oc'] = c['Outcome']
for o in outcomes:
    if o['Position'] and o['Position'].endswith('1st'):
        per = o['Position'].rsplit(' · ', 1)[0]
        if any(c['_oc'] == o['ID'] and c['Position'] == per + ' · 2nd' for c in card_rows):
            findings.append(f"I8 {o['ID']}")
for x in relations:
    for tgt in x['to']:
        if tgt not in byid: findings.append(f"{x['property']} {x['from']} → unknown {tgt}")
        elif x['property'] == 'Precedes' and PI(byid[x['from']]['Position']) > PI(byid[tgt]['Position']):
            findings.append(f"I5 {x['from']}")
for c in card_rows: c.pop('_oc', None)

for r in rows:
    r.pop('Outcome', None)  # r7: the outcome is derived from Serves, never stored
json.dump({'source': A.md, 'page_reference': page_reference, 'schema': schema, 'ddl_after': ddl_after, 'positions': positions, 'colours': colours,
           'rows': rows, 'relations': relations, 'page': page, 'views': views, 'findings': findings},
          open(A.out, 'w'), indent=1, ensure_ascii=False)
print(f"{len(outcomes)} outcomes, {len(card_rows)} cards, {len(relations)} relations, {len(positions)} positions; findings: {findings or 'none'}")
