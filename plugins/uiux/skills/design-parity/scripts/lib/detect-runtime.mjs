/**
 * detect-runtime.mjs — pick the runtime adapter.
 *
 * Detection order for `runtime: auto`:
 *   1. PARITY_RUNTIME env var (explicit override)
 *   2. PARITY_MCP_PLAYWRIGHT=1 → mcp-playwright
 *   3. PARITY_MCP_CHROME_DEVTOOLS=1 → mcp-chrome-devtools
 *   4. Node playwright resolvable → node-playwright
 *   5. Fail with a clear error listing remediation steps
 *
 * MCP runtimes never touch the browser directly — they emit a plan (ordered
 * JSON tool-call list) which the calling agent executes through its own
 * MCP tool-use loop.
 */

import { createRequire } from 'node:module';

export const RUNTIMES = ['node-playwright', 'mcp-playwright', 'mcp-chrome-devtools'];

export function detectRuntime(configured) {
  const explicit = process.env.PARITY_RUNTIME || configured;
  if (explicit && explicit !== 'auto') {
    if (!RUNTIMES.includes(explicit)) {
      throw new Error(`Unknown runtime: ${explicit}. Valid: ${RUNTIMES.join(', ')}`);
    }
    return explicit;
  }

  if (process.env.PARITY_MCP_PLAYWRIGHT === '1') return 'mcp-playwright';
  if (process.env.PARITY_MCP_CHROME_DEVTOOLS === '1') return 'mcp-chrome-devtools';

  try {
    const require = createRequire(import.meta.url);
    require.resolve('playwright');
    return 'node-playwright';
  } catch {
    throw new Error(
      'No runtime available. Install playwright (`npm install --save-dev playwright odiff-bin pngjs yaml`) ' +
      'or set PARITY_MCP_PLAYWRIGHT=1 / PARITY_MCP_CHROME_DEVTOOLS=1 if the calling agent has the corresponding MCP server connected.'
    );
  }
}
