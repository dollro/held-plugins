/**
 * page-measure.mjs: functions that run INSIDE the page via page.evaluate().
 *
 * Playwright serialises each function with toString(), so every function here
 * must be self-contained: no imports, no references to module scope.
 */

/** Installed with addInitScript before navigation: collects CLS and LCP. */
export function installPerfObservers() {
  window.__uir = { cls: 0, lcp: 0 };
  try {
    new PerformanceObserver((list) => {
      for (const e of list.getEntries()) if (!e.hadRecentInput) window.__uir.cls += e.value;
    }).observe({ type: 'layout-shift', buffered: true });
  } catch {}
  try {
    new PerformanceObserver((list) => {
      const es = list.getEntries();
      if (es.length) window.__uir.lcp = es[es.length - 1].startTime;
    }).observe({ type: 'largest-contentful-paint', buffered: true });
  } catch {}
}

/**
 * Reads the design tokens the page defines as CSS custom properties and
 * classifies them into colours, lengths and shadows, resolved for the current
 * colour scheme.
 */
export function tokensFromPage(opts) {
  const { prefixes = [], exclude = [] } = opts || {};
  const root = document.documentElement;
  const rootFont = parseFloat(getComputedStyle(root).fontSize) || 16;
  const names = new Set();

  const walk = (rules) => {
    for (const rule of rules) {
      if (rule.style) {
        for (let i = 0; i < rule.style.length; i++) {
          const p = rule.style[i];
          if (p.startsWith('--')) names.add(p);
        }
      }
      if (rule.cssRules) walk(rule.cssRules);
    }
  };
  for (const sheet of document.styleSheets) {
    try { walk(sheet.cssRules); } catch { /* cross-origin sheet */ }
  }

  const probe = document.createElement('div');
  probe.style.cssText = 'position:absolute;visibility:hidden;pointer-events:none';
  document.body.appendChild(probe);

  // Chromium serialises relative colours as color(srgb 0..1), plain ones as rgb(0..255).
  const parseRgb = (s) => {
    const m = s && s.match(/-?[\d.]+(e-?\d+)?/g);
    if (!m || m.length < 3) return null;
    const k = /^color\(srgb/.test(s) ? 255 : 1;
    const c = (v) => Math.max(0, Math.min(255, Math.round(parseFloat(v) * k)));
    return { r: c(m[0]), g: c(m[1]), b: c(m[2]) };
  };
  const toRgb = (str) => {
    probe.style.color = '';
    probe.style.color = `rgb(from ${str} r g b)`;
    if (!probe.style.color) return null;
    return parseRgb(getComputedStyle(probe).color);
  };

  const keep = (n) =>
    (!prefixes.length || prefixes.some((p) => n.startsWith(p))) &&
    !exclude.some((p) => n.startsWith(p));

  const out = { colors: [], lengths: [], shadows: [], count: 0 };
  for (const name of names) {
    if (!keep(name)) continue;
    const v = getComputedStyle(root).getPropertyValue(name).trim();
    if (!v) continue;
    out.count++;
    const len = v.match(/^(-?[\d.]+)(px|rem|em)$/);
    if (len) {
      const n = parseFloat(len[1]);
      out.lengths.push({ name, px: +(len[2] === 'px' ? n : n * rootFont).toFixed(2) });
      continue;
    }
    if (/^-?[\d.]+$/.test(v)) continue;
    if (CSS.supports('color', v)) {
      const rgb = toRgb(v);
      if (rgb) out.colors.push({ name, ...rgb });
      continue;
    }
    if (/\d/.test(v) && CSS.supports('box-shadow', v)) {
      probe.style.boxShadow = v;
      out.shadows.push({ name, value: getComputedStyle(probe).boxShadow.replace(/\s+/g, ' ') });
      probe.style.boxShadow = '';
    }
  }
  probe.remove();
  return out;
}

/** Transitions and animations, measured BEFORE animations are frozen. */
export function measureMotion() {
  const durations = {};
  const easings = {};
  let slow = 0;
  let overshoot = 0;
  const samples = [];
  const toMs = (s) => (s.endsWith('ms') ? parseFloat(s) : parseFloat(s) * 1000);
  const isOvershoot = (fn) => {
    const m = fn.match(/cubic-bezier\(([^)]+)\)/);
    if (!m) return false;
    const [, y1, , y2] = m[1].split(',').map(Number);
    return y1 < 0 || y1 > 1 || y2 < 0 || y2 > 1;
  };
  for (const el of document.body.querySelectorAll('*')) {
    const cs = getComputedStyle(el);
    if (cs.transitionProperty === 'none') continue;
    const ds = cs.transitionDuration.split(',').map((s) => toMs(s.trim()));
    const max = Math.max(...ds);
    if (!(max > 0)) continue;
    durations[max] = (durations[max] || 0) + 1;
    for (const fn of cs.transitionTimingFunction.split(/,(?![^(]*\))/).map((s) => s.trim())) {
      easings[fn] = (easings[fn] || 0) + 1;
      if (isOvershoot(fn) || fn.startsWith('linear(')) {
        overshoot++;
        if (samples.length < 5) samples.push({ kind: 'overshoot-easing', value: fn, el: el.tagName.toLowerCase() + (el.className && typeof el.className === 'string' ? '.' + el.className.trim().split(/\s+/).slice(0, 2).join('.') : '') });
      }
    }
    if (max > 500) {
      slow++;
      if (samples.length < 5) samples.push({ kind: 'slow-transition', value: `${max}ms`, el: el.tagName.toLowerCase() });
    }
  }
  const anims = document.getAnimations().filter((a) => a.playState === 'running');
  const infinite = anims.filter((a) => a.effect && a.effect.getTiming().iterations === Infinity).length;
  return { durations, easings, slow, overshoot, runningAnimations: anims.length, infiniteAnimations: infinite, samples };
}

/**
 * The measured layer: token conformance, typography, spacing rhythm,
 * alignment, colour use, targets, overflow. Runs after stabilisation.
 */
export function measurePage(opts) {
  const { grid = 4, tokens = null, ignore = [], primarySelector = null, scope = null, colorTolerance = 3, nearTolerance = 20 } = opts || {};
  const vw = window.innerWidth;
  const doc = document.documentElement;

  // ---------- helpers ----------
  const probe = document.createElement('div');
  probe.style.cssText = 'position:absolute;visibility:hidden;pointer-events:none';
  document.body.appendChild(probe);
  const cache = new Map();
  const parseNums = (s) => (s.match(/-?[\d.]+(e-?\d+)?/g) || []).map(parseFloat);
  const toRgba = (str) => {
    if (!str || str === 'transparent') return null;
    if (cache.has(str)) return cache.get(str);
    let out = null;
    probe.style.color = '';
    probe.style.color = `rgb(from ${str} r g b / alpha)`;
    if (probe.style.color) {
      const cs = getComputedStyle(probe).color;
      const n = parseNums(cs);
      if (n.length >= 3) {
        const k = /^color\(srgb/.test(cs) ? 255 : 1;
        const c = (v) => Math.max(0, Math.min(255, Math.round(v * k)));
        out = { r: c(n[0]), g: c(n[1]), b: c(n[2]), a: n.length > 3 ? +n[3].toFixed(2) : 1 };
      }
    }
    cache.set(str, out);
    return out;
  };
  const key = (c) => `rgb(${c.r} ${c.g} ${c.b})`;
  const dist = (a, b) => Math.sqrt((a.r - b.r) ** 2 + (a.g - b.g) ** 2 + (a.b - b.b) ** 2);
  const label = (el) => {
    let s = el.tagName.toLowerCase();
    if (el.id) return `${s}#${el.id}`;
    const cls = typeof el.className === 'string' ? el.className.trim().split(/\s+/).filter(Boolean).slice(0, 3) : [];
    if (cls.length) s += '.' + cls.join('.');
    const role = el.getAttribute('role');
    if (role) s += `[role=${role}]`;
    const txt = (el.innerText || el.getAttribute('aria-label') || '').trim().replace(/\s+/g, ' ').slice(0, 30);
    return txt ? `${s} "${txt}"` : s;
  };
  const hist = () => new Map();
  const bump = (h, k, el, area = 0) => {
    const e = h.get(k) || { count: 0, area: 0, sample: label(el) };
    e.count++;
    e.area += area;
    h.set(k, e);
  };
  const histOut = (h, sortBy = 'count') =>
    [...h.entries()].map(([value, e]) => ({ value, ...e, area: Math.round(e.area) })).sort((a, b) => b[sortBy] - a[sortBy]);

  const ignored = ignore.length ? [...document.querySelectorAll(ignore.join(','))] : [];
  const isIgnored = (el) => ignored.some((i) => i === el || i.contains(el));
  const visible = (el, cs, r) =>
    r.width >= 1 && r.height >= 1 && cs.visibility !== 'hidden' && cs.display !== 'none' && parseFloat(cs.opacity) > 0.01;
  const ownText = (el) => {
    for (const n of el.childNodes) if (n.nodeType === 3 && n.nodeValue.trim()) return n;
    return null;
  };
  const INTERACTIVE = 'a[href],button,input:not([type=hidden]),select,textarea,summary,[role=button],[role=link],[role=tab],[role=menuitem],[role=checkbox],[role=radio],[role=switch],[role=option],[tabindex]:not([tabindex="-1"])';
  const tokenLengths = tokens ? tokens.lengths.map((t) => t.px) : [];
  const nearestColor = (c) => {
    let best = null;
    for (const t of tokens.colors) {
      const d = dist(c, t);
      if (!best || d < best.d) best = { d, name: t.name };
    }
    return best;
  };

  // ---------- collections ----------
  const colors = { text: hist(), background: hist(), border: hist() };
  const fontSizes = hist(), fontWeights = hist(), families = hist(), textStyles = hist();
  const radii = hist(), shadows = hist(), spacing = hist();
  const edges = new Map();
  const tinyText = [], smallTargets = [], warnTargets = [], truncated = [], overflowRight = [], longLines = [];
  let filledActions = 0, tinyCount = 0;
  const filledActionSamples = [];
  let saturatedArea = 0;
  const pageArea = Math.max(1, doc.scrollWidth * doc.scrollHeight);

  // scope: measure only inside this element (a dialog, a drawer); falls back to the whole page.
  const scopeEl = scope ? document.querySelector(scope) : null;
  const all = scopeEl ? scopeEl.querySelectorAll('*') : [document.body, ...document.body.querySelectorAll('*')];
  for (const el of all) {
    if (el instanceof SVGElement && el.tagName.toLowerCase() !== 'svg') continue;
    if (['SCRIPT', 'STYLE', 'NOSCRIPT', 'TEMPLATE', 'BR', 'WBR'].includes(el.tagName)) continue;
    if (el === probe || isIgnored(el)) continue;
    const cs = getComputedStyle(el);
    const r = el.getBoundingClientRect();
    if (!visible(el, cs, r)) continue;
    const area = r.width * r.height;

    // background and borders
    const bg = toRgba(cs.backgroundColor);
    if (bg && bg.a > 0) {
      bump(colors.background, key(bg), el, area);
      const max = Math.max(bg.r, bg.g, bg.b), min = Math.min(bg.r, bg.g, bg.b);
      const sat = max === 0 ? 0 : (max - min) / max;
      if (sat > 0.35 && max > 50 && bg.a > 0.5) saturatedArea += area;
    }
    for (const side of ['Top', 'Right', 'Bottom', 'Left']) {
      if (parseFloat(cs[`border${side}Width`]) > 0 && !['none', 'hidden'].includes(cs[`border${side}Style`])) {
        const bc = toRgba(cs[`border${side}Color`]);
        if (bc && bc.a > 0) bump(colors.border, key(bc), el, 0);
      }
    }

    // radius and shadow
    const rad = Math.max(...['TopLeft', 'TopRight', 'BottomRight', 'BottomLeft'].map((c) => parseFloat(cs[`border${c}Radius`]) || 0));
    if (rad > 0) bump(radii, rad >= Math.min(r.width, r.height) / 2 - 1 ? 'full' : `${+rad.toFixed(2)}px`, el);
    if (cs.boxShadow && cs.boxShadow !== 'none') bump(shadows, cs.boxShadow.replace(/\s+/g, ' '), el);

    // spacing rhythm: padding, gap, vertical margins
    // Vertical margins count for rhythm, except on positioned layers and auto-centred boxes.
    const sp = [cs.paddingTop, cs.paddingRight, cs.paddingBottom, cs.paddingLeft];
    if (!/fixed|absolute/.test(cs.position) && el.tagName !== 'DIALOG') {
      for (const v of [cs.marginTop, cs.marginBottom]) if (parseFloat(v) <= 160) sp.push(v);
    }
    if (/flex|grid/.test(cs.display)) sp.push(cs.rowGap, cs.columnGap);
    for (const v of sp) {
      const n = parseFloat(v);
      if (n > 0) bump(spacing, +n.toFixed(2), el);
    }

    // text
    const tn = ownText(el);
    if (tn) {
      const tc = toRgba(cs.color);
      if (tc) bump(colors.text, key(tc), el, 0);
      const fs = parseFloat(cs.fontSize);
      bump(fontSizes, fs, el);
      bump(fontWeights, cs.fontWeight, el);
      bump(families, cs.fontFamily.split(',')[0].replace(/["']/g, '').trim(), el);
      bump(textStyles, `${fs}px/${cs.lineHeight} ${cs.fontWeight}`, el);
      if (fs < 12) {
        tinyCount++;
        if (tinyText.length < 10) tinyText.push({ el: label(el), size: fs });
      }
      const range = document.createRange();
      range.selectNodeContents(tn);
      const tr = range.getBoundingClientRect();
      if (tr.width > 0 && tr.left >= 0 && tr.left <= vw) {
        const x = Math.round(tr.left);
        const e = edges.get(x) || { count: 0, sample: label(el) };
        e.count++;
        edges.set(x, e);
      }
      const text = el.innerText || '';
      if (text.length > 160 && cs.display !== 'inline') {
        const chars = r.width / (fs * 0.5);
        if (chars > 90 && longLines.length < 10) longLines.push({ el: label(el), approxChars: Math.round(chars) });
      }
      if ((cs.overflow !== 'visible' || cs.textOverflow === 'ellipsis') && el.scrollWidth > el.clientWidth + 1) {
        if (truncated.length < 10) truncated.push({ el: label(el) });
      }
    }

    // interactive targets
    if (el.matches(INTERACTIVE)) {
      const inlineLink = el.tagName === 'A' && cs.display === 'inline' && el.parentElement && (el.parentElement.innerText || '').length > (el.innerText || '').length + 20;
      const m = Math.min(r.width, r.height);
      if (!inlineLink) {
        if (m < 24) smallTargets.push({ el: label(el), size: `${Math.round(r.width)}x${Math.round(r.height)}` });
        else if (m < 44) warnTargets.push({ el: label(el), size: `${Math.round(r.width)}x${Math.round(r.height)}` });
      }
      if (!tn) {
        const x = Math.round(r.left);
        if (x >= 0 && x <= vw) {
          const e = edges.get(x) || { count: 0, sample: label(el) };
          e.count++;
          edges.set(x, e);
        }
      }
      if (!primarySelector && bg && bg.a > 0.5) {
        const max = Math.max(bg.r, bg.g, bg.b), min = Math.min(bg.r, bg.g, bg.b);
        if (max > 50 && (max - min) / max > 0.35 && el.matches('button,a,[role=button],input[type=submit]')) {
          filledActions++;
          if (filledActionSamples.length < 6) filledActionSamples.push(label(el));
        }
      }
    }

    if (r.right > vw + 1 && cs.position !== 'fixed' && overflowRight.length < 10) {
      let p = el.parentElement, clipped = false;
      while (p && p !== document.body) {
        const pcs = getComputedStyle(p);
        if (/auto|scroll|hidden|clip/.test(pcs.overflowX)) { clipped = true; break; }
        p = p.parentElement;
      }
      if (!clipped) overflowRight.push({ el: label(el), right: Math.round(r.right) });
    }
  }

  if (primarySelector) {
    const prim = [...document.querySelectorAll(primarySelector)].filter((el) => {
      const r = el.getBoundingClientRect();
      return r.width > 0 && r.height > 0 && getComputedStyle(el).visibility !== 'hidden';
    });
    filledActions = prim.length;
    filledActionSamples.push(...prim.slice(0, 6).map(label));
  }

  // ---------- alignment ----------
  const xs = [...edges.entries()].filter(([, e]) => e.count >= 2).sort((a, b) => a[0] - b[0]);
  const nearMisses = [];
  for (let i = 1; i < xs.length; i++) {
    const d = xs[i][0] - xs[i - 1][0];
    if (d > 0 && d <= 3) nearMisses.push({ x: [xs[i - 1][0], xs[i][0]], samples: [xs[i - 1][1].sample, xs[i][1].sample] });
  }

  // ---------- token conformance ----------
  let tokenCheck = null;
  if (tokens && (tokens.colors.length || tokens.lengths.length)) {
    const offColors = [], nearColors = [];
    if (tokens.colors.length) {
      for (const [role, h] of Object.entries(colors)) {
        for (const [k, e] of h.entries()) {
          const [r, g, b] = k.match(/\d+/g).map(Number);
          const best = nearestColor({ r, g, b });
          if (best.d <= colorTolerance) continue;
          const item = { role, value: k, count: e.count, sample: e.sample, nearest: best.name, distance: Math.round(best.d) };
          (best.d <= nearTolerance ? nearColors : offColors).push(item);
        }
      }
    }
    const offLen = (h) =>
      tokenLengths.length
        ? [...h.entries()].filter(([v]) => typeof v === 'number' && !tokenLengths.some((t) => Math.abs(t - v) < 0.26)).map(([v, e]) => ({ value: `${v}px`, count: e.count, sample: e.sample }))
        : [];
    const radiusNums = new Map([...radii.entries()].filter(([k]) => k !== 'full').map(([k, e]) => [parseFloat(k), e]));
    const tokenShadows = new Set((tokens.shadows || []).map((s) => s.value));
    tokenCheck = {
      colorTokens: tokens.colors.length,
      lengthTokens: tokens.lengths.length,
      offColors: offColors.sort((a, b) => b.count - a.count),
      nearColors: nearColors.sort((a, b) => b.count - a.count),
      offFontSizes: offLen(fontSizes),
      offRadii: offLen(radiusNums),
      offShadows: tokenShadows.size ? [...shadows.entries()].filter(([v]) => !tokenShadows.has(v)).map(([v, e]) => ({ value: v, count: e.count, sample: e.sample })) : [],
    };
  }

  const offGrid = [...spacing.entries()]
    .filter(([v]) => v > 2 && Math.abs(v / grid - Math.round(v / grid)) > 0.05)
    .map(([v, e]) => ({ value: `${v}px`, count: e.count, sample: e.sample }))
    .sort((a, b) => b.count - a.count);

  probe.remove();
  const allColors = new Set([...colors.text.keys(), ...colors.background.keys(), ...colors.border.keys()]);

  return {
    page: { width: doc.scrollWidth, height: doc.scrollHeight, viewport: vw, horizontalScroll: doc.scrollWidth > vw + 1 },
    colors: {
      distinct: allColors.size,
      text: histOut(colors.text),
      background: histOut(colors.background, 'area'),
      border: histOut(colors.border),
      saturatedFillShare: +(saturatedArea / pageArea).toFixed(3),
    },
    type: {
      fontSizes: histOut(fontSizes).map((e) => ({ ...e, value: `${e.value}px` })),
      fontWeights: histOut(fontWeights),
      families: histOut(families),
      textStyles: histOut(textStyles).length,
      tinyText: { count: tinyCount, samples: tinyText },
      longLines,
    },
    spacing: { distinct: spacing.size, offGrid, grid, top: histOut(spacing).slice(0, 12).map((e) => ({ value: `${e.value}px`, count: e.count })) },
    shape: { radii: histOut(radii), shadows: histOut(shadows) },
    alignment: { lines: xs.length, nearMisses },
    actions: { filledActions, samples: filledActionSamples, source: primarySelector ? 'selector' : 'heuristic' },
    targets: { below24: smallTargets.length, below44: warnTargets.length, samples24: smallTargets.slice(0, 8), samples44: warnTargets.slice(0, 8) },
    overflow: { truncated, offscreenRight: overflowRight },
    tokens: tokenCheck,
  };
}

/** Focus indicator of the active element: compares focused vs blurred styles. */
export function inspectFocus() {
  const el = document.activeElement;
  if (!el || el === document.body) return null;
  const pick = (cs) => ({ outline: `${cs.outlineStyle} ${cs.outlineWidth} ${cs.outlineColor}`, shadow: cs.boxShadow, border: cs.borderColor, bg: cs.backgroundColor, ow: parseFloat(cs.outlineWidth), os: cs.outlineStyle });
  const focused = pick(getComputedStyle(el));
  el.blur();
  const blurred = pick(getComputedStyle(el));
  el.focus();
  const outline = focused.os !== 'none' && focused.ow > 0;
  const changed = focused.shadow !== blurred.shadow || focused.border !== blurred.border || focused.bg !== blurred.bg || focused.outline !== blurred.outline;
  const r = el.getBoundingClientRect();
  let s = el.tagName.toLowerCase();
  const txt = (el.innerText || el.getAttribute('aria-label') || el.getAttribute('placeholder') || '').trim().replace(/\s+/g, ' ').slice(0, 30);
  if (txt) s += ` "${txt}"`;
  return { el: s, visible: outline || changed, outline, box: { x: r.x, y: r.y, w: r.width, h: r.height } };
}

/** Converts DTCG colour strings to sRGB in the browser's own colour engine. */
export function normalizeColors(list) {
  const probe = document.createElement('div');
  document.body.appendChild(probe);
  const out = [];
  for (const { name, value } of list) {
    probe.style.color = '';
    probe.style.color = `rgb(from ${value} r g b)`;
    if (!probe.style.color) continue;
    const cs = getComputedStyle(probe).color;
    const n = (cs.match(/-?[\d.]+(e-?\d+)?/g) || []).map(parseFloat);
    if (n.length >= 3) {
      const k = /^color\(srgb/.test(cs) ? 255 : 1;
      const c = (v) => Math.max(0, Math.min(255, Math.round(v * k)));
      out.push({ name, r: c(n[0]), g: c(n[1]), b: c(n[2]) });
    }
  }
  probe.remove();
  return out;
}
