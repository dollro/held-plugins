/**
 * auth.mjs — non-interactive auth modes for parity runs.
 *
 *   form           — navigate, fill fields, submit, wait for success_match, save storageState
 *   cookie         — inject cookies directly into the browser context
 *   storage-state  — load a pre-existing storageState JSON
 *   none           — noop
 *
 * All modes run headless. The old interactive `--auth-setup` flow remains in
 * screenshot.mjs for human operators but is never required inside an agent loop.
 */

import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import { dirname, resolve } from 'node:path';

export async function ensureAuth(browser, cfg) {
  const auth = cfg.auth;
  if (!auth || auth.mode === 'none' || !auth.mode) return null;
  const rootDir = cfg._rootDir;

  switch (auth.mode) {
    case 'storage-state':
      return storageStateMode(auth, rootDir);
    case 'cookie':
      return cookieMode(auth, rootDir);
    case 'form':
      return formMode(browser, auth, cfg, rootDir);
    default:
      throw new Error(`Unknown auth.mode: ${auth.mode}`);
  }
}

function storageStateMode(auth, rootDir) {
  const p = resolve(rootDir, auth.storage_state);
  if (!existsSync(p)) throw new Error(`auth.storage_state not found: ${p}`);
  return { storageState: p };
}

function cookieMode(auth, rootDir) {
  const outPath = auth.storage_state
    ? resolve(rootDir, auth.storage_state)
    : null;
  return {
    cookies: auth.cookies,
    _persist: outPath,
  };
}

async function formMode(browser, auth, cfg, rootDir) {
  const outPath = auth.storage_state
    ? resolve(rootDir, auth.storage_state)
    : resolve(rootDir, '.parity/auth.json');

  // Reuse saved state if still valid
  if (existsSync(outPath) && !process.env.PARITY_FORCE_LOGIN) {
    return { storageState: outPath };
  }

  const ctx = await browser.newContext({
    viewport: { width: cfg.viewport[0], height: cfg.viewport[1] },
    deviceScaleFactor: cfg.dpr,
  });
  const page = await ctx.newPage();

  const loginUrl = auth.login_url.startsWith('http')
    ? auth.login_url
    : joinUrl(cfg.base_url, auth.login_url);

  await page.goto(loginUrl, { waitUntil: 'networkidle', timeout: cfg.timeout_ms });

  for (const [selector, value] of Object.entries(auth.fields || {})) {
    if (value === '') {
      throw new Error(`auth.fields[${selector}] expanded to empty — check the env var referenced.`);
    }
    await page.fill(selector, value);
  }

  if (auth.submit_selector) {
    await page.click(auth.submit_selector);
  } else {
    await page.keyboard.press('Enter');
  }

  // Success = URL matches regex OR network idle settles after redirect
  if (auth.success_match) {
    const re = parseRegex(auth.success_match);
    await page.waitForURL(re, { timeout: cfg.timeout_ms });
  } else {
    await page.waitForLoadState('networkidle', { timeout: cfg.timeout_ms });
  }

  await mkdir(dirname(outPath), { recursive: true });
  await ctx.storageState({ path: outPath });
  await ctx.close();
  return { storageState: outPath };
}

function parseRegex(src) {
  if (src instanceof RegExp) return src;
  const m = /^\/(.+)\/([gimsuy]*)$/.exec(src);
  if (m) return new RegExp(m[1], m[2]);
  return new RegExp(src);
}

function joinUrl(base, path) {
  return base.replace(/\/+$/, '') + (path.startsWith('/') ? path : '/' + path);
}

// Applied after newContext(), before navigation. For cookie mode.
export async function applyContextAuth(context, auth) {
  if (auth?.cookies) {
    await context.addCookies(auth.cookies);
    if (auth._persist) {
      await mkdir(dirname(auth._persist), { recursive: true });
      await context.storageState({ path: auth._persist });
    }
  }
}
