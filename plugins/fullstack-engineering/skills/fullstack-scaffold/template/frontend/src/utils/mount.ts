import { createApp, type Component } from 'vue'
import { createPinia } from 'pinia'

/**
 * Mount a Vue island into a Django-rendered page. Each island is its own app;
 * data-* attributes on the element become props.
 */
export function mountIsland(component: Component, selector: string): void {
  const el = document.querySelector<HTMLElement>(selector)
  if (!el) return
  const app = createApp(component, { ...el.dataset })
  app.use(createPinia())
  app.mount(el)
}
