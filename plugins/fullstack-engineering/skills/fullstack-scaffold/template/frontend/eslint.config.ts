// create-vue generated eslint.config.base.ts (kept as generated, so it can be
// regenerated). Project rules are added here on top.
import base from './eslint.config.base.ts'

export default [
  ...base,
  {
    name: 'app/http-only-through-client',
    files: ['src/**/*.{ts,vue}'],
    ignores: ['src/api/client.ts'],
    rules: {
      'no-restricted-globals': [
        'error',
        { name: 'fetch', message: 'Use { api } from "@/api/client" instead.' },
      ],
    },
  },
  { name: 'app/ignores', ignores: ['playwright-report/**', 'test-results/**'] },
]
