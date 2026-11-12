#!/usr/bin/env node
/**
 * parity.mjs — single entry point for a config-driven parity run.
 *
 *   parity run [--screen <id>] [--strict] [--iteration <n>]
 *     Execute the full loop (prepare target → screenshot impl → diff) for
 *     every screen in parity.config.yaml, or just one.
 *
 *   parity plan [--screen <id>]
 *     Emit an MCP tool-call plan for each screen (when runtime is mcp-*).
 *
 *   parity auth
 *     Perform the configured auth flow (headless) and persist storageState.
 *
 *   parity init
 *     Scaffold parity.config.yaml + parity.rubric.yaml + .parity/.gitignore.
 *
 * Config path defaults to ./parity.config.yaml; override with --config <path>.
 */

import { parseArgs } from 'node:util';
import { readFile, writeFile, mkdir, copyFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve, relative, join } from 'node:path';
import { execSync, spawnSync } from 'node:child_process';
import { loadConfig, resolveViewportForScreen } from './lib/config.mjs';
import { detectRuntime } from './lib/detect-runtime.mjs';
import { buildScreenPlan } from './lib/mcp-plan.mjs';

const HERE = dirname(new URL(import.meta.url).pathname);

async function main() {
  const cmd = process.argv[2];
  const rest = process.argv.slice(3);

  const { values: args, positionals } = parseArgs({
    args: rest,
    options: {
      config: { type: 'string', default: 'parity.config.yaml' },
      screen: { type: 'string' },
      iteration: { type: 'string' },
      strict: { type: 'boolean', default: false },
      'plan-only': { type: 'boolean', default: false },
    },
    allowPositionals: true,
  });

  if (!cmd || cmd === '--help' || cmd === '-h') return usage(0);
  if (cmd === 'init') return cmdInit(args);

  const cfg = await loadConfig(args.config);
  const runtime = detectRuntime(cfg.runtime);
  const screens = args.screen
    ? cfg.screens.filter(s => s.id === args.screen)
    : cfg.screens;
  if (args.screen && !screens.length) throw new Error(`No screen with id ${args.screen}`);

  switch (cmd) {
    case 'run':   return cmdRun(cfg, runtime, screens, args);
    case 'plan':  return cmdPlan(cfg, runtime, screens, args);
    case 'auth':  return cmdAuth(cfg);
    default:      return usage(1);
  }
}

function usage(code) {
  process.stderr.write(`Usage:
  parity run   [--screen <id>] [--strict] [--config <path>]
  parity plan  [--screen <id>] [--config <path>]
  parity auth  [--config <path>]
  parity init  [--config <path>]
`);
  process.exit(code);
}

// -----------------------------------------------------------------------------
// run — executes the Node-Playwright path end-to-end
// -----------------------------------------------------------------------------

async function cmdRun(cfg, runtime, screens, args) {
  if (runtime !== 'node-playwright') {
    process.stderr.write(
      `[parity] runtime is ${runtime} — emitting plan instead of executing.\n` +
      `         Run \`parity plan\` and execute the plan via your MCP tool-use loop.\n`
    );
    return cmdPlan(cfg, runtime, screens, args);
  }

  const iteration = args.iteration ? Number(args.iteration) : await nextIteration(cfg, screens[0]?.id || 'run');
  const results = [];

  for (const screen of screens) {
    process.stderr.write(`[parity] ${screen.id} · iteration ${iteration}\n`);

    const viewport = await resolveViewportForScreen(screen, { strict: args.strict });
    const runRoot = join(cfg._rootDir, cfg.artifacts.root, 'runs', screen.id, `iteration_${iteration}`);
    await mkdir(runRoot, { recursive: true });

    // Fixtures
    if (screen.fixtures?.length) await runFixtures(cfg, screen.fixtures);

    // Target
    const targetOut = join(runRoot, 'target.png');
    await prepareTarget(screen, targetOut, viewport);

    // Implementation
    const implOut = join(runRoot, 'impl.png');
    await screenshotImpl(cfg, screen, implOut, viewport);

    // Diff
    const diffOut = join(runRoot, 'diff.png');
    const diffResult = await runDiff(targetOut, implOut, diffOut, cfg.rubric);

    results.push({
      screen: screen.id,
      iteration,
      artifacts: {
        target: relative(cfg._rootDir, targetOut),
        impl:   relative(cfg._rootDir, implOut),
        diff:   relative(cfg._rootDir, diffOut),
      },
      diff: diffResult,
    });

    await writeFile(
      join(runRoot, 'run.json'),
      JSON.stringify({ screen: screen.id, iteration, viewport, diff: diffResult }, null, 2)
    );
  }

  process.stdout.write(JSON.stringify({ iteration, results }, null, 2) + '\n');
}

// -----------------------------------------------------------------------------
// plan — emits MCP tool-call plan(s) as JSON
// -----------------------------------------------------------------------------

async function cmdPlan(cfg, runtime, screens, args) {
  const iteration = args.iteration ? Number(args.iteration) : await nextIteration(cfg, screens[0]?.id || 'run');
  const plans = [];

  for (const screen of screens) {
    const viewport = await resolveViewportForScreen(screen, { strict: args.strict });
    const runRoot = join(cfg._rootDir, cfg.artifacts.root, 'runs', screen.id, `iteration_${iteration}`);

    const target = {
      needsCapture: screen._target.kind === 'html',
      url: screen._target.kind === 'html' ? pathToFileUrl(screen._target.path) : null,
      selector: screen._target.selector,
      out: join(runRoot, 'target.png'),
      pngSource: screen._target.kind === 'png' ? screen._target.path : null,
    };

    const impl = {
      url: screen._url,
      out: join(runRoot, 'impl.png'),
      storageState: screen.requires_auth && cfg.auth?.storage_state
        ? relative(cfg._rootDir, resolve(cfg._rootDir, cfg.auth.storage_state))
        : null,
    };

    const plan = buildScreenPlan({ screen, runtime, impl, target, rootDir: cfg._rootDir, viewport });
    if (target.pngSource) {
      plan.pre_steps = [{ op: 'copy', from: relative(cfg._rootDir, target.pngSource), to: relative(cfg._rootDir, target.out) }];
    }
    plans.push(plan);
  }

  process.stdout.write(JSON.stringify({ iteration, runtime, plans }, null, 2) + '\n');
}

// -----------------------------------------------------------------------------
// auth — runs configured auth and persists storageState
// -----------------------------------------------------------------------------

async function cmdAuth(cfg) {
  const runtime = detectRuntime(cfg.runtime);
  if (runtime !== 'node-playwright') {
    throw new Error(
      `auth subcommand requires node-playwright runtime. Current runtime: ${runtime}. ` +
      `For MCP runtimes, trigger your app's login flow via the MCP tools directly.`
    );
  }
  const { chromium } = await import('playwright');
  const { ensureAuth } = await import('./lib/auth.mjs');
  const browser = await chromium.launch({ headless: true });
  try {
    const result = await ensureAuth(browser, cfg);
    process.stdout.write(JSON.stringify({ ok: true, result }, null, 2) + '\n');
  } finally {
    await browser.close();
  }
}

// -----------------------------------------------------------------------------
// init — scaffold config + rubric + .parity gitignore
// -----------------------------------------------------------------------------

async function cmdInit(args) {
  const cfgPath = resolve(args.config);
  const rubricPath = resolve(dirname(cfgPath), 'parity.rubric.yaml');
  const parityDir = resolve(dirname(cfgPath), '.parity');
  const gitignore = join(parityDir, '.gitignore');

  await mkdir(parityDir, { recursive: true });

  if (!existsSync(cfgPath)) {
    await copyFile(join(HERE, '..', 'references', 'parity.config.example.yaml'), cfgPath);
    process.stderr.write(`[parity] wrote ${relative(process.cwd(), cfgPath)}\n`);
  }
  if (!existsSync(rubricPath)) {
    await copyFile(join(HERE, '..', 'references', 'parity.rubric.example.yaml'), rubricPath);
    process.stderr.write(`[parity] wrote ${relative(process.cwd(), rubricPath)}\n`);
  }
  if (!existsSync(gitignore)) {
    await writeFile(gitignore, '# everything under .parity/ is a transient audit trail + deps\n*\n!.gitignore\n');
    process.stderr.write(`[parity] wrote ${relative(process.cwd(), gitignore)}\n`);
  }
}

// -----------------------------------------------------------------------------
// Helpers (node-playwright path)
// -----------------------------------------------------------------------------

async function prepareTarget(screen, outPath, viewport) {
  const t = screen._target;
  if (t.kind === 'png') {
    await mkdir(dirname(outPath), { recursive: true });
    await copyFile(t.path, outPath);
    return;
  }

  // HTML: render via screenshot.mjs. Selector → partial capture.
  const url = pathToFileUrl(t.path);
  const argv = [
    'screenshot.mjs',
    '--url', url,
    '--viewport', `${viewport[0]}x${viewport[1]}`,
    '--out', outPath,
  ];
  if (t.selector) argv.push('--selector', t.selector);
  runNode(argv);
}

async function screenshotImpl(cfg, screen, outPath, viewport) {
  const argv = [
    'screenshot.mjs',
    '--url', screen._url,
    '--viewport', `${viewport[0]}x${viewport[1]}`,
    '--dpr', String(screen._dpr),
    '--out', outPath,
    '--wait-for', cfg.wait_for,
  ];

  if (screen.requires_auth && cfg.auth?.storage_state) {
    const ss = resolve(cfg._rootDir, cfg.auth.storage_state);
    if (!existsSync(ss)) {
      // Run auth first
      await cmdAuth(cfg);
    }
    argv.push('--storage-state', ss);
  }

  for (const m of screen._masks) {
    if (m.kind === 'selector') argv.push('--mask', m.value);
    else if (m.kind === 'region') argv.push('--mask-region', `${m.x},${m.y},${m.w},${m.h}`);
    else if (m.kind === 'text') argv.push('--mask-text', m.pattern);
  }

  runNode(argv);
}

async function runDiff(base, impl, out, rubric) {
  const threshold = String(rubric?.color?.delta_e_threshold ? 0.1 : 0.1);
  const res = spawnSync('node', [
    join(HERE, 'diff.mjs'),
    '--base', base,
    '--compare', impl,
    '--out', out,
    '--threshold', threshold,
  ], { encoding: 'utf8' });
  if (res.status !== null && res.status > 1) {
    throw new Error(`diff.mjs failed: ${res.stderr}`);
  }
  try {
    return JSON.parse(res.stdout);
  } catch {
    return { raw: res.stdout, stderr: res.stderr };
  }
}

async function runFixtures(cfg, names) {
  for (const name of names) {
    const fx = cfg.fixtures?.[name];
    if (!fx) throw new Error(`Unknown fixture: ${name}`);
    if (fx.seed) {
      process.stderr.write(`[parity] fixture ${name}: ${fx.seed}\n`);
      execSync(fx.seed, { cwd: cfg._rootDir, stdio: 'inherit' });
    }
  }
}

function runNode(argv) {
  const res = spawnSync('node', [join(HERE, argv[0]), ...argv.slice(1)], {
    stdio: 'inherit',
  });
  if (res.status !== 0) {
    throw new Error(`${argv[0]} exited with ${res.status}`);
  }
}

function pathToFileUrl(p) {
  return 'file://' + resolve(p);
}

async function nextIteration(cfg, screenId) {
  if (!screenId) return 1;
  const dir = join(cfg._rootDir, cfg.artifacts.root, 'runs', screenId);
  if (!existsSync(dir)) return 1;
  const { readdir } = await import('node:fs/promises');
  const entries = await readdir(dir).catch(() => []);
  const nums = entries
    .map(e => /^iteration_(\d+)$/.exec(e)?.[1])
    .filter(Boolean)
    .map(Number);
  return nums.length ? Math.max(...nums) + 1 : 1;
}

main().catch(err => {
  console.error(`parity: ${err.message}`);
  process.exit(1);
});
