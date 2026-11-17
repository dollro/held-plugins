/**
 * report.mjs: flattens captures into comparable numbers, applies thresholds
 * (with an optional baseline ratchet), writes report.md and compare.md.
 */

/** One flat row of "lower is better" numbers per capture. null = not measured. */
export function summarize(c) {
  if (c.failed || !c.metrics) return { failed: c.failed || 'no metrics' };
  const m = c.metrics;
  const axe = c.axe || null;
  return {
    off_token_colors: m.tokens && m.tokens.colorTokens ? m.tokens.offColors.length : null,
    near_token_colors: m.tokens && m.tokens.colorTokens ? m.tokens.nearColors.length : null,
    off_token_font_sizes: m.tokens && m.tokens.lengthTokens ? m.tokens.offFontSizes.length : null,
    off_token_radii: m.tokens && m.tokens.lengthTokens ? m.tokens.offRadii.length : null,
    off_grid_spacing: m.spacing.offGrid.length,
    colors_distinct: m.colors.distinct,
    font_sizes: m.type.fontSizes.length,
    font_weights: m.type.fontWeights.length,
    font_families: m.type.families.length,
    filled_actions: m.actions.filledActions,
    alignment_near_misses: m.alignment.nearMisses.length,
    alignment_lines: m.alignment.lines,
    axe_serious: axe ? axe.filter((v) => ['serious', 'critical'].includes(v.impact)).length : null,
    axe_total: axe ? axe.length : null,
    targets_below_24: m.targets.below24,
    targets_below_44: m.targets.below44,
    horizontal_scroll: m.page.horizontalScroll ? 1 : 0,
    tiny_text: m.type.tinyText.count,
    truncated: m.overflow.truncated.length,
    missing_focus: c.focus ? c.focus.missing.length : null,
    cls: c.perf ? +c.perf.cls.toFixed(3) : null,
    overshoot_easing: c.motion ? c.motion.overshoot : null,
    slow_transitions: c.motion ? c.motion.slow : null,
    infinite_animations: c.motion ? c.motion.infiniteAnimations : null,
    console_errors: c.errors.length,
  };
}

const LIMIT_KEYS = {
  off_token_colors: 'off_token_colors',
  off_token_font_sizes: 'off_token_font_sizes',
  off_grid_spacing: 'off_grid_spacing',
  font_sizes: 'font_sizes_max',
  font_weights: 'font_weights_max',
  font_families: 'font_families_max',
  filled_actions: 'filled_actions_max',
  alignment_near_misses: 'alignment_near_misses',
  axe_serious: 'axe_serious',
  targets_below_24: 'targets_below_24',
  horizontal_scroll: 'horizontal_scroll',
  missing_focus: 'missing_focus',
  tiny_text: 'tiny_text',
  cls: 'cls_max',
  overshoot_easing: 'overshoot_easing',
  infinite_animations: 'infinite_animations',
};

/**
 * Gate. Without a baseline: value must be <= threshold.
 * With a baseline (ratchet): value must be <= max(threshold, baseline value),
 * so an MVP never gets worse and is never asked to be better than the threshold.
 */
export function evaluate(captures, thresholds, baseline = null) {
  const fails = [];
  for (const c of captures) {
    const s = summarize(c);
    if (s.failed) {
      fails.push({ capture: c.id, check: 'capture', value: s.failed, limit: 'loads' });
      continue;
    }
    // filled_actions only makes sense for the default state at a given viewport
    for (const [metric, tKey] of Object.entries(LIMIT_KEYS)) {
      const limit0 = thresholds[tKey];
      const v = s[metric];
      if (limit0 == null || v == null) continue;
      if (metric === 'filled_actions' && c.state !== 'default') continue;
      if (metric === 'infinite_animations' && c.live) continue; // a spinner in a loading state is expected
      const base = baseline?.[c.id]?.[metric];
      const limit = base != null ? Math.max(limit0, base) : limit0;
      if (v > limit) fails.push({ capture: c.id, check: metric, value: v, limit, ratchet: base != null && base > limit0 });
    }
  }
  return fails;
}

export function baselineFrom(captures) {
  const out = {};
  for (const c of captures) {
    const s = summarize(c);
    if (!s.failed) out[c.id] = s;
  }
  return out;
}

// ---------------------------------------------------------------------------

const t = (rows, head) => {
  if (!rows.length) return '_none_\n';
  const esc = (v) => String(v ?? '').replace(/\|/g, '\\|').replace(/\n/g, ' ');
  return `| ${head.join(' | ')} |\n|${head.map(() => '-').join('|')}|\n${rows.map((r) => `| ${r.map(esc).join(' | ')} |`).join('\n')}\n`;
};

const where = (caps) => (caps.size > 3 ? `${caps.size} captures, e.g. ${[...caps][0]}` : [...caps].join(', '));

function aggregate(captures, pick, keyOf) {
  const map = new Map();
  for (const c of captures) {
    for (const item of pick(c) || []) {
      const k = keyOf(item);
      const e = map.get(k) || { ...item, captures: new Set(), total: 0 };
      e.captures.add(c.id);
      e.total += item.count ?? item.nodes ?? 1;
      map.set(k, e);
    }
  }
  return [...map.values()].sort((a, b) => b.total - a.total);
}

export function renderReport({ label, cfg, captures, fails, sheets }) {
  const ok = captures.filter((c) => !c.failed);
  const tok = ok.find((c) => c.tokenSource)?.tokenSource;
  let md = `# Visual review: ${label}\n\n`;
  md += `Base URL ${cfg.base_url} · ${captures.length} captures (${captures.length - ok.length} failed) · `;
  md += tok ? `tokens: ${tok.colors} colours, ${tok.lengths} lengths, ${tok.shadows} shadows (source: ${cfg.tokens.source})\n\n` : `no tokens found, token checks skipped (set tokens: in the config)\n\n`;
  md += `This file is the **measured layer**. The vision review (rubric in references/vision-rubric.md) goes into review.md next to it.\n\n`;

  md += `## Gate\n\n${fails.length ? `**${fails.length} failing checks.**` : '**All checks pass.**'}\n\n`;
  if (fails.length) {
    const groups = new Map();
    for (const f of fails) {
      const place = f.capture.split('/')[0];
      const k = `${f.check}|${place}`;
      const g = groups.get(k) || { check: f.check, place, caps: [], values: [], limits: new Set() };
      g.caps.push(f.capture.split('/').slice(1).join('/'));
      g.values.push(f.value);
      g.limits.add(f.limit + (f.ratchet ? ' (baseline)' : ''));
      groups.set(k, g);
    }
    const range = (vs) => (vs.every((v) => typeof v === 'number') ? (Math.min(...vs) === Math.max(...vs) ? vs[0] : `${Math.min(...vs)} to ${Math.max(...vs)}`) : vs[0]);
    md += t([...groups.values()].map((g) => [g.check, g.place, range(g.values), [...g.limits].join(', '), g.caps.length > 4 ? `${g.caps.length} captures` : g.caps.join(', ')]), ['Check', 'Place', 'Value', 'Limit', 'Where']);
  }

  const cols = ['off_token_colors', 'near_token_colors', 'off_grid_spacing', 'font_sizes', 'font_weights', 'colors_distinct', 'filled_actions', 'alignment_near_misses', 'axe_serious', 'targets_below_24', 'horizontal_scroll', 'missing_focus', 'cls'];
  const short = ['off-tok col', 'near-tok col', 'off-grid', 'sizes', 'weights', 'colours', 'filled CTAs', 'align miss', 'axe ser.', '<24px', 'h-scroll', 'no focus', 'CLS'];
  md += `\n## Numbers per capture\n\nLower is better everywhere. Empty = not measured for this capture.\n\n`;
  md += t(captures.map((c) => {
    const s = summarize(c);
    return s.failed ? [c.id, `FAILED: ${s.failed}`, ...cols.slice(1).map(() => '')] : [c.id, ...cols.map((k) => s[k])];
  }), ['Capture', ...short]);

  md += `\n## Findings\n\n`;
  const offC = aggregate(ok, (c) => c.metrics.tokens?.offColors, (i) => `${i.role}|${i.value}`);
  md += `### Off-token colours\n\nColours in use that match no token. Each is either a missing token or a hard-coded value.\n\n`;
  md += t(offC.slice(0, 20).map((i) => [i.value, i.role, i.total, i.nearest + ` (Δ${i.distance})`, i.sample, i.captures.size]), ['Colour', 'Role', 'Uses', 'Nearest token', 'Example', 'Captures']);
  const nearC = aggregate(ok, (c) => c.metrics.tokens?.nearColors, (i) => `${i.role}|${i.value}`);
  md += `\n### Near-token colours\n\nClose to a token but not equal: almost always a hand-typed approximation. Replace with the token.\n\n`;
  md += t(nearC.slice(0, 20).map((i) => [i.value, i.role, i.total, i.nearest + ` (Δ${i.distance})`, i.sample]), ['Colour', 'Role', 'Uses', 'Should be', 'Example']);
  const offFs = aggregate(ok, (c) => c.metrics.tokens?.offFontSizes, (i) => i.value);
  const offR = aggregate(ok, (c) => c.metrics.tokens?.offRadii, (i) => i.value);
  const offSh = aggregate(ok, (c) => c.metrics.tokens?.offShadows, (i) => i.value);
  md += `\n### Off-token font sizes, radii, shadows\n\n`;
  md += t([...offFs.map((i) => ['font-size', i.value, i.total, i.sample]), ...offR.map((i) => ['radius', i.value, i.total, i.sample]), ...offSh.slice(0, 8).map((i) => ['shadow', i.value, i.total, i.sample])], ['Kind', 'Value', 'Uses', 'Example']);
  const grid = aggregate(ok, (c) => c.metrics.spacing.offGrid, (i) => i.value);
  md += `\n### Spacing off the ${cfg.grid}px grid\n\n`;
  md += t(grid.slice(0, 15).map((i) => [i.value, i.total, i.sample]), ['Value', 'Uses', 'Example']);
  md += `\n### Alignment near-misses\n\nTwo alignment lines 1 to 3px apart: elements that were meant to line up and don't.\n\n`;
  const misses = new Map();
  for (const c of ok) for (const n of c.metrics.alignment.nearMisses) {
    const k = n.samples.join(' ↔ ');
    const e = misses.get(k) || { lines: `${n.x[0]}px / ${n.x[1]}px`, caps: new Set() };
    e.caps.add(c.id);
    misses.set(k, e);
  }
  md += t([...misses.entries()].slice(0, 20).map(([k, e]) => [k, e.lines, where(e.caps)]), ['Elements', 'Lines', 'Where']);

  md += `\n### Type and colour palette in use\n\n`;
  md += t(ok.filter((c) => c.state === 'default' && c.viewport === cfg.viewports[cfg.viewports.length - 1].id).map((c) => [
    c.id,
    c.metrics.type.fontSizes.map((f) => f.value).join(' '),
    c.metrics.type.fontWeights.map((f) => f.value).join(' '),
    c.metrics.type.families.map((f) => f.value).join(', '),
    c.metrics.colors.saturatedFillShare,
  ]), ['Capture', 'Font sizes', 'Weights', 'Families', 'Saturated fill share']);

  const axe = aggregate(ok, (c) => c.axe, (i) => i.id);
  md += `\n### Accessibility (axe, WCAG 2.2 AA)\n\n`;
  md += t(axe.map((i) => [i.id, i.impact, i.help, i.total, i.captures.size, (i.samples || []).join(' · ')]), ['Rule', 'Impact', 'Problem', 'Nodes', 'Captures', 'Example']);

  md += `\n### Targets, overflow, truncation, tiny text\n\n`;
  const issues = new Map();
  const add = (c, issue, el) => {
    const k = `${issue}|${el}`;
    const e = issues.get(k) || { issue, el, caps: new Set() };
    e.caps.add(c.id);
    issues.set(k, e);
  };
  for (const c of ok) {
    const m = c.metrics;
    for (const s of m.targets.samples24) add(c, 'target < 24px', `${s.el} ${s.size}`);
    for (const s of m.overflow.offscreenRight) add(c, 'off-screen right', s.el);
    for (const s of m.overflow.truncated) add(c, 'truncated text', s.el);
    for (const s of m.type.tinyText.samples) add(c, 'text < 12px', `${s.el} ${s.size}px`);
    for (const s of m.type.longLines) add(c, 'line too long', `${s.el} ~${s.approxChars}ch`);
  }
  md += t([...issues.values()].slice(0, 30).map((e) => [e.issue, e.el, where(e.caps)]), ['Issue', 'Element', 'Where']);

  md += `\n### Focus\n\n`;
  md += t(ok.filter((c) => c.focus).map((c) => [c.id, c.focus.stops, c.focus.missing.join(' · ') || 'all visible']), ['Capture', 'Tab stops checked', 'No visible focus']);

  md += `\n### Motion and perceived speed\n\n`;
  md += t(ok.filter((c) => c.motion && c.state === 'default' && c.viewport === cfg.viewports[cfg.viewports.length - 1].id).map((c) => [
    c.id,
    Object.keys(c.motion.durations).sort((a, b) => a - b).map((d) => `${d}ms`).join(' ') || 'none',
    Object.keys(c.motion.easings).slice(0, 4).join(' · ') || '',
    c.motion.overshoot,
    c.motion.infiniteAnimations,
    c.reducedMotion ? (c.reducedMotion.failed ? 'failed' : c.reducedMotion.runningAnimations) : '',
    c.perf ? c.perf.cls.toFixed(3) : '',
    c.perf ? Math.round(c.perf.lcp) : '',
  ]), ['Capture', 'Durations', 'Easings', 'Overshoot', 'Infinite anim.', 'Running with reduced motion', 'CLS', 'LCP ms (dev server, relative only)']);

  const errs = ok.filter((c) => c.errors.length);
  if (errs.length) {
    md += `\n### Console errors\n\n`;
    md += t(errs.map((c) => [c.id, c.errors.length, c.errors[0]]), ['Capture', 'Errors', 'First']);
  }

  md += `\n## For the vision pass\n\nRead these with the rubric. Contact sheets first, single screenshots for detail.\n\n`;
  md += sheets.map((s) => `- \`${s}\``).join('\n') + '\n';
  return md;
}

export function renderCompare(a, b, labelA, labelB) {
  const keys = ['off_token_colors', 'near_token_colors', 'off_grid_spacing', 'font_sizes', 'font_weights', 'colors_distinct', 'filled_actions', 'alignment_near_misses', 'axe_serious', 'axe_total', 'targets_below_24', 'targets_below_44', 'horizontal_scroll', 'tiny_text', 'truncated', 'missing_focus', 'cls', 'overshoot_easing', 'infinite_animations', 'console_errors'];
  const byId = (caps) => Object.fromEntries(caps.map((c) => [c.id, summarize(c)]));
  const A = byId(a), B = byId(b);
  const ids = Object.keys(B).filter((id) => A[id]);
  const totals = {};
  let better = 0, worse = 0;
  const rows = [];
  for (const id of ids) {
    if (A[id].failed || B[id].failed) continue;
    for (const k of keys) {
      const x = A[id][k], y = B[id][k];
      if (x == null || y == null) continue;
      totals[k] = totals[k] || [0, 0];
      totals[k][0] += x;
      totals[k][1] += y;
      if (y < x) better++;
      if (y > x) { worse++; rows.push([id, k, x, y]); }
    }
  }
  let md = `# Compare: ${labelA} → ${labelB}\n\n${ids.length} matching captures. ${better} numbers improved, ${worse} got worse.\n\n## Totals\n\n`;
  md += t(Object.entries(totals).map(([k, [x, y]]) => [k, +x.toFixed(3), +y.toFixed(3), y < x ? 'better' : y > x ? '**worse**' : 'same']), ['Metric', labelA, labelB, '']);
  md += `\n## Regressions\n\n` + t(rows, ['Capture', 'Metric', labelA, labelB]);
  md += `\nNumbers say what changed, not whether it looks better. Do the pairwise vision review on the side-by-side sheets (references/vision-rubric.md, "Pairwise").\n`;
  return md;
}
