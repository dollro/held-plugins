/**
 * config.mjs: loads review.config.yaml, expands ${env:VAR}, applies defaults
 * and expands the capture matrix (place x state x viewport x scheme).
 */

import { readFile } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve, isAbsolute } from 'node:path';
import { parse as parseYaml } from 'yaml';

export const DEFAULT_VIEWPORTS = [
  { id: 'mobile', size: [375, 812] },
  { id: 'tablet', size: [768, 1024] },
  { id: 'desktop', size: [1440, 900] },
];

export const DEFAULT_THRESHOLDS = {
  off_token_colors: 0,
  off_token_font_sizes: 0,
  off_grid_spacing: 0,
  font_sizes_max: 8,
  font_weights_max: 4,
  font_families_max: 3,
  filled_actions_max: 1,
  alignment_near_misses: 0,
  axe_serious: 0,
  targets_below_24: 0,
  horizontal_scroll: 0,
  missing_focus: 0,
  tiny_text: 0,
  cls_max: 0.1,
  overshoot_easing: 0,
  infinite_animations: 0,
};

const DEFAULTS = {
  base_url: 'http://localhost:5173',
  dpr: 1,
  wait_for: 'networkidle',
  timeout_ms: 30000,
  settle_ms: 300,
  grid: 4,
  schemes: ['light'],
  dark_mode: 'media',
  axe: true,
  focus_stops: 12,
  artifacts: '.uireview',
};

export async function loadConfig(configPath) {
  const abs = resolve(configPath);
  if (!existsSync(abs)) {
    throw new Error(`Config not found: ${abs}. Run "review init" or copy references/review.config.example.yaml.`);
  }
  const raw = parseYaml(await readFile(abs, 'utf8')) || {};
  const cfg = { ...DEFAULTS, ...expandEnv(raw) };
  cfg._rootDir = dirname(abs);
  cfg.viewports = (cfg.viewports || DEFAULT_VIEWPORTS).map((v) => ({ id: v.id, size: v.size }));
  cfg.thresholds = { ...DEFAULT_THRESHOLDS, ...(cfg.thresholds || {}) };
  cfg.tokens = cfg.tokens || { source: 'css' };
  cfg.artifactsDir = abs2(cfg.artifacts, cfg._rootDir);
  // design-parity's auth module expects these keys.
  cfg.viewport = cfg.viewports[cfg.viewports.length - 1].size;
  if (cfg.auth && cfg.auth.mode && cfg.auth.mode !== 'none' && !cfg.auth.storage_state) {
    cfg.auth.storage_state = `${cfg.artifacts}/auth.json`;
  }
  if (!Array.isArray(cfg.places) || !cfg.places.length) throw new Error('Config needs at least one entry under places:');
  for (const p of cfg.places) {
    if (!p.id || !p.path) throw new Error(`Every place needs id and path (got ${JSON.stringify(p)})`);
    p.states = p.states && p.states.length ? p.states : [{ id: 'default' }];
    if (!p.states.some((s) => s.id === 'default')) p.states.unshift({ id: 'default' });
  }
  return cfg;
}

/**
 * The default state runs on every viewport and scheme; other states on the
 * widest viewport and first scheme unless they list their own.
 */
export function expandMatrix(cfg, filter = {}) {
  const widest = cfg.viewports[cfg.viewports.length - 1].id;
  const out = [];
  for (const place of cfg.places) {
    if (filter.place && place.id !== filter.place) continue;
    for (const state of place.states) {
      if (filter.state && state.id !== filter.state) continue;
      const vps = state.viewports || (state.id === 'default' ? cfg.viewports.map((v) => v.id) : [widest]);
      const schemes = state.schemes || (state.id === 'default' ? cfg.schemes : [cfg.schemes[0]]);
      for (const vpId of vps) {
        const vp = cfg.viewports.find((v) => v.id === vpId);
        if (!vp) throw new Error(`Place ${place.id}, state ${state.id}: unknown viewport ${vpId}`);
        for (const scheme of schemes) out.push({ place, state, viewport: vp, scheme, id: `${place.id}/${state.id}/${vp.id}-${scheme}` });
      }
    }
  }
  return out;
}

export function joinUrl(base, path) {
  if (/^https?:|^file:/.test(path)) return path;
  return base.replace(/\/+$/, '') + (path.startsWith('/') ? path : '/' + path);
}

function abs2(p, root) {
  return isAbsolute(p) ? p : resolve(root, p);
}

function expandEnv(node) {
  if (typeof node === 'string') return node.replace(/\$\{env:([A-Z0-9_]+)\}/gi, (_, n) => process.env[n] ?? '');
  if (Array.isArray(node)) return node.map(expandEnv);
  if (node && typeof node === 'object') return Object.fromEntries(Object.entries(node).map(([k, v]) => [k, expandEnv(v)]));
  return node;
}

/** Reads a W3C DTCG token file into the same shape tokensFromPage returns (lengths in px, colours as strings). */
export async function tokensFromDtcg(paths, rootDir) {
  const flat = {};
  const walk = (node, path, inheritedType) => {
    if (!node || typeof node !== 'object') return;
    const type = node.$type || inheritedType;
    if ('$value' in node) {
      flat[path.join('.')] = { value: node.$value, type };
      return;
    }
    for (const [k, v] of Object.entries(node)) if (!k.startsWith('$')) walk(v, [...path, k], type);
  };
  for (const p of [].concat(paths)) walk(JSON.parse(await readFile(abs2(p, rootDir), 'utf8')), [], undefined);
  const resolveAlias = (v, depth = 0) => {
    if (typeof v === 'string' && /^\{.+\}$/.test(v) && depth < 10) {
      const t = flat[v.slice(1, -1)];
      return t ? resolveAlias(t.value, depth + 1) : null;
    }
    return v;
  };
  const out = { colors: [], lengths: [], shadows: [], rawColors: [] };
  for (const [name, t] of Object.entries(flat)) {
    const v = resolveAlias(t.value);
    if (v == null) continue;
    if (t.type === 'color') {
      const s = typeof v === 'string' ? v : v.hex || null;
      if (s) out.rawColors.push({ name, value: s });
    } else if (t.type === 'dimension') {
      const s = typeof v === 'string' ? v : `${v.value}${v.unit}`;
      const m = String(s).match(/^(-?[\d.]+)(px|rem)$/);
      if (m) out.lengths.push({ name, px: m[2] === 'px' ? +m[1] : +m[1] * 16 });
    }
  }
  return out;
}
