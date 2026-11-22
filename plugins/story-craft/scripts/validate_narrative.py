"""validate_narrative.py: check the contract of a story-craft narrative.md.

Usage: python validate_narrative.py narrative.md [--intake intake.md]
The intake defaults to intake.md next to the narrative. Needs PyYAML (pip install pyyaml).

Errors (exit 1):
  beat IDs unique and shaped B01, B02, ... (gaps allowed, never renumber);
  every role known; exactly one reveal, exactly one star (and `star:` points at it),
  at least one villain, exactly one close;
  every proof, cost and versus beat cites an evidence ID that exists in intake.md
  with strength solid or likely (missing fails);
  every cut lists existing beats in narrative order, contains a villain, the reveal and
  the close, and ends on the close.
Warnings (exit 0): cuts too long for their runtime (film-60 > 10 beats, teaser-20 > 5).
Each finding prints as `beat · problem → fix`.
"""
import os
import re
import sys

try:
    import yaml
except ImportError:
    print("PyYAML missing: pip install pyyaml (or: uv run --with pyyaml python validate_narrative.py ...)")
    sys.exit(2)

ROLES = {"moment", "villain", "cost", "turn", "reveal", "pillar", "proof", "objection", "versus",
         "voice", "star", "outcome", "close"}
NEEDS_EVIDENCE = {"proof", "cost", "versus"}
USABLE = {"solid", "likely"}
ID_RE = re.compile(r"^B\d{2,}$")
# runtime in seconds -> max beats (warning only)
BEAT_BUDGET = [(20, 5), (30, 6), (60, 10), (90, 14)]


def frontmatter(path):
    text = open(path, encoding="utf-8").read()
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n", text, re.S)
    if not m:
        raise ValueError("no YAML frontmatter between --- lines")
    return yaml.safe_load(m.group(1)) or {}


def evidence_table(path):
    """Return {E1: 'solid', ...} from the Evidence inventory table of intake.md."""
    rows, inside = {}, False
    for line in open(path, encoding="utf-8"):
        if line.startswith("## "):
            inside = line.strip().lower() == "## evidence inventory"
            continue
        if inside and line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if cells and re.match(r"^E\d+$", cells[0]):
                rows[cells[0]] = cells[-1].lower()
    return rows


def seconds(runtime):
    m = re.match(r"^\s*(\d+(?:\.\d+)?)\s*(s|sec|min)?", str(runtime))
    if not m:
        return None
    value = float(m.group(1))
    return value * 60 if m.group(2) == "min" else value


def validate(narrative_path, intake_path=None):
    errors, warnings = [], []
    try:
        fm = frontmatter(narrative_path)
    except (ValueError, yaml.YAMLError) as exc:
        return [("–", f"frontmatter unreadable: {exc}", "fix the YAML between the --- lines")], []

    beats = fm.get("beats") or []
    if not beats:
        errors.append(("–", "no beats in frontmatter", "add beats: [{id: B01, role: ...}, ...]"))

    intake_path = intake_path or os.path.join(os.path.dirname(os.path.abspath(narrative_path)), "intake.md")
    evidence = evidence_table(intake_path) if os.path.exists(intake_path) else None
    if evidence is None:
        errors.append(("–", f"intake not found at {intake_path}", "pass --intake or run story-craft:stock-take"))

    order, by_role, seen = {}, {}, set()
    for i, b in enumerate(beats):
        bid = str(b.get("id", f"#{i + 1}"))
        if not ID_RE.match(bid):
            errors.append((bid, "beat ID not shaped B01, B02, ...", "use B + two digits; never renumber"))
        if bid in seen:
            errors.append((bid, "duplicate beat ID", "give the new beat the next free ID"))
        seen.add(bid)
        order.setdefault(bid, i)
        role = b.get("role")
        if role not in ROLES:
            errors.append((bid, f"unknown role '{role}'", "use one of " + ", ".join(sorted(ROLES))))
        by_role.setdefault(role, []).append(bid)
        if role in NEEDS_EVIDENCE and evidence is not None:
            eid = b.get("evidence")
            if not eid:
                errors.append((bid, f"{role} beat has no evidence", "cite an intake row (E1, ...) or change the role"))
            elif eid not in evidence:
                errors.append((bid, f"{role} beat cites {eid}, which is not in intake.md", "add the row to the evidence inventory or cite another"))
            elif evidence[eid] not in USABLE:
                errors.append((bid, f"{role} beat cites {eid}, which is '{evidence[eid]}' in intake.md",
                               "find evidence, weaken the beat to a non-claim role, or drop it"))

    reveals, stars = by_role.get("reveal", []), by_role.get("star", [])
    closes, villains = by_role.get("close", []), by_role.get("villain", [])
    if len(reveals) != 1:
        errors.append((", ".join(reveals) or "–", f"{len(reveals)} reveal beats, need exactly one", "keep one reveal; make the others pillars or turns"))
    if len(stars) != 1:
        errors.append((", ".join(stars) or "–", f"{len(stars)} star beats, need exactly one", "pick the one moment they will retell"))
    elif fm.get("star") and fm["star"] != stars[0]:
        errors.append((stars[0], f"frontmatter star: {fm['star']} but the star beat is {stars[0]}", "make star: point at the star beat"))
    if not villains:
        errors.append(("–", "no villain beat", "name the concrete pain the product defeats"))
    if len(closes) != 1:
        errors.append((", ".join(closes) or "–", f"{len(closes)} close beats, need exactly one", "one close: availability, price, the ask"))

    cuts = fm.get("cuts") or {}
    if not cuts:
        errors.append(("–", "no cuts", "add at least the master cut, e.g. keynote: {beats: all}"))
    for name, cut in cuts.items():
        cut = cut or {}
        listed = cut.get("beats", [])
        ids = [str(b.get("id")) for b in beats] if listed == "all" else [str(x) for x in (listed or [])]
        unknown = [x for x in ids if x not in order]
        for x in unknown:
            errors.append((x, f"cut {name} lists a beat that does not exist", "add the beat to the master or remove it from the cut"))
        known = [x for x in ids if x in order]
        if [order[x] for x in known] != sorted(order[x] for x in known):
            errors.append((name, f"cut {name} is out of narrative order", "list the cut's beats in the master's order"))
        roles = {beats[order[x]].get("role") for x in known}
        for need in ("villain", "reveal", "close"):
            if need not in roles:
                errors.append((name, f"cut {name} has no {need}", f"add the {need} beat to cut {name}"))
        if "close" in roles and known and beats[order[known[-1]]].get("role") != "close":
            errors.append((name, f"cut {name} does not end on the close", "move the close to the end of the cut"))
        secs = seconds(cut.get("runtime", ""))
        if secs is not None:
            for limit, max_beats in BEAT_BUDGET:
                if secs <= limit:
                    if len(ids) > max_beats:
                        warnings.append((name, f"cut {name} has {len(ids)} beats for {cut.get('runtime')}", f"aim for ≤ {max_beats}; drop from the middle"))
                    break
    return errors, warnings


def main(argv):
    args = [a for a in argv if not a.startswith("--")]
    intake = argv[argv.index("--intake") + 1] if "--intake" in argv else None
    if intake:
        args.remove(intake)
    if not args:
        print(__doc__)
        return 2
    errors, warnings = validate(args[0], intake)
    for beat, problem, fix in errors:
        print(f"ERROR {beat} · {problem} → {fix}")
    for beat, problem, fix in warnings:
        print(f"WARN  {beat} · {problem} → {fix}")
    print(f"{len(errors)} errors, {len(warnings)} warnings → {'FAIL' if errors else 'PASS'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
