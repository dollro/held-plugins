/**
 * config.mjs — loads parity.config.yaml and parity.rubric.yaml, expands
 * ${env:VAR} references, validates the schema, and normalizes per-screen
 * targets into a uniform shape.
 */

import { readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve, isAbsolute } from 'node:path';
import { parse as parseYaml } from 'yaml';
import { PNG } from 'pngjs';

const DEFAULTS = {
  runtime: 'auto',
  base_url: 'http://localhost:3000',
  viewport: [1440, 900],
  dpr: 1,
  wait_for: 'networkidle',
  timeout_ms: 30000,
  artifacts: { root: '.parity', keep_iterations: 10 },
};

export async function loadConfig(configPath) {
  const abs = resolve(configPath);
  if (!existsSync(abs)) {
    throw new Error(`Config not found: ${abs}. Copy references/parity.config.example.yaml to parity.config.yaml.`);
  }
  const raw = await readFile(abs, 'utf8');
  const parsed = parseYaml(raw) || {};
  const expanded = expandEnv(parsed);
  const cfg = mergeDefaults(expanded);
  const rootDir = dirname(abs);

  for (const screen of cfg.screens || []) {
    normalizeScreen(screen, cfg, rootDir);
  }

  if (cfg.rubric && typeof cfg.rubric === 'string') {
    const rubricPath = resolvePath(cfg.rubric, rootDir);
    if (existsSync(rubricPath)) {
      cfg.rubric = parseYaml(await readFile(rubricPath, 'utf8')) || {};
    } else {
      cfg.rubric = {};
    }
  } else {
    cfg.rubric = cfg.rubric || {};
  }

  cfg._configPath = abs;
  cfg._rootDir = rootDir;
  return cfg;
}

function mergeDefaults(cfg) {
  const out = { ...DEFAULTS, ...cfg };
  out.artifacts = { ...DEFAULTS.artifacts, ...(cfg.artifacts || {}) };
  return out;
}

function resolvePath(p, rootDir) {
  return isAbsolute(p) ? p : resolve(rootDir, p);
}

function normalizeScreen(screen, cfg, rootDir) {
  if (!screen.id) throw new Error('Every screen needs an id');

  // Normalize target into {kind: 'html'|'png', path, selector?}
  const t = screen.target;
  if (!t) throw new Error(`Screen ${screen.id} has no target`);

  if (typeof t === 'string') {
    const p = resolvePath(t, rootDir);
    screen._target = {
      kind: p.toLowerCase().endsWith('.png') ? 'png' : 'html',
      path: p,
    };
  } else if (typeof t === 'object') {
    if (t.html) {
      screen._target = {
        kind: 'html',
        path: resolvePath(t.html, rootDir),
        selector: t.selector || null,
      };
    } else if (t.png) {
      screen._target = {
        kind: 'png',
        path: resolvePath(t.png, rootDir),
      };
    } else {
      throw new Error(`Screen ${screen.id} target must have html or png`);
    }
  }

  // Normalize masks into [{kind: 'selector'|'region'|'text', ...}]
  screen._masks = normalizeMasks(screen.mask || []);

  // Resolve the impl URL
  const base = screen.base_url || cfg.base_url;
  screen._url = joinUrl(base, screen.path || '/');
  screen._viewport = screen.viewport || cfg.viewport;
  screen._dpr = screen.dpr ?? cfg.dpr;
}

function normalizeMasks(masks) {
  return masks.map(m => {
    if (typeof m === 'string') return { kind: 'selector', value: m };
    if (m.selector) return { kind: 'selector', value: m.selector };
    if (m.region) {
      const [x, y, w, h] = m.region;
      return { kind: 'region', x, y, w, h };
    }
    if (m.text) return { kind: 'text', pattern: m.text };
    throw new Error(`Unknown mask entry: ${JSON.stringify(m)}`);
  });
}

function joinUrl(base, path) {
  const b = base.replace(/\/+$/, '');
  const p = path.startsWith('/') ? path : '/' + path;
  return b + p;
}

// Resolve PNG dims and override viewport if the caller didn't set one explicitly.
export async function resolveViewportForScreen(screen, { strict = false } = {}) {
  if (screen._target.kind !== 'png') return screen._viewport;

  const pngDims = await readPngDims(screen._target.path);
  const vp = screen._viewport;
  const matches = vp[0] === pngDims.width && vp[1] === pngDims.height;

  if (matches) return vp;

  if (strict) {
    throw new Error(
      `Screen ${screen.id}: PNG is ${pngDims.width}×${pngDims.height} but viewport is ${vp[0]}×${vp[1]}. ` +
      `Remove the viewport override or drop --strict.`
    );
  }

  // Auto-match PNG dims. Warn if the user explicitly set a different viewport.
  if (screen.viewport || screen.viewport) {
    process.stderr.write(
      `[parity] ${screen.id}: auto-matching viewport ${vp[0]}×${vp[1]} → ${pngDims.width}×${pngDims.height} to match PNG\n`
    );
  }
  return [pngDims.width, pngDims.height];
}

async function readPngDims(path) {
  const buf = await readFile(path);
  const png = PNG.sync.read(buf);
  return { width: png.width, height: png.height };
}

function expandEnv(node) {
  if (typeof node === 'string') {
    return node.replace(/\$\{env:([A-Z0-9_]+)\}/gi, (_, name) => process.env[name] ?? '');
  }
  if (Array.isArray(node)) return node.map(expandEnv);
  if (node && typeof node === 'object') {
    const out = {};
    for (const [k, v] of Object.entries(node)) out[k] = expandEnv(v);
    return out;
  }
  return node;
}
