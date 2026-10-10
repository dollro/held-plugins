// Entry for the authenticated single-page app below /app/.
import 'vite/modulepreload-polyfill'
import './styles.css'

import { createApp } from 'vue'
import { createPinia } from 'pinia'

import App from './App.vue'
import { createAppRouter } from './router'

const el = document.getElementById('vue-app')
if (el) {
  const app = createApp(App)
  app.use(createPinia())
  app.use(createAppRouter())
  app.mount(el)
}
