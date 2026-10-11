---
name: uiux-design-vue3-options-api
description: "Vue 3 Options API style (data(), methods, the this context). Use only in an existing Options API codebase where the user has confirmed they want to keep it; new code uses the Composition API (uiux-design-vue3-best-practices)."
version: 2.1.0
license: MIT
author: github.com/vuejs-ai
---

> **When to use this skill**: This skill is for **brownfield projects that already use Options API exclusively** and where the user has explicitly chosen to continue with Options API for the current task. For all greenfield work and mixed codebases, use `uiux-design-vue3-best-practices` (Composition API with `<script setup>`).
>
> If you haven't asked the user yet, **ask before loading this skill**. The recommended path is always Composition API — it offers better reusability (composables over mixins), better TypeScript support, smaller bundles, and superior code organization at scale.

Vue.js Options API best practices, TypeScript integration, and common gotchas.

### TypeScript
- Need to enable TypeScript type inference for component properties → See [ts-options-api-use-definecomponent](reference/ts-options-api-use-definecomponent.md)
- Enabling type safety for Options API this context → See [ts-strict-mode-options-api](reference/ts-strict-mode-options-api.md)
- Using old TypeScript versions with prop validators → See [ts-options-api-arrow-functions-validators](reference/ts-options-api-arrow-functions-validators.md)
- Event handler parameters need proper type safety → See [ts-options-api-type-event-handlers](reference/ts-options-api-type-event-handlers.md)
- Need to type object or array props with interfaces → See [ts-options-api-proptype-complex-types](reference/ts-options-api-proptype-complex-types.md)
- Injected properties missing TypeScript types completely → See [ts-options-api-provide-inject-limitations](reference/ts-options-api-provide-inject-limitations.md)
- Complex computed properties lack clear type documentation → See [ts-options-api-computed-return-types](reference/ts-options-api-computed-return-types.md)

### Methods & Lifecycle
- Methods aren't binding to component instance context → See [no-arrow-functions-in-methods](reference/no-arrow-functions-in-methods.md)
- Lifecycle hooks losing access to component data → See [no-arrow-functions-in-lifecycle-hooks](reference/no-arrow-functions-in-lifecycle-hooks.md)
- Debounced functions sharing state across component instances → See [stateful-methods-lifecycle](reference/stateful-methods-lifecycle.md)
