#!/usr/bin/env node
/**
 * screenshot.mjs — Stabilized Playwright screenshot helper for design-parity loop.
 *
 * Primary invocation is indirect via `parity.mjs`. Direct CLI use is still
 * supported for one-off captures and legacy workflows.
 *
 * Usage:
 *   node screenshot.mjs --url <url> --viewport WxH --out <path> [options]
 *
 * Options:
 *   --url <url>              Target URL (http://, https://, or file://)
 *   --viewport WxH           Viewport, e.g. 1440x900 (default)
 *   --dpr <n>                Device pixel ratio (default: 1)
 *   --out <path>             Output PNG path
 *   --selector <css>         Screenshot only the element matching <css>. Useful for
 *                            multi-screen canvas HTML exports (one file, many screens).
 *   --wait-for <state>       load | domcontentloaded | networkidle (default: networkidle)
 *   --disable-animations     Inject CSS to freeze animations (default: true)
 *   --storage-state <path>   Load auth state JSON
 *   --auth-setup             Open visible browser for interactive login, save storageState
 *                            (human-only — for agent/CI loops, use `parity auth` instead)
 *   --mask <selectors>       Comma-separated selectors to hide before screenshot
 *   --mask-region <x,y,w,h>  Rectangular region to black out. Can be repeated.
 *   --mask-text <regex>      /pattern/flags — replace matching text-node content with
 *                            spaces before capture. Can be repeated.
 *   --extract-styles <sels>  Extract computed styles for selectors, write <out>.styles.json
 *   --timeout <ms>           Navigation timeout (default: 30000)
 *   --full-page              Capture full page, not just viewport
 *
 * Exits 0 on success, 1 on failure. Writes screenshot to --out path.
 */

import { chromium } from 'playwright';
import { parseArgs } from 'node:util';
import { mkdir, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';

const { values: args } = parseArgs({
  options: {
    url: { type: 'string' },
    viewport: { type: 'string', default: '1440x900' },
    dpr: { type: 'string', default: '1' },
    out: { type: 'string' },
    selector: { type: 'string' },
    'wait-for': { type: 'string', default: 'networkidle' },
    'disable-animations': { type: 'boolean', default: true },
    'storage-state': { type: 'string' },
    'auth-setup': { type: 'boolean', default: false },
    mask: { type: 'string' },
    'mask-region': { type: 'string', multiple: true },
    'mask-text': { type: 'string', multiple: true },
    'extract-styles': { type: 'string' },
    timeout: { type: 'string', default: '30000' },
    'full-page': { type: 'boolean', default: false },
  },
});

if (!args.url) { console.error('Error: --url is required'); process.exit(1); }
if (!args['auth-setup'] && !args.out) { console.error('Error: --out is required (unless --auth-setup)'); process.exit(1); }

const [width, height] = args.viewport.split('x').map(Number);
const deviceScaleFactor = Number(args.dpr);
const timeout = Number(args.timeout);

async function main() {
  const browser = await chromium.launch({ headless: !args['auth-setup'] });

  const contextOpts = {
    viewport: { width, height },
    deviceScaleFactor,
    reducedMotion: 'reduce',
  };
  if (args['storage-state']) contextOpts.storageState = args['storage-state'];

  const context = await browser.newContext(contextOpts);
  const page = await context.newPage();

  // Interactive auth mode (humans only)
  if (args['auth-setup']) {
    await page.goto(args.url);
    console.log('Log in manually in the browser window, then press Enter here.');
    await new Promise(resolve => process.stdin.once('data', resolve));
    const authPath = '.parity/auth.json';
    await mkdir(dirname(authPath), { recursive: true });
    await context.storageState({ path: authPath });
    console.log(`Saved auth state to ${authPath}`);
    await browser.close();
    process.exit(0);
  }

  // ---- Stabilization pipeline ----
  if (args['disable-animations']) {
    await context.addInitScript(() => {
      const style = document.createElement('style');
      style.textContent = `
        *, *::before, *::after {
          animation-duration: 0s !important;
          animation-delay: 0s !important;
          animation-iteration-count: 1 !important;
          transition-duration: 0s !important;
          transition-delay: 0s !important;
          scroll-behavior: auto !important;
        }
      `;
      const insert = () => {
        if (document.head) document.head.appendChild(style);
        else requestAnimationFrame(insert);
      };
      insert();
    });
  }

  await page.goto(args.url, { waitUntil: args['wait-for'], timeout });
  await page.evaluate(() => document.fonts.ready);
  await page.evaluate(() => { document.getAnimations().forEach(a => { try { a.finish(); } catch {} }); });

  await page.evaluate(async () => {
    const h = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
    const step = window.innerHeight;
    for (let y = 0; y < h; y += step) { window.scrollTo(0, y); await new Promise(r => setTimeout(r, 80)); }
    window.scrollTo(0, 0);
  });
  await page.waitForTimeout(400);

  // Selector masks (visibility:hidden — preserves layout)
  if (args.mask) {
    const selectors = args.mask.split(',').map(s => s.trim()).filter(Boolean);
    await page.evaluate((sels) => {
      for (const sel of sels) document.querySelectorAll(sel).forEach(el => { el.style.visibility = 'hidden'; });
    }, selectors);
  }

  // Regex-over-text masks
  if (args['mask-text']?.length) {
    await page.evaluate((patterns) => {
      const res = patterns.map(p => {
        const m = /^\/(.+)\/([gimsuy]*)$/.exec(p);
        return m ? new RegExp(m[1], m[2]) : new RegExp(p);
      });
      const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
      let n;
      while ((n = walker.nextNode())) {
        for (const re of res) {
          if (re.test(n.nodeValue)) {
            n.nodeValue = n.nodeValue.replace(re, (m) => ' '.repeat(m.length));
          }
        }
      }
    }, args['mask-text']);
  }

  // Extract styles (unchanged)
  if (args['extract-styles']) {
    const selectors = args['extract-styles'].split(',').map(s => s.trim()).filter(Boolean);
    const styles = await page.evaluate((sels) => {
      const out = {};
      for (const sel of sels) {
        const el = document.querySelector(sel);
        if (!el) { out[sel] = null; continue; }
        const cs = getComputedStyle(el);
        const rect = el.getBoundingClientRect();
        out[sel] = {
          box: { x: rect.x, y: rect.y, width: rect.width, height: rect.height },
          fontFamily: cs.fontFamily, fontSize: cs.fontSize, fontWeight: cs.fontWeight,
          lineHeight: cs.lineHeight, letterSpacing: cs.letterSpacing,
          color: cs.color, backgroundColor: cs.backgroundColor,
          borderRadius: cs.borderRadius, borderColor: cs.borderColor, borderWidth: cs.borderWidth,
          padding: cs.padding, margin: cs.margin,
          boxShadow: cs.boxShadow, display: cs.display, position: cs.position,
        };
      }
      return out;
    }, selectors);
    const stylesPath = args.out.replace(/\.png$/, '.styles.json');
    await mkdir(dirname(stylesPath), { recursive: true });
    await writeFile(stylesPath, JSON.stringify(styles, null, 2));
    console.log(`Styles written to ${stylesPath}`);
  }

  // Region masks — overlay opaque rectangles before capture
  const regions = (args['mask-region'] || []).map(r => {
    const [x, y, w, h] = r.split(',').map(Number);
    return { x, y, w, h };
  });
  if (regions.length) {
    await page.evaluate((regs) => {
      const overlay = document.createElement('div');
      overlay.style.cssText = 'position:fixed;inset:0;pointer-events:none;z-index:2147483647';
      for (const { x, y, w, h } of regs) {
        const rect = document.createElement('div');
        rect.style.cssText = `position:absolute;left:${x}px;top:${y}px;width:${w}px;height:${h}px;background:#000`;
        overlay.appendChild(rect);
      }
      document.body.appendChild(overlay);
    }, regions);
  }

  await mkdir(dirname(args.out), { recursive: true });

  // Selector capture for canvas-with-many-screens targets
  if (args.selector) {
    const locator = page.locator(args.selector).first();
    await locator.waitFor({ state: 'visible', timeout }).catch(() => {});
    await locator.screenshot({ path: args.out, animations: 'disabled' });
  } else {
    await page.screenshot({
      path: args.out,
      fullPage: args['full-page'],
      animations: 'disabled',
    });
  }

  const metaPath = args.out.replace(/\.png$/, '.meta.json');
  await writeFile(metaPath, JSON.stringify({
    url: args.url,
    selector: args.selector || null,
    viewport: { width, height },
    deviceScaleFactor,
    timestamp: new Date().toISOString(),
    fullPage: args['full-page'],
    masks: {
      selectors: args.mask ? args.mask.split(',').map(s => s.trim()) : [],
      regions,
      text: args['mask-text'] || [],
    },
  }, null, 2));

  console.log(`Screenshot written to ${args.out}`);
  await browser.close();
}

main().catch(err => {
  console.error('Screenshot failed:', err.message);
  process.exit(1);
});
