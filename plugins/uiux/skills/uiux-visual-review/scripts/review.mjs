#!/usr/bin/env node
/**
 * review.mjs: the measured layer of uiux-visual-review.
 *
 *   review init                      scaffold review.config.yaml and .uireview/.gitignore
 *   review run [--place id] [--state id] [--label name] [--no-axe] [--check]
 *                                    capture every place x state x viewport x scheme,
 *                                    write metrics.json, report.md and contact sheets
 *   review check [label]             apply thresholds (and the baseline ratchet) to a run; exit 1 on failure
 *   review baseline [label]          write review.baseline.json from a run (commit it)
 *   review compare <labelA> <labelB> [--all]
 *                                    metric deltas plus side-by-side sheets for the pairwise review
 *   review dna <url> [--viewport 1440x900] [--scheme light|dark] [--out dir]
 *                                    extract the design DNA of any page (inspiration intake)
 *
 * Options: --config <path> (default ./review.config.yaml)
 */

import { parseArgs } from 'node:util';
import { readFile, writeFile, mkdir, copyFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, join, resolve } from 'node:path';
import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import { chromium } from 'playwright';
import { ensureAuth } from '../../design-parity/scripts/lib/auth.mjs';
import { loadConfig, expandMatrix, tokensFromDtcg } from './lib/config.mjs';
import { capture } from './lib/capture.mjs';
import { evaluate, baselineFrom, renderReport, renderCompare } from './lib/report.mjs';
import { buildSheets, buildPairs } from './lib/sheet.mjs';
import { measureMotion, measurePage } from './lib/page-measure.mjs';

const HERE = dirname(fileURLToPath(import.meta.url));

async function main() {
  const [cmd, ...rest] = process.argv.slice(2);
  const { values: args, positionals } = parseArgs({
    args: rest,
    allowPositionals: true,
    options: {
      config: { type: 'string', default: 'review.config.yaml' },
      place: { type: 'string' },
      state: { type: 'string' },
      label: { type: 'string' },
      'no-axe': { type: 'boolean', default: false },
      check: { type: 'boolean', default: false },
      all: { type: 'boolean', default: false },
      viewport: { type: 'string', default: '1440x900' },
      scheme: { type: 'string', default: 'light' },
      out: { type: 'string' },
    },
  });

  switch (cmd) {
    case 'init': return cmdInit(args);
    case 'run': return cmdRun(args);
    case 'check': return cmdCheck(args, positionals[0]);
    case 'baseline': return cmdBaseline(args, positionals[0]);
    case 'compare': return cmdCompare(args, positionals);
    case 'dna': return cmdDna(args, positionals[0]);
    default:
      process.stderr.write('Usage: review init | run | check [label] | baseline [label] | compare <a> <b> | dna <url>\n');
      process.exit(cmd ? 1 : 0);
  }
}

async function cmdInit(args) {
  const target = resolve(args.config);
  if (existsSync(target)) throw new Error(`${target} exists; not overwriting.`);
  await copyFile(join(HERE, '../references/review.config.example.yaml'), target);
  const dir = join(dirname(target), '.uireview');
  await mkdir(dir, { recursive: true });
  await writeFile(join(dir, '.gitignore'), '*\n!.gitignore\n');
  console.log(`Wrote ${target} and ${dir}/.gitignore. Fill in places: from the breadboard, then run "review run".`);
}

function stamp() {
  const d = new Date();
  const p = (n) => String(n).padStart(2, '0');
  return `${d.getFullYear()}${p(d.getMonth() + 1)}${p(d.getDate())}-${p(d.getHours())}${p(d.getMinutes())}${p(d.getSeconds())}`;
}

async function cmdRun(args) {
  const cfg = await loadConfig(args.config);
  if (cfg.tokens.source === 'dtcg') cfg._dtcg = await tokensFromDtcg(cfg.tokens.files, cfg._rootDir);
  const label = args.label || stamp();
  const runDir = join(cfg.artifactsDir, 'runs', label);
  await mkdir(runDir, { recursive: true });
  const matrix = expandMatrix(cfg, { place: args.place, state: args.state });
  if (!matrix.length) throw new Error('Nothing to capture: check --place / --state.');

  if (cfg.setup) execSync(cfg.setup, { cwd: cfg._rootDir, stdio: 'inherit' });
  const browser = await chromium.launch();
  const captures = [];
  try {
    const auth = await ensureAuth(browser, cfg);
    const focusDone = new Set();
    for (const item of matrix) {
      const widest = cfg.viewports[cfg.viewports.length - 1].id;
      const focus = item.state.id === 'default' && item.viewport.id === widest && item.scheme === cfg.schemes[0] && !focusDone.has(item.place.id);
      if (focus) focusDone.add(item.place.id);
      process.stderr.write(`[review] ${item.id}\n`);
      const c = await capture(browser, cfg, item, auth, runDir, { focus, noAxe: args['no-axe'] });
      if (c.failed) process.stderr.write(`[review]   failed: ${c.failed}\n`);
      captures.push(c);
    }
    const sheets = await buildSheets(browser, cfg, captures, runDir);
    const baseline = await readBaseline(cfg);
    const fails = evaluate(captures, cfg.thresholds, baseline);
    await writeFile(join(runDir, 'metrics.json'), JSON.stringify({ label, base_url: cfg.base_url, created: new Date().toISOString(), captures }, null, 2));
    await writeFile(join(runDir, 'report.md'), renderReport({ label, cfg, captures, fails, sheets }));
    await writeFile(join(cfg.artifactsDir, 'latest'), label);
    console.log(`Run ${label}: ${captures.length} captures, ${captures.filter((c) => c.failed).length} failed, ${fails.length} failing checks${baseline ? ' (baseline ratchet on)' : ''}.`);
    console.log(`Report: ${join(runDir, 'report.md')}`);
    for (const s of sheets) console.log(`Sheet:  ${s}`);
    if (args.check && fails.length) process.exitCode = 1;
  } finally {
    await browser.close();
    if (cfg.teardown) execSync(cfg.teardown, { cwd: cfg._rootDir, stdio: 'inherit' });
  }
}

async function loadRun(cfg, label) {
  const l = label || (existsSync(join(cfg.artifactsDir, 'latest')) ? (await readFile(join(cfg.artifactsDir, 'latest'), 'utf8')).trim() : null);
  if (!l) throw new Error('No run found. Run "review run" first or pass a label.');
  const p = join(cfg.artifactsDir, 'runs', l, 'metrics.json');
  if (!existsSync(p)) throw new Error(`No metrics for run ${l} at ${p}`);
  return { label: l, ...JSON.parse(await readFile(p, 'utf8')) };
}

async function readBaseline(cfg) {
  const p = join(cfg._rootDir, 'review.baseline.json');
  return existsSync(p) ? JSON.parse(await readFile(p, 'utf8')).captures : null;
}

async function cmdCheck(args, label) {
  const cfg = await loadConfig(args.config);
  const run = await loadRun(cfg, label);
  const fails = evaluate(run.captures, cfg.thresholds, await readBaseline(cfg));
  for (const f of fails) console.log(`FAIL ${f.capture} ${f.check}: ${f.value} > ${f.limit}${f.ratchet ? ' (baseline)' : ''}`);
  console.log(fails.length ? `${fails.length} failing checks in run ${run.label}.` : `Run ${run.label}: all checks pass.`);
  if (fails.length) process.exitCode = 1;
}

async function cmdBaseline(args, label) {
  const cfg = await loadConfig(args.config);
  const run = await loadRun(cfg, label);
  const p = join(cfg._rootDir, 'review.baseline.json');
  await writeFile(p, JSON.stringify({ from_run: run.label, created: new Date().toISOString(), captures: baselineFrom(run.captures) }, null, 2) + '\n');
  console.log(`Wrote ${p} from run ${run.label}. Commit it: CI then fails only on regressions beyond it.`);
}

async function cmdCompare(args, [a, b]) {
  if (!a || !b) throw new Error('Usage: review compare <labelA> <labelB>');
  const cfg = await loadConfig(args.config);
  const A = await loadRun(cfg, a), B = await loadRun(cfg, b);
  const outDir = join(cfg.artifactsDir, 'compare', `${a}__${b}`);
  await mkdir(outDir, { recursive: true });
  const browser = await chromium.launch();
  try {
    const pairs = await buildPairs(browser, cfg, A.captures, B.captures, a, b, outDir, args.all);
    let md = renderCompare(A.captures, B.captures, a, b);
    md += `\n## Side-by-side sheets\n\n${pairs.map((p) => `- \`${p}\``).join('\n')}\n`;
    await writeFile(join(outDir, 'compare.md'), md);
    console.log(`Compare: ${join(outDir, 'compare.md')} (${pairs.length} side-by-side sheets)`);
  } finally {
    await browser.close();
  }
}

async function cmdDna(args, url) {
  if (!url) throw new Error('Usage: review dna <url>');
  const [w, h] = args.viewport.split('x').map(Number);
  const host = new URL(url).hostname.replace(/[^a-z0-9.-]/gi, '_');
  const outDir = resolve(args.out || join('.uireview', 'dna', host));
  await mkdir(outDir, { recursive: true });
  const browser = await chromium.launch();
  try {
    const ctx = await browser.newContext({ viewport: { width: w, height: h }, colorScheme: args.scheme === 'dark' ? 'dark' : 'light' });
    const page = await ctx.newPage();
    await page.goto(url, { waitUntil: 'load', timeout: 45000 });
    await page.waitForTimeout(1500);
    const motion = await page.evaluate(measureMotion);
    await page.addStyleTag({ content: '*,*::before,*::after{animation-duration:0s!important;transition-duration:0s!important}' });
    await page.screenshot({ path: join(outDir, 'first-screen.png') });
    await page.screenshot({ path: join(outDir, 'full.png'), fullPage: true });
    const m = await page.evaluate(measurePage, { grid: 4 });
    await ctx.close();
    const dna = { url, viewport: [w, h], motion, metrics: m };
    await writeFile(join(outDir, 'dna.json'), JSON.stringify(dna, null, 2));
    await writeFile(join(outDir, 'dna.md'), renderDna(dna));
    console.log(`DNA: ${join(outDir, 'dna.md')} (screenshots first-screen.png, full.png)`);
  } finally {
    await browser.close();
  }
}

function renderDna({ url, viewport, motion, metrics: m }) {
  const top = (arr, n, f) => arr.slice(0, n).map(f).join(' · ');
  return `# Design DNA: ${url}

Measured at ${viewport.join('x')}. Values are what the browser computed, not what the site's CSS claims.

| Aspect | Measured |
|-|-|
| Families (declared first family; check the screenshot that it actually loaded) | ${top(m.type.families, 4, (f) => `${f.value} (${f.count})`)} |
| Font sizes in use | ${m.type.fontSizes.map((f) => f.value).sort((a, b) => parseFloat(a) - parseFloat(b)).join(' ')} |
| Weights | ${top(m.type.fontWeights, 6, (f) => `${f.value} (${f.count})`)} |
| Text colours | ${top(m.colors.text, 6, (c) => `${c.value} (${c.count})`)} |
| Surface colours by area | ${top(m.colors.background, 6, (c) => c.value)} |
| Border colours | ${top(m.colors.border, 4, (c) => c.value)} |
| Saturated fill share | ${m.colors.saturatedFillShare} of page area |
| Distinct colours | ${m.colors.distinct} |
| Radii | ${top(m.shape.radii, 6, (r) => `${r.value} (${r.count})`)} |
| Shadows | ${m.shape.shadows.length} distinct; most used: ${m.shape.shadows[0]?.value || 'none'} |
| Spacing values (most used) | ${top(m.spacing.top, 10, (s) => `${s.value} (${s.count})`)}; off a 4px grid: ${m.spacing.offGrid.length} values |
| Alignment lines | ${m.alignment.lines} |
| Filled accent actions | ${m.actions.filledActions} |
| Transition durations | ${Object.keys(motion.durations).map((d) => `${d}ms`).join(' ') || 'none'} |
| Easings | ${Object.keys(motion.easings).slice(0, 4).join(' · ') || 'none'} |
| Page size | ${m.page.width}x${m.page.height} |

Write the DNA note from this plus the screenshots: what to take, what to reject (references/inspiration-intake.md in uiux-visual-uplift).
`;
}

main().catch((e) => {
  console.error(`[review] ${e.message}`);
  process.exit(1);
});
