/**
 * capture.mjs: one capture = one place, in one state, at one viewport and
 * colour scheme. Measures motion and perf live, then freezes animations,
 * measures the static layer, runs axe, walks focus and takes the screenshot.
 */

import { mkdir } from 'node:fs/promises';
import { join, resolve } from 'node:path';
import AxeBuilder from '@axe-core/playwright';
import { applyContextAuth } from '../../../design-parity/scripts/lib/auth.mjs';
import { installPerfObservers, tokensFromPage, measureMotion, measurePage, inspectFocus, normalizeColors } from './page-measure.mjs';
import { joinUrl } from './config.mjs';

const FREEZE_CSS = `*,*::before,*::after{animation-duration:0s!important;animation-delay:0s!important;animation-iteration-count:1!important;transition-duration:0s!important;transition-delay:0s!important;scroll-behavior:auto!important;caret-color:transparent!important}`;

export async function capture(browser, cfg, item, auth, outDir, opts = {}) {
  const { place, state, viewport, scheme } = item;
  const needsAuth = place.requires_auth ?? !!(cfg.auth && cfg.auth.mode && cfg.auth.mode !== 'none');
  const ctxOpts = {
    viewport: { width: viewport.size[0], height: viewport.size[1] },
    deviceScaleFactor: cfg.dpr,
    colorScheme: scheme === 'dark' ? 'dark' : 'light',
    reducedMotion: 'no-preference',
  };
  if (needsAuth && auth?.storageState) ctxOpts.storageState = auth.storageState;
  const context = await browser.newContext(ctxOpts);
  if (needsAuth) await applyContextAuth(context, auth);
  await context.addInitScript(installPerfObservers);
  if (scheme === 'dark') await applyDarkMode(context, cfg.dark_mode);

  const page = await context.newPage();
  const errors = [];
  page.on('pageerror', (e) => errors.push(String(e.message || e).slice(0, 200)));
  page.on('console', (m) => { if (m.type() === 'error') errors.push(m.text().slice(0, 200)); });

  const mocks = [].concat(place.mock || [], state.mock || []);
  for (const m of mocks) await page.route(m.url, (route) => fulfil(route, m));

  const url = joinUrl(cfg.base_url, place.path);
  const live = state.capture_after_ms != null || mocks.some((m) => m.hang);
  const result = { id: item.id, place: place.id, state: state.id, viewport: viewport.id, size: viewport.size, scheme, url, live, errors };

  try {
    await page.goto(url, { waitUntil: live ? 'domcontentloaded' : cfg.wait_for, timeout: cfg.timeout_ms });
    if (state.offline) await context.setOffline(true);
    await runSteps(page, [].concat(place.steps || [], state.steps || []), cfg.timeout_ms, cfg._rootDir);
    await page.waitForTimeout(state.capture_after_ms ?? cfg.settle_ms);
    await page.evaluate(() => document.fonts.ready.then(() => true));

    result.motion = await page.evaluate(measureMotion);
    result.perf = await page.evaluate(() => window.__uir || null);

    await page.addStyleTag({ content: FREEZE_CSS });
    await page.evaluate(() => document.getAnimations().forEach((a) => { try { a.finish(); } catch {} }));
    if (!live) await lazyScroll(page);

    const tokens = await loadTokens(page, cfg);
    result.tokenSource = tokens ? { colors: tokens.colors.length, lengths: tokens.lengths.length, shadows: (tokens.shadows || []).length } : null;
    result.metrics = await page.evaluate(measurePage, {
      grid: cfg.grid,
      tokens,
      ignore: cfg.ignore || [],
      primarySelector: cfg.primary_action || null,
      scope: state.scope || place.scope || null,
    });

    if (cfg.axe && !opts.noAxe) result.axe = await runAxe(page, cfg);
    if (opts.focus) result.focus = await walkFocus(page, cfg, join(outDir, 'focus', place.id));

    await applyMasks(page, [].concat(cfg.mask || [], place.mask || []));
    const shot = join(outDir, place.id, state.id, `${viewport.id}-${scheme}.png`);
    await mkdir(join(outDir, place.id, state.id), { recursive: true });
    await page.screenshot({ path: shot, fullPage: true, animations: 'disabled' });
    result.screenshot = shot;
  } catch (e) {
    result.failed = String(e.message || e).split('\n')[0];
  }
  await context.close();

  if (opts.focus && !result.failed) result.reducedMotion = await reducedMotionPass(browser, cfg, item, auth, ctxOpts);
  return result;
}

async function fulfil(route, m) {
  if (m.hang) return; // never answered: the loading state stays on screen
  if (m.abort) return route.abort();
  if (m.delay_ms) await new Promise((r) => setTimeout(r, m.delay_ms));
  const body = m.json !== undefined ? JSON.stringify(m.json) : m.body ?? '';
  return route.fulfill({
    status: m.status ?? 200,
    contentType: m.json !== undefined ? 'application/json' : m.content_type || 'text/plain',
    headers: m.headers || {},
    body,
  }).catch(() => {});
}

async function applyDarkMode(context, mode) {
  if (!mode || mode === 'media') return;
  await context.addInitScript((m) => {
    if (m.local_storage) for (const [k, v] of Object.entries(m.local_storage)) localStorage.setItem(k, v);
    const apply = () => {
      const el = m.target === 'body' ? document.body : document.documentElement;
      if (!el) return requestAnimationFrame(apply);
      if (m.class) el.classList.add(m.class);
      if (m.attribute) el.setAttribute(m.attribute, m.value ?? 'dark');
    };
    apply();
  }, mode);
}

export async function runSteps(page, steps, timeout, rootDir = process.cwd()) {
  for (const s of steps) {
    if (s.click) await page.locator(s.click).first().click({ timeout });
    else if (s.fill) await page.locator(s.fill.selector).first().fill(String(s.fill.value), { timeout });
    else if (s.press) await page.keyboard.press(s.press);
    else if (s.hover) await page.locator(s.hover).first().hover({ timeout });
    else if (s.select) await page.locator(s.select.selector).first().selectOption(String(s.select.value), { timeout });
    else if (s.upload) await page.locator(s.upload.selector).first().setInputFiles(resolve(rootDir, s.upload.file), { timeout });
    else if (s.check) await page.locator(s.check).first().check({ timeout });
    else if (s.wait_for) await page.locator(s.wait_for).first().waitFor({ state: 'visible', timeout });
    else if (s.wait_ms) await page.waitForTimeout(s.wait_ms);
    else if (s.scroll_to) await page.locator(s.scroll_to).first().scrollIntoViewIfNeeded({ timeout });
    else throw new Error(`Unknown step: ${JSON.stringify(s)}`);
  }
}

async function lazyScroll(page) {
  await page.evaluate(async () => {
    const h = document.documentElement.scrollHeight;
    for (let y = 0; y < h; y += window.innerHeight) {
      window.scrollTo(0, y);
      await new Promise((r) => setTimeout(r, 60));
    }
    window.scrollTo(0, 0);
  });
  await page.waitForTimeout(200);
}

async function loadTokens(page, cfg) {
  const t = cfg.tokens;
  if (t.source === 'none') return null;
  if (t.source === 'dtcg') {
    const d = cfg._dtcg;
    if (!d) return null;
    return { colors: await page.evaluate(normalizeColors, d.rawColors), lengths: d.lengths, shadows: [] };
  }
  const found = await page.evaluate(tokensFromPage, { prefixes: t.prefixes || [], exclude: t.exclude || [] });
  return found.count ? found : null;
}

async function runAxe(page, cfg) {
  try {
    let b = new AxeBuilder({ page }).withTags(['wcag2a', 'wcag2aa', 'wcag21a', 'wcag21aa', 'wcag22aa']);
    for (const sel of cfg.ignore || []) b = b.exclude(sel);
    const res = await b.analyze();
    return res.violations.map((v) => ({
      id: v.id,
      impact: v.impact,
      help: v.help,
      nodes: v.nodes.length,
      samples: v.nodes.slice(0, 3).map((n) => n.target.join(' ')),
    }));
  } catch (e) {
    return [{ id: 'axe-failed', impact: 'minor', help: String(e.message || e).slice(0, 160), nodes: 0, samples: [] }];
  }
}

async function walkFocus(page, cfg, dir) {
  await mkdir(dir, { recursive: true });
  await page.evaluate(() => { document.activeElement?.blur?.(); window.scrollTo(0, 0); });
  const stops = [];
  let first = null;
  for (let i = 0; i < cfg.focus_stops; i++) {
    await page.keyboard.press('Tab');
    const info = await page.evaluate(inspectFocus);
    if (!info) break;
    const sig = `${info.el}@${Math.round(info.box.x)},${Math.round(info.box.y)}`;
    if (first === sig) break;
    first = first || sig;
    const n = String(i + 1).padStart(2, '0');
    const path = join(dir, `${n}.png`);
    const pad = 12;
    const clip = {
      x: Math.max(0, info.box.x - pad),
      y: Math.max(0, info.box.y - pad),
      width: Math.max(1, info.box.w + 2 * pad),
      height: Math.max(1, info.box.h + 2 * pad),
    };
    try {
      await page.screenshot({ path, clip });
      info.frame = path;
    } catch {}
    stops.push(info);
  }
  return { stops: stops.length, missing: stops.filter((s) => !s.visible).map((s) => s.el), frames: stops.map((s) => s.frame).filter(Boolean) };
}

async function applyMasks(page, masks) {
  if (!masks.length) return;
  await page.evaluate((list) => {
    for (const m of list) {
      if (typeof m === 'string' || m.selector) {
        document.querySelectorAll(typeof m === 'string' ? m : m.selector).forEach((el) => { el.style.visibility = 'hidden'; });
      } else if (m.text) {
        const mm = /^\/(.+)\/([gimsuy]*)$/.exec(m.text);
        const re = mm ? new RegExp(mm[1], mm[2]) : new RegExp(m.text);
        const w = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
        let n;
        while ((n = w.nextNode())) if (re.test(n.nodeValue)) n.nodeValue = n.nodeValue.replace(re, (x) => ' '.repeat(x.length));
      }
    }
  }, masks);
}

/** Second load with prefers-reduced-motion: reduce; counts what still moves. */
async function reducedMotionPass(browser, cfg, item, auth, ctxOpts) {
  const context = await browser.newContext({ ...ctxOpts, reducedMotion: 'reduce' });
  try {
    if (auth?.cookies) await applyContextAuth(context, auth);
    const page = await context.newPage();
    await page.goto(joinUrl(cfg.base_url, item.place.path), { waitUntil: cfg.wait_for, timeout: cfg.timeout_ms });
    await page.waitForTimeout(cfg.settle_ms);
    return await page.evaluate(() => {
      const running = document.getAnimations().filter((a) => a.playState === 'running');
      return { runningAnimations: running.length, infinite: running.filter((a) => a.effect && a.effect.getTiming().iterations === Infinity).length };
    });
  } catch (e) {
    return { failed: String(e.message || e).split('\n')[0] };
  } finally {
    await context.close();
  }
}
