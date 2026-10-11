# Design System Architecture Template

> **Purpose**: Comprehensive, tool-agnostic reference for architecting a production design system.
> Applies to Penpot, Figma, or code-only systems. For Penpot-specific implementation
> (page structure, frame naming, asset registration), see `uiux-design-penpot/references/penpot-design-system-guide.md`.

---

## 1. Design Principles

These principles guide every design decision. When in doubt, resolve ambiguity by checking against them — in priority order:

1. **Functional first.** Every element must serve a clear purpose. No decorative-only elements. If you can't explain what a shape communicates, remove it.
2. **Accessible by default.** WCAG AA compliance is a constraint, not a nice-to-have. Every color pairing, every interactive element, every text size must meet the standards in the Accessibility section.
3. **Clarity over cleverness.** Prefer explicit labels over icons-only. Prefer standard patterns over novel interactions. Users should never have to guess what something does.
4. **Consistent, then custom.** Always use an existing token/component/pattern before creating a new one. If a new element is needed, it should follow the established naming and structural conventions.
5. **Content-aware.** Design for real content lengths, edge cases, and empty states — not just the happy path with perfect placeholder text.

---

## 2. Component Architecture

### Naming Convention

Use slash-separated hierarchy for component naming — this creates nested groups in asset panels:

```
{tier}/{component}/{variant-type}/{variant-value}
```

### Full Component Inventory

```
── Atoms ──
atoms/button/primary/default
atoms/button/primary/hover
atoms/button/primary/active
atoms/button/primary/disabled
atoms/button/primary/loading
atoms/button/secondary/default
atoms/button/secondary/hover
atoms/button/secondary/disabled
atoms/button/outline/default
atoms/button/outline/hover
atoms/button/ghost/default
atoms/button/ghost/hover
atoms/button/danger/default
atoms/button/danger/hover
atoms/button/icon-only/default
atoms/button/sm
atoms/button/md
atoms/button/lg

atoms/input/text/default
atoms/input/text/focus
atoms/input/text/error
atoms/input/text/disabled
atoms/input/text/filled
atoms/input/textarea/default
atoms/input/textarea/focus
atoms/input/search/default
atoms/input/number/default

atoms/badge/status/info
atoms/badge/status/success
atoms/badge/status/warning
atoms/badge/status/danger
atoms/badge/count/default
atoms/badge/tag/default
atoms/badge/tag/removable

atoms/avatar/image/sm
atoms/avatar/image/md
atoms/avatar/image/lg
atoms/avatar/initials/sm
atoms/avatar/initials/md
atoms/avatar/initials/lg

atoms/toggle/default
atoms/toggle/checked
atoms/toggle/disabled
atoms/checkbox/default
atoms/checkbox/checked
atoms/checkbox/indeterminate
atoms/checkbox/disabled
atoms/radio/default
atoms/radio/selected
atoms/radio/disabled

atoms/divider/horizontal
atoms/divider/vertical
atoms/tooltip/top
atoms/tooltip/bottom
atoms/tooltip/left
atoms/tooltip/right
atoms/spinner/sm
atoms/spinner/md
atoms/spinner/lg

── Molecules ──
molecules/form-field/default
molecules/form-field/error
molecules/form-field/required

molecules/card/content/default
molecules/card/content/hover
molecules/card/media/default
molecules/card/stat/default

molecules/nav-item/sidebar/default
molecules/nav-item/sidebar/active
molecules/nav-item/sidebar/collapsed
molecules/nav-item/tab/default
molecules/nav-item/tab/active
molecules/nav-item/breadcrumb/default

molecules/dropdown/single/closed
molecules/dropdown/single/open
molecules/dropdown/multi/closed
molecules/dropdown/multi/open
molecules/dropdown/searchable/default

molecules/toast/info
molecules/toast/success
molecules/toast/warning
molecules/toast/error
molecules/alert/info
molecules/alert/danger

molecules/search-bar/default
molecules/search-bar/focused
molecules/search-bar/with-results

molecules/pagination/default
molecules/pagination/compact

── Organisms ──
organisms/header/desktop/default
organisms/header/desktop/scrolled
organisms/header/mobile/default
organisms/header/mobile/menu-open

organisms/sidebar/expanded/default
organisms/sidebar/collapsed/default
organisms/sidebar/mobile-drawer/default

organisms/data-table/default
organisms/data-table/loading
organisms/data-table/empty
organisms/data-table/selected-rows

organisms/modal/confirm/default
organisms/modal/form/default
organisms/modal/fullscreen/default

organisms/footer/minimal/default
organisms/footer/mega/default

organisms/command-palette/default

── Icons ──
icons/navigation/home
icons/navigation/settings
icons/navigation/search
icons/navigation/menu
icons/navigation/chevron-left
icons/navigation/chevron-right
icons/navigation/chevron-down
icons/navigation/arrow-left
icons/navigation/arrow-right
icons/action/edit
icons/action/delete
icons/action/copy
icons/action/download
icons/action/upload
icons/action/plus
icons/action/minus
icons/action/close
icons/action/check
icons/action/external-link
icons/action/filter
icons/action/sort
icons/status/info
icons/status/success
icons/status/warning
icons/status/error
icons/status/loading
icons/social/github
icons/social/linkedin
icons/social/twitter
icons/social/mail
icons/misc/user
icons/misc/bell
icons/misc/calendar
icons/misc/clock
icons/misc/star
icons/misc/heart
```

### Variant System

For components with multiple variant axes, prefer native **variant properties** over encoding everything in the slash-name. The slash-name creates the folder hierarchy in the assets panel; the variant system handles property switching.

Example for Button:
```
Component name in assets:  atoms/button
Variant properties:
  - style:  primary | secondary | outline | ghost | danger
  - size:   sm | md | lg
  - state:  default | hover | active | disabled | loading
  - icon:   true | false
```

All variant instances live inside a **variant area** on the canvas. The workflow:
1. Create each individual variant as a component
2. Select all → Combine as variants
3. The tool auto-generates property names and values from component names

### Component Annotations

Every main component MUST have an annotation:

```
Purpose: [one-line description]
Tokens: [list of tokens this component consumes]
Slots: [replaceable nested component slots, if any]
States: [all states this component supports]
Accessibility:
  - Role: [ARIA role, e.g., button, dialog, alert]
  - Keyboard: [key interactions, e.g., Enter/Space to activate, Escape to close]
  - Focus: [focus ring style, tab order notes]
  - Screen reader: [aria-label pattern or live region behavior]
Responsive: [how it adapts — e.g., "Full width below 768px", "Icon-only below 480px"]
Do: [1-2 correct usage examples]
Don't: [1-2 common mistakes to avoid]
```

Example for Modal:
```
Purpose: Confirmation dialog for destructive actions
Tokens: --bg-body, --txt-primary, --action-danger-bg, --radius-modal, --duration-normal, --easing-enter
Slots: icon (optional), body content, action buttons
States: open, closing (exit animation)
Accessibility:
  - Role: dialog with aria-modal="true"
  - Keyboard: Escape closes, Tab trapped inside, autofocus on cancel button
  - Focus: returns to trigger element on close
  - Screen reader: aria-labelledby on title, aria-describedby on body
Responsive: max-width 480px centered on desktop, full-width sheet from bottom on mobile
Do: Use for irreversible actions (delete, disconnect, remove access)
Don't: Don't use for simple confirmations ("Are you sure you want to save?") — just save
```

---

## 3. Typography Scale

> **Methodology:** Sizes derived from a Major Third (1.25) scale ratio starting at 16px base, snapped to nearest multiple of 4. Line heights use ×1.2 for headings and ×1.5 for body, also snapped to 4px grid. Adjust ratio and base for your project — Minor Third (1.2) for conservative apps, Perfect Fourth (1.333) for dramatic marketing.

| Style | Font | Size | Line Height | Weight | Usage |
|-|-|-|-|-|-|
| heading/h1 | Inter | 60px | 72px | 700 | Page titles, hero headlines |
| heading/h2 | Inter | 48px | 56px | 700 | Section headers |
| heading/h3 | Inter | 40px | 48px | 600 | Subsections |
| heading/h4 | Inter | 32px | 40px | 600 | Card titles, panel headers |
| heading/h5 | Inter | 24px | 28px | 600 | Subheadings |
| heading/h6 | Inter | 20px | 24px | 600 | Label headings |
| body/lg | Inter | 18px | 28px | 400 | Lead text |
| body/md | Inter | 16px | 24px | 400 | Main content |
| body/sm | Inter | 14px | 20px | 400 | Secondary content |
| caption/default | Inter | 12px | 16px | 400 | Labels, hints |
| caption/strong | Inter | 12px | 16px | 500 | Emphasized captions |
| label/default | Inter | 14px | 20px | 500 | Form labels |
| label/sm | Inter | 12px | 16px | 500 | Small labels |
| mono/default | JetBrains Mono | 14px | 20px | 400 | Code blocks |
| mono/sm | JetBrains Mono | 12px | 16px | 400 | Inline code |
| overline/default | Inter | 11px | 16px | 600 | Uppercase, letter-spacing 0.05em |

**Responsive typography rule:** Body text stays 16px on all breakpoints. Only headings scale down on mobile. See the responsive table in `typography.md` for desktop→mobile mappings.

---

## 4. Layout & Grid System

### Breakpoints

| Name | Width | Columns | Gutter | Margin |
|-|-|-|-|-|
| mobile | 375px | 4 | 16px | 16px |
| tablet | 768px | 8 | 24px | 32px |
| desktop | 1440px | 12 | 24px | 80px |
| wide | 1920px | 12 | 32px | 160px |

### Spacing Scale (4px base)

```
4  →  xs (tight: icon padding, badge padding)
8  →  sm (input padding, small gaps)
12 →  md-sm (form field gap)
16 →  md (standard gap between elements)
20 →  md-lg
24 →  lg (card padding, section inner gap)
32 →  xl (between related sections)
48 →  2xl (between distinct sections)
64 →  3xl (major section dividers)
80 →  4xl (page-level vertical rhythm)
```

### Frame Sizes for Responsive Design

```
Desktop:  1440 × auto (content height)
Tablet:    768 × auto
Mobile:    375 × auto
```

---

## 5. Motion & Animation

### Duration Scale

| Token | Value | Usage |
|-|-|-|
| `duration/instant` | 100ms | Hover state changes, toggle switches, focus rings |
| `duration/fast` | 150ms | Button feedback, tooltip show/hide, badge count update |
| `duration/normal` | 250ms | Dropdown open/close, card hover lift, nav item highlight |
| `duration/slow` | 350ms | Modal enter/exit, sidebar expand/collapse, accordion |
| `duration/deliberate` | 500ms | Page transitions, skeleton → content reveal, onboarding steps |

### Easing Curves

| Token | Value | Usage |
|-|-|-|
| `easing/default` | `cubic-bezier(0.4, 0, 0.2, 1)` | General purpose — most transitions |
| `easing/enter` | `cubic-bezier(0, 0, 0.2, 1)` | Elements appearing: modals, dropdowns, toasts |
| `easing/exit` | `cubic-bezier(0.4, 0, 1, 1)` | Elements disappearing |
| `easing/bounce` | `cubic-bezier(0.34, 1.56, 0.64, 1)` | Playful micro-interactions only (badge bump, success check) |

### Animation Rules

- **Prefer opacity + transform only.** Never animate `width`, `height`, `margin`, or `box-shadow` — they trigger layout recalculation.
- **Respect prefers-reduced-motion.** Every animation must have a `@media (prefers-reduced-motion: reduce)` fallback.
- **Purposeful only.** Animation must communicate state change, provide feedback, or guide attention. Never animate for decoration.
- **No animation on initial page load** — elements render in their final state. Animation triggers on user interaction or state change only.

### Animation Annotation Format

Document animation intent on components:
```
Animation: opacity 0→1 + translateY(8px→0), duration/normal, easing/enter
Trigger: on mount / on dropdown open / on hover
Reduced motion: instant opacity 0→1, no transform
```

---

## 6. Pattern Recipes

### Layout Templates

```
patterns/layout/sidebar-content     ← 256px sidebar + fluid main area
patterns/layout/top-nav-content     ← 64px top bar + fluid main area
patterns/layout/centered-narrow     ← max-width 640px centered column
patterns/layout/centered-wide       ← max-width 1200px centered column
patterns/layout/two-column          ← 50/50 or 60/40 split
patterns/layout/three-column        ← 33/33/33 split
```

### Section Recipes (Landing Pages & Marketing)

```
patterns/section/hero-split         ← Text left, image right
patterns/section/hero-centered      ← Centered headline + CTA + bg image
patterns/section/features-grid      ← 3-column icon + text grid
patterns/section/features-alternating ← Image/text alternating rows
patterns/section/pricing-table      ← 2-3 plan cards side by side
patterns/section/testimonials       ← Quote cards carousel/grid
patterns/section/cta-banner         ← Full-width call-to-action strip
patterns/section/faq-accordion      ← Question/answer expandable list
patterns/section/logo-cloud         ← Row of partner/client logos
patterns/section/stats-row          ← 3-4 metric cards in a row
patterns/section/team-grid          ← Team member cards
patterns/section/footer-standard    ← Multi-column footer with links
```

### State Patterns

```
patterns/state/empty                ← Illustration + headline + description + CTA
patterns/state/loading-skeleton     ← Shimmer/pulse placeholder blocks
patterns/state/error-page           ← Error icon + message + retry button
patterns/state/no-results           ← Search illustration + suggestion text
patterns/state/offline              ← Offline icon + reconnect message
```

---

## 7. UX Decision Patterns

### Forms & Validation

**Label placement:** Labels always above the input (not inline, not to the left). Most accessible and space-efficient.

**Placeholder text** is NOT a substitute for labels. Use for example values only (e.g., "jane@example.com").

**Required fields:** Mark with red asterisk (*), absolute-positioned to the left of the label so it doesn't push labels out of alignment. If most fields are required, instead mark optional fields with "(optional)".

**Validation timing:** Validate on blur (when user leaves the field), not on every keystroke. Show inline error below field using `molecules/form-field/error`. Error text uses danger color and starts with what's wrong:
- Good: "Email address is not valid"
- Bad: "Error: Please enter a valid email address"

**Field grouping:**
- Related fields grouped with a fieldset label ("Contact information", "Billing address")
- Spacing within group: `spacing/md` (16px)
- Spacing between groups: `spacing/xl` (32px)

**Submit behavior:**
- Primary action button at bottom-left (LTR)
- Secondary action (Cancel) as ghost button to the right
- Disable submit while submitting (loading variant)
- Inline success feedback or redirect — never a separate success page for simple forms

### Feedback & Notifications

| Situation | Component | Behavior |
|-|-|-|
| Action succeeded (save, delete, send) | `molecules/toast/success` | Auto-dismiss after 5s |
| Action failed (network error) | `molecules/toast/error` | Persist until dismissed. Include retry if applicable |
| Informational update (new feature, tip) | `molecules/toast/info` | Auto-dismiss after 8s |
| Destructive confirmation (delete account) | `organisms/modal/confirm` | Require explicit action. Never auto-dismiss |
| System-wide warning (maintenance) | `molecules/alert/warning` | Persistent banner. Dismissible but re-shows until resolved |
| Field-level validation | `molecules/form-field/error` | Inline below field. Appears on blur, clears on fix |
| Permission denied | `patterns/state/error` | Full-page or section-level with explanation and action |

**Never stack more than 3 toasts.** If a 4th triggers, dismiss the oldest.

### Data Display

| Data shape | Component | Use when |
|-|-|-|
| Structured rows, sortable columns | `organisms/data-table` | >5 items with 3+ attributes each |
| Homogeneous items, visual preview | `molecules/card` in grid | Products, team members, projects |
| Sequential items, time-based | Vertical list with dividers | Activity feeds, notifications, changelogs |
| Single key metric | `molecules/card/stat` | Dashboard summary numbers |
| Key-value pairs | Definition list (label: value rows) | Profile details, settings, receipts |

**Table rules:**
- Always include a header row
- Numeric columns right-aligned. Text columns left-aligned
- Default sort by most relevant column (usually date or name)
- Pagination if >20 rows. Use `molecules/pagination/default`
- Empty table shows `patterns/state/empty` inside the table container — never a blank grid

---

## 8. Product Screen Patterns

### Landing Page

```
landing/desktop         ← Full composition at 1440px:
                           - organisms/header (sticky)
                           - patterns/section/hero-centered
                           - patterns/section/logo-cloud
                           - patterns/section/features-grid
                           - patterns/section/features-alternating
                           - patterns/section/pricing-table
                           - patterns/section/testimonials
                           - patterns/section/cta-banner
                           - patterns/section/faq-accordion
                           - organisms/footer/mega
landing/tablet          ← Same sections, 768px reflow
landing/mobile          ← Same sections, 375px stack
```

### Dashboard

```
dashboard/default       ← sidebar-nav + header + stat cards + data table
dashboard/empty         ← sidebar-nav + header + empty state pattern
dashboard/loading       ← sidebar-nav + header + skeleton loading
dashboard/detail-panel  ← sidebar-nav + header + split view with detail panel
```

### Settings

```
settings/profile        ← Form fields: name, email, avatar upload
settings/account        ← Password change, 2FA, delete account
settings/preferences    ← Toggles, dropdowns for notification prefs
settings/billing        ← Plan card, payment method, invoice table
```

### Auth Flows

```
auth/login              ← Centered card: email + password + submit + social login
auth/register           ← Centered card: name + email + password + confirm + submit
auth/forgot-password    ← Centered card: email + submit
auth/reset-password     ← Centered card: new password + confirm + submit
auth/verify-email       ← Centered card: illustration + message + resend link
```

### Onboarding

```
onboarding/step-1       ← Welcome + role selection
onboarding/step-2       ← Workspace setup
onboarding/step-3       ← Invite team / skip
onboarding/complete     ← Success + go to dashboard
```

---

## 9. Content & Voice

### Tone

Professional, clear, and warm. Not robotic, not playful. Think helpful colleague, not chatbot and not legal document.

| Context | Tone | Example |
|-|-|-|
| Success feedback | Warm, brief | "Changes saved" — not "Your changes have been successfully saved!" |
| Error message | Direct, helpful | "Couldn't connect. Check your internet and try again." |
| Empty state | Encouraging | "No projects yet. Create your first one to get started." |
| Destructive action | Serious, specific | "Delete this project? This removes all files and can't be undone." |
| Onboarding | Friendly, guiding | "Let's set up your workspace. This takes about 2 minutes." |
| Labels and buttons | Action-oriented | "Save changes" not "Submit", "Create project" not "OK" |

### Grammar Rules

| Rule | Standard | Example |
|-|-|-|
| Casing for UI labels | Sentence case | "Create new project" not "Create New Project" |
| Casing for headings | Sentence case | "Getting started" not "Getting Started" |
| Button labels | Verb + noun | "Save changes", "Delete project", "Send invite" |
| Avoid | "Please", "Successfully", "Error:" prefix | Just state what happened or what to do |
| Punctuation | No periods on single-sentence UI text | Toast: "Changes saved" not "Changes saved." |
| Punctuation | Periods on multi-sentence text | Error: "Couldn't save. Try again in a few minutes." |
| Date format | Relative for recent, absolute for old | "2 hours ago", "Yesterday", "Mar 15, 2026" |
| Numbers | Separators for >999 | "1,234" not "1234" |
| Truncation | Single character ellipsis | "Very long project na…" |

### Terminology Glossary

| Preferred | NOT | Context |
|-|-|-|
| Log in | Sign in, Login | Authentication action |
| Log out | Sign out, Logout | De-authentication |
| Sign up | Register, Create account | New user registration |
| Email | Email address, E-mail | Form labels |
| Password | Passcode, Secret | Form labels |
| Project | Workspace, Space | Primary container — adapt to product |
| Settings | Preferences, Configuration | User config area |
| Delete | Remove, Destroy | Destructive action |
| Cancel | Dismiss, Close, Nevermind | Abort action |
| Save | Apply, Confirm, Submit | Persist action |

---

## 10. Icon Specifications

- Grid: 24x24px viewBox
- Stroke-based, 1.5px stroke width
- No fills (outline style)
- Corner radius on strokes: round caps, round joins
- Consistent 2px padding from edge (20x20 active area within 24x24 grid)
- Recommended set: Lucide (open source, consistent with shadcn ecosystem)
- Each icon is a component: `icons/{category}/{name}`
- Wrap SVG paths in a frame component for consistent sizing

---

## 11. Responsive Behavior Rules

| Pattern | Implementation |
|-|-|
| Stack on mobile | Horizontal flex → vertical flex at mobile breakpoint |
| Hide on mobile | Create separate mobile variant without the element |
| Full-width on mobile | Fixed width on desktop → `fill` on mobile |
| Sidebar collapse | Expanded sidebar → collapsed variant → mobile drawer variant |
| Grid reflow | 3-col grid on desktop → 2-col on tablet → 1-col stacked on mobile |

For each organism and pattern, create **three frames** at the standard breakpoints (1440, 768, 375). These show the same component at different container widths to document responsive behavior.

---

## 12. Accessibility Standards

### Target: WCAG 2.2 Level AA

### Color Contrast

| Element | Minimum | Notes |
|-|-|-|
| Body text (< 18px) | 4.5:1 | Against its background |
| Large text (>= 18px or >= 14px bold) | 3:1 | Against its background |
| UI components (borders, icons, controls) | 3:1 | Against adjacent colors |
| Focus indicators | 3:1 | Against both component and background |
| Decorative elements | No requirement | Non-functional exempt |

### Contrast-Safe Token Pairings

| Background | Safe Text | Ratio |
|-|-|-|
| `bg/body` (white) | `txt/primary` (gray-900) | 15.4:1 |
| `bg/body` (white) | `txt/secondary` (gray-500) | 4.6:1 |
| `bg/surface` (gray-50) | `txt/primary` (gray-900) | 13.9:1 |
| `bg/muted` (gray-100) | `txt/primary` (gray-900) | 12.1:1 |
| `action/primary-bg` (blue-600) | `action/primary-fg` (white) | 7.1:1 |
| `action/danger-bg` (red-500) | `action/danger-fg` (white) | 4.6:1 |
| `bg/inverse` (gray-900) | `txt/inverse` (white) | 15.4:1 |

**Rule: Never use `txt/muted` (gray-400) on `bg/body` (white) for essential content** — only ~3.1:1 ratio. Use only for decorative/supplementary text.

### Keyboard Navigation

- Every interactive element reachable via Tab
- Tab order follows visual reading order (top-to-bottom, left-to-right in LTR)
- Focus rings: 2px solid `border/focus` with 2px offset
- Focus trapping in modals: Tab cycles within, Escape closes, focus returns to trigger
- Skip links: every page with nav must have "Skip to main content" as first focusable element
- Custom components must implement WAI-ARIA patterns

### Required ARIA by Component

| Component | Required ARIA |
|-|-|
| Button | `role="button"` (native if `<button>`). `aria-label` if icon-only |
| Modal | `role="dialog"`, `aria-modal="true"`, `aria-labelledby` |
| Toast | `role="status"`, `aria-live="polite"` |
| Alert | `role="alert"`, `aria-live="assertive"` |
| Form input | `aria-describedby` → helper/error text. `aria-invalid="true"` on error |
| Toggle | `role="switch"`, `aria-checked` |
| Dropdown | `role="listbox"`, options `role="option"`, `aria-expanded` on trigger |
| Tabs | `role="tablist"`, `role="tab"`, `role="tabpanel"`. Arrow keys to switch |
| Data table | `role="table"` (native), `scope` on `<th>`, `aria-sort` on sortable |
| Spinner | `role="status"`, `aria-label="Loading"` |
| Sidebar nav | `role="navigation"`, `aria-label="Main"` |

### Accessibility Checklist

- [ ] All text meets 4.5:1 contrast (3:1 for large text)
- [ ] Interactive elements have visible focus rings
- [ ] No information conveyed by color alone
- [ ] All images/icons have text alternatives
- [ ] Form inputs have associated labels (not just placeholders)
- [ ] Error states announced to screen readers (aria-live)
- [ ] Modal focus trapped and returns correctly
- [ ] Custom widgets follow WAI-ARIA authoring patterns

---

## 13. Completeness Checklist

Before considering the design system complete:

### Phase 1: Token Foundation
- [ ] Define brand color palette (primary + error + success + warning + info + neutral)
- [ ] Build 50–950 scales for each color (opacity method → solid hex conversion)
- [ ] Define number scale (4px grid multiples)
- [ ] Set font family tokens (body, heading, mono)
- [ ] Set font weight tokens (regular, medium, semibold, bold)
- [ ] Create Primitive/Brand collection

### Phase 2: Semantic Layer
- [ ] Create Alias/Semantic collection with full shade ranges per group
- [ ] Add foundation values (white, black)
- [ ] Define border width aliases (default: 1px, focus: 2px)
- [ ] Define border radius aliases (sm through full)
- [ ] All semantic tokens reference primitives (no raw hex in semantic tier)

### Phase 3: Component/Mapped Tokens
- [ ] Create Mapped collection with four categories: text, icon, surface, border
- [ ] Define all state variants (default, hover, focus, disabled, error, success, etc.)
- [ ] Add `on-action` variants for content on primary surfaces
- [ ] Icon tokens mirror text tokens intentionally
- [ ] Scope variables to appropriate types (hide brand colors from component fills)

### Phase 4: Typography
- [ ] Generate type scale using ratio method (e.g., typescale.com)
- [ ] Snap all sizes to 4px grid
- [ ] Calculate line heights (×1.2 headings, ×1.5 body, snap to 4px)
- [ ] Create responsive collection with Desktop/Mobile modes
- [ ] Set paragraph spacing values
- [ ] Create all text styles (Heading/H1 through Body/XS-Link)
- [ ] All typographies registered in typography assets

### Phase 5: Theming
- [ ] Light + Dark theme defined and switchable
- [ ] Dark mode remaps semantic tier (not primitives)
- [ ] Test dark mode with accessibility contrast checker
- [ ] High contrast mode tokens defined (for EAA compliance)
- [ ] All semantic color pairings pass WCAG AA contrast

### Phase 6: Components (Build Order)
- [ ] Button (filled, outline, transparent × states × sizes)
- [ ] Label (default, required)
- [ ] Input Field (with all states) → Input (composed: Label + Field + Hint)
- [ ] Checkbox, Radio, Switch (selected/unselected × states) + label molecules
- [ ] Text Area, Menu (from .menu-item), Tab Bar (from .tab-item)
- [ ] Button Group, Link + breadcrumb, Avatar + group, Tag/Chip, Badge
- [ ] Loader, Progress Bar + circle, Snackbar/Toast
- [ ] Button Icon, Carousel, Table (cells → columns → table)
- [ ] Every atom has all states (default/hover/active/disabled/focus)
- [ ] Every molecule shows which atoms it composes
- [ ] Every organism has responsive frames (desktop/tablet/mobile)
- [ ] Every main component has an annotation
- [ ] Internal components prefixed with dot (.)
- [ ] Icon set covers navigation, action, status, and social categories
- [ ] Empty/loading/error states documented for every data-driven screen

### Phase 7: Accessibility Audit
- [ ] All focus states implemented with 2px visible ring
- [ ] All interactive elements have ≥24px touch targets (AA), prefer 44px
- [ ] All text/surface combinations meet WCAG AA contrast (4.5:1 / 3:1)
- [ ] Focus ring tokens defined
- [ ] Reduced motion tokens defined
- [ ] High contrast mode tokens defined (EAA)
- [ ] Accessibility annotations on every interactive component

### Phase 8: Publish & Distribute
- [ ] Review all component names (no accidental `.` prefixes on public components)
- [ ] Publish library
- [ ] Export tokens as W3C DTCG JSON
- [ ] Transform to CSS custom properties via Style Dictionary
- [ ] Integrate with Tailwind v4 `@theme` block
- [ ] Document the token API for developers
- [ ] Cover page has current version and changelog
- [ ] Design principles documented on getting-started page
- [ ] Voice and tone guidelines documented
- [ ] Terminology glossary defined and consistent
- [ ] Form validation pattern documented
- [ ] Feedback pattern decision table documented
- [ ] Data display guidance documented
- [ ] Motion tokens defined (duration scale + easing curves)
