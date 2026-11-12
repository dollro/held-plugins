/**
 * mcp-plan.mjs — emit a JSON plan describing the MCP tool calls needed to
 * produce a target+impl screenshot pair for one screen. The calling agent
 * (Claude Code, typically) executes these via its normal tool-use loop.
 *
 * The plan is intentionally runtime-agnostic at the field level —
 * `tool` names differ between Playwright-MCP and Chrome-DevTools-MCP, but
 * the stabilization steps (fonts, animations, scroll, mask) are identical.
 */

import { relative } from 'node:path';

const PLAYWRIGHT_MCP = {
  new_context: 'browser_new_context',
  new_page: 'browser_new_page',
  goto: 'browser_navigate',
  set_viewport: 'browser_resize',
  eval: 'browser_evaluate',
  screenshot: 'browser_take_screenshot',
  close: 'browser_close',
};

const CHROME_DEVTOOLS_MCP = {
  new_page: 'new_page',
  goto: 'navigate_page',
  set_viewport: 'resize_page',
  eval: 'evaluate_script',
  screenshot: 'take_screenshot',
  close: 'close_page',
};

const STABILIZATION_JS = `
(async () => {
  const style = document.createElement('style');
  style.textContent = '*,*::before,*::after{animation-duration:0s!important;animation-delay:0s!important;transition-duration:0s!important;transition-delay:0s!important;scroll-behavior:auto!important}';
  document.head.appendChild(style);
  await document.fonts.ready;
  document.getAnimations().forEach(a => { try { a.finish(); } catch {} });
  const h = Math.max(document.body.scrollHeight, document.documentElement.scrollHeight);
  for (let y = 0; y < h; y += window.innerHeight) {
    window.scrollTo(0, y);
    await new Promise(r => setTimeout(r, 80));
  }
  window.scrollTo(0, 0);
  await new Promise(r => setTimeout(r, 400));
})()
`.trim();

function maskJs(masks) {
  if (!masks?.length) return null;
  const selectors = masks.filter(m => m.kind === 'selector').map(m => m.value);
  const textPatterns = masks.filter(m => m.kind === 'text').map(m => m.pattern);
  // Regions are applied by the screenshot tool itself via clip/overlay; pass through.
  return `
(() => {
  const sels = ${JSON.stringify(selectors)};
  for (const s of sels) document.querySelectorAll(s).forEach(e => e.style.visibility = 'hidden');
  const patterns = ${JSON.stringify(textPatterns)}.map(p => {
    const m = /^\\/(.+)\\/([gimsuy]*)$/.exec(p);
    return m ? new RegExp(m[1], m[2]) : new RegExp(p);
  });
  if (patterns.length) {
    const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
    let n;
    while ((n = walker.nextNode())) {
      for (const re of patterns) if (re.test(n.nodeValue)) { n.nodeValue = n.nodeValue.replace(re, ''); break; }
    }
  }
})()`.trim();
}

export function buildScreenPlan({ screen, runtime, impl, target, rootDir, viewport }) {
  const tools = runtime === 'mcp-chrome-devtools' ? CHROME_DEVTOOLS_MCP : PLAYWRIGHT_MCP;
  const [w, h] = viewport;

  const steps = [];

  // --- Target capture ---
  if (target.needsCapture) {
    steps.push({ tool: tools.new_page, args: {} });
    steps.push({ tool: tools.set_viewport, args: { width: w, height: h } });
    steps.push({
      tool: tools.goto,
      args: { url: target.url, waitUntil: 'networkidle' },
    });
    steps.push({ tool: tools.eval, args: { script: STABILIZATION_JS } });
    if (target.selector) {
      steps.push({
        tool: tools.screenshot,
        args: { selector: target.selector, path: relative(rootDir, target.out) },
      });
    } else {
      steps.push({
        tool: tools.screenshot,
        args: { path: relative(rootDir, target.out) },
      });
    }
    steps.push({ tool: tools.close, args: {} });
  }

  // --- Impl capture ---
  steps.push({ tool: tools.new_page, args: {} });
  steps.push({ tool: tools.set_viewport, args: { width: w, height: h } });
  if (impl.storageState) {
    steps.push({
      tool: '__parity_note__',
      args: { message: `Ensure MCP context has cookies/storage from ${impl.storageState} loaded before continuing.` },
    });
  }
  steps.push({
    tool: tools.goto,
    args: { url: impl.url, waitUntil: 'networkidle' },
  });
  steps.push({ tool: tools.eval, args: { script: STABILIZATION_JS } });
  const mask = maskJs(screen._masks);
  if (mask) steps.push({ tool: tools.eval, args: { script: mask } });
  steps.push({
    tool: tools.screenshot,
    args: { path: relative(rootDir, impl.out) },
  });
  steps.push({ tool: tools.close, args: {} });

  return {
    screen: screen.id,
    runtime,
    viewport: [w, h],
    steps,
    followup: {
      note: 'After executing the steps above, run `node scripts/diff.mjs --base <target> --compare <impl> --out <diff>` locally to complete the iteration.',
    },
  };
}
