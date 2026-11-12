#!/usr/bin/env node
/**
 * diff.mjs — Pixel diff wrapper using odiff-bin.
 *
 * Produces both the diff PNG and a structured JSON summary with
 * bounding boxes for changed regions (so Claude's vision pass knows
 * WHERE to look).
 *
 * Usage:
 *   node diff.mjs --base <target.png> --compare <impl.png> --out <diff.png> [options]
 *
 * Options:
 *   --base <path>          Target (baseline) PNG
 *   --compare <path>       Implementation PNG
 *   --out <path>           Output diff PNG
 *   --threshold <n>        Pixel color threshold 0-1 (default: 0.1)
 *   --antialiasing         Ignore AA pixels (default: true)
 *   --fail-on-layout       Exit non-zero on dimension mismatch (default: true)
 *   --ignore-region <x1,y1,x2,y2>   Can be passed multiple times
 *   --cluster-regions      Compute bounding boxes of changed pixel clusters (default: true)
 *
 * Writes diff JSON summary to stdout. Exit 0 if match, 1 if diff, 2 on error.
 */

import { compare } from 'odiff-bin';
import { parseArgs } from 'node:util';
import { mkdir, readFile, writeFile } from 'node:fs/promises';
import { dirname } from 'node:path';
import { PNG } from 'pngjs';

const { values: args, positionals } = parseArgs({
  options: {
    base: { type: 'string' },
    compare: { type: 'string' },
    out: { type: 'string' },
    threshold: { type: 'string', default: '0.1' },
    antialiasing: { type: 'string', default: 'true' },
    'fail-on-layout': { type: 'string', default: 'true' },
    'ignore-region': { type: 'string', multiple: true },
    'cluster-regions': { type: 'string', default: 'true' },
  },
  allowPositionals: true,
});

for (const required of ['base', 'compare', 'out']) {
  if (!args[required]) {
    console.error(`Error: --${required} is required`);
    process.exit(2);
  }
}

const ignoreRegions = (args['ignore-region'] || []).map(r => {
  const [x1, y1, x2, y2] = r.split(',').map(Number);
  return { x1, y1, x2, y2 };
});

async function main() {
  await mkdir(dirname(args.out), { recursive: true });

  const result = await compare(args.base, args.compare, args.out, {
    threshold: Number(args.threshold),
    antialiasing: args.antialiasing === 'true',
    failOnLayoutDiff: args['fail-on-layout'] === 'true',
    ignoreRegions,
    outputDiffMask: false,
  });

  const summary = {
    base: args.base,
    compare: args.compare,
    diff: args.out,
    threshold: Number(args.threshold),
    antialiasing: args.antialiasing === 'true',
    ignoreRegions,
    timestamp: new Date().toISOString(),
    ...result,
  };

  // If there's a pixel diff, cluster the changed pixels into bounding boxes
  // so Claude's vision pass has structured "look here" coordinates.
  if (!result.match && result.reason === 'pixel-diff' && args['cluster-regions'] === 'true') {
    try {
      summary.clusters = await clusterDiffPixels(args.out);
    } catch (err) {
      summary.clusterError = err.message;
    }
  }

  // Also: what dimensions are we dealing with?
  try {
    const baseMeta = await readPngMeta(args.base);
    const compareMeta = await readPngMeta(args.compare);
    summary.dimensions = {
      base: baseMeta,
      compare: compareMeta,
      match: baseMeta.width === compareMeta.width && baseMeta.height === compareMeta.height,
    };
  } catch {}

  const summaryPath = args.out.replace(/\.png$/, '.json');
  await writeFile(summaryPath, JSON.stringify(summary, null, 2));
  console.log(JSON.stringify(summary, null, 2));

  process.exit(result.match ? 0 : 1);
}

async function readPngMeta(path) {
  const buf = await readFile(path);
  const png = PNG.sync.read(buf);
  return { width: png.width, height: png.height };
}

/**
 * Read the diff PNG, find clusters of changed pixels, return bounding boxes.
 * This uses simple flood-fill clustering — good enough for ranking regions
 * by area. Not trying to be perfect.
 */
async function clusterDiffPixels(diffPath) {
  const buf = await readFile(diffPath);
  const png = PNG.sync.read(buf);
  const { width, height, data } = png;

  // Build a binary mask: is this pixel flagged as changed?
  // odiff paints changed pixels in red (#cd2cc9 by default or #ff0000). We check
  // for any strongly non-grayscale output pixel.
  const mask = new Uint8Array(width * height);
  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const i = (y * width + x) * 4;
      const r = data[i], g = data[i + 1], b = data[i + 2];
      // Changed pixels are colored distinctly vs. greyscale background
      const isChanged = (r > 200 && g < 100) || (b > 200 && g < 100) || (r > 200 && b > 200 && g < 150);
      mask[y * width + x] = isChanged ? 1 : 0;
    }
  }

  // Connected-component labelling with an iterative stack (flood fill).
  // Components below MIN_AREA are discarded (sub-pixel noise).
  const MIN_AREA = 25;
  const visited = new Uint8Array(width * height);
  const clusters = [];

  for (let y = 0; y < height; y++) {
    for (let x = 0; x < width; x++) {
      const idx = y * width + x;
      if (!mask[idx] || visited[idx]) continue;

      // BFS flood
      let minX = x, minY = y, maxX = x, maxY = y, area = 0;
      const stack = [idx];
      while (stack.length) {
        const p = stack.pop();
        if (visited[p]) continue;
        visited[p] = 1;
        if (!mask[p]) continue;
        const py = Math.floor(p / width);
        const px = p - py * width;
        if (px < minX) minX = px;
        if (px > maxX) maxX = px;
        if (py < minY) minY = py;
        if (py > maxY) maxY = py;
        area++;
        if (px > 0) stack.push(p - 1);
        if (px < width - 1) stack.push(p + 1);
        if (py > 0) stack.push(p - width);
        if (py < height - 1) stack.push(p + width);
      }

      if (area >= MIN_AREA) {
        clusters.push({
          x: minX,
          y: minY,
          width: maxX - minX + 1,
          height: maxY - minY + 1,
          area,
        });
      }
    }
  }

  // Sort by area descending — largest clusters first matter most
  clusters.sort((a, b) => b.area - a.area);

  // Cap to 20 so the JSON stays manageable
  return clusters.slice(0, 20);
}

main().catch(err => {
  console.error('Diff failed:', err.message);
  process.exit(2);
});
