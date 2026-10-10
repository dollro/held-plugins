import { fileURLToPath, URL } from 'node:url'

import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

const src = fileURLToPath(new URL('./src', import.meta.url))

// Django serves every page; there is no index.html. Vite only builds assets into
// Django's static dir with a manifest (production) or serves them with HMR on
// :3000 (development). django-vite reads both. Tooling config (TypeScript,
// ESLint, Vitest) comes from create-vue; this file holds the Django integration.
// No environment values are compiled in: the bundle is the same for staging and
// production, and runtime values come from Django (src/config.ts).
export default defineConfig({
  root: src,
  base: '/static/vue/',
  plugins: [vue(), tailwindcss()],
  resolve: {
    alias: { '@': src },
  },
  build: {
    outDir: fileURLToPath(new URL('../backend/static/vue', import.meta.url)),
    emptyOutDir: true,
    manifest: true,
    // Entry points = the `{% vite_asset %}` names used in Django templates.
    rolldownOptions: {
      input: {
        main: fileURLToPath(new URL('./src/main.ts', import.meta.url)),
        'app-main': fileURLToPath(new URL('./src/app-main.ts', import.meta.url)),
      },
    },
  },
  server: {
    host: '0.0.0.0',
    port: 3000,
    strictPort: true,
    origin: 'http://localhost:3000',
    // Pages come from the local proxy on :8000; allow exactly that origin.
    cors: { origin: 'http://localhost:8000' },
    watch: { usePolling: true },
  },
})
