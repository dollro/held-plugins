/**
 * sheet.mjs: contact sheets for the vision pass. Each sheet is an HTML file
 * in the run folder (open it in a browser) rendered to a PNG (read it as an image).
 */

import { writeFile, mkdir } from 'node:fs/promises';
import { relative, dirname, join } from 'node:path';
import { pathToFileURL } from 'node:url';

const CSS = `
body{margin:0;padding:24px;background:#e9e9ec;font:14px/1.4 system-ui,sans-serif;color:#1a1a1f}
h1{font-size:18px;margin:0 0 16px}
.grid{display:grid;gap:20px;grid-template-columns:repeat(var(--cols),var(--w))}
figure{margin:0;background:#fff;box-shadow:0 1px 3px rgba(0,0,0,.15)}
figcaption{padding:6px 10px;font-size:13px;font-weight:600;border-bottom:1px solid #ddd}
.frame{width:var(--w);height:var(--h);overflow:hidden}
.frame img{width:100%;display:block}
.missing{display:flex;align-items:center;justify-content:center;color:#a00;height:var(--h)}
`;

/**
 * tiles: [{ caption, image (absolute path or null) }]
 * aspect: [w, h] of the source viewport, used to crop each tile to its first screen.
 */
export async function renderSheet(browser, outHtml, title, tiles, { aspect = [1440, 900], tileWidth = null, cols = null, full = false } = {}) {
  const w = tileWidth || (aspect[0] <= 480 ? 300 : aspect[0] <= 900 ? 420 : 720);
  const c = cols || Math.max(1, Math.min(tiles.length, Math.floor(2300 / (w + 20))));
  const h = full ? 'auto' : `${Math.round((w * aspect[1]) / aspect[0])}px`;
  const dir = dirname(outHtml);
  const figs = tiles.map((t) => `<figure><figcaption>${esc(t.caption)}</figcaption>${t.image ? `<div class="frame"><img src="${encodeURI(relative(dir, t.image))}"></div>` : '<div class="missing">capture failed</div>'}</figure>`).join('\n');
  const html = `<!doctype html><meta charset="utf-8"><title>${esc(title)}</title><style>${CSS}</style><body style="--cols:${c};--w:${w}px;--h:${h}"><h1>${esc(title)}</h1><div class="grid">${figs}</div></body>`;
  await mkdir(dir, { recursive: true });
  await writeFile(outHtml, html);
  const ctx = await browser.newContext({ viewport: { width: 2400, height: 1000 } });
  const page = await ctx.newPage();
  await page.goto(pathToFileURL(outHtml).href, { waitUntil: 'load' });
  await page.evaluate(() => Promise.all([...document.images].map((i) => (i.complete ? null : new Promise((r) => { i.onload = i.onerror = r; })))));
  const png = outHtml.replace(/\.html$/, '.png');
  const width = await page.evaluate(() => document.querySelector('.grid').getBoundingClientRect().right + 24);
  await page.setViewportSize({ width: Math.ceil(width), height: 1000 });
  await page.screenshot({ path: png, fullPage: true });
  await ctx.close();
  return png;
}

/** Builds the standard sheets of a run: consistency per viewport, states per place, focus per place. */
export async function buildSheets(browser, cfg, captures, runDir) {
  const out = [];
  const sheetsDir = join(runDir, 'sheets');
  for (const vp of cfg.viewports) {
    for (const scheme of cfg.schemes) {
      const tiles = captures.filter((c) => c.state === 'default' && c.viewport === vp.id && c.scheme === scheme).map((c) => ({ caption: c.place, image: c.screenshot || null }));
      if (tiles.length > 1) out.push(await renderSheet(browser, join(sheetsDir, `places-${vp.id}-${scheme}.html`), `All places, default state, ${vp.id} ${scheme}: same product?`, tiles, { aspect: vp.size }));
    }
  }
  for (const place of cfg.places) {
    const caps = captures.filter((c) => c.place === place.id && c.scheme === cfg.schemes[0] && c.viewport === cfg.viewports[cfg.viewports.length - 1].id);
    if (caps.length > 1) out.push(await renderSheet(browser, join(sheetsDir, `states-${place.id}.html`), `${place.id}: states`, caps.map((c) => ({ caption: c.state, image: c.screenshot || null })), { aspect: cfg.viewports[cfg.viewports.length - 1].size }));
    const vps = captures.filter((c) => c.place === place.id && c.state === 'default' && c.scheme === cfg.schemes[0]);
    if (vps.length > 1) out.push(await renderSheet(browser, join(sheetsDir, `viewports-${place.id}.html`), `${place.id}: viewports`, vps.map((c) => ({ caption: c.viewport, image: c.screenshot || null })), { tileWidth: 360, full: true, cols: vps.length }));
    const focus = captures.find((c) => c.place === place.id && c.focus && c.focus.frames.length);
    if (focus) out.push(await renderSheet(browser, join(sheetsDir, `focus-${place.id}.html`), `${place.id}: keyboard focus, tab order`, focus.focus.frames.map((f, i) => ({ caption: `Tab ${i + 1}`, image: f })), { tileWidth: 260, full: true, cols: 6 }));
  }
  return out;
}

/** Side-by-side pairs of two runs for the pairwise vision review. */
export async function buildPairs(browser, cfg, a, b, labelA, labelB, outDir, all = false) {
  const out = [];
  const widest = cfg.viewports[cfg.viewports.length - 1];
  const byId = Object.fromEntries(a.map((c) => [c.id, c]));
  for (const cb of b) {
    const ca = byId[cb.id];
    if (!ca) continue;
    if (!all && (cb.state !== 'default' || cb.viewport !== widest.id || cb.scheme !== cfg.schemes[0])) continue;
    const vp = cfg.viewports.find((v) => v.id === cb.viewport) || widest;
    const name = cb.id.replace(/\//g, '__');
    out.push(await renderSheet(browser, join(outDir, `${name}.html`), `${cb.id}: ${labelA} (left) vs ${labelB} (right)`, [
      { caption: labelA, image: ca.screenshot || null },
      { caption: labelB, image: cb.screenshot || null },
    ], { aspect: vp.size, cols: 2, full: true, tileWidth: vp.size[0] <= 480 ? 375 : 1000 }));
  }
  return out;
}

function esc(s) {
  return String(s).replace(/[&<>"]/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;' }[c]));
}
