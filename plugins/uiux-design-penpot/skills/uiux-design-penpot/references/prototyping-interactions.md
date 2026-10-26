# Prototyping & Interactions

## Contents

- Adding Interactions
- Triggers
- Actions
- Animations
- Flows
- Common Patterns

Add interactive behaviors to shapes for prototyping in Penpot's view mode.

## Adding Interactions

```javascript
const interaction = shape.addInteraction(trigger, action, delay?);
shape.removeInteraction(interaction);
```

## Triggers

| Trigger | Description |
|-|-|
| `"click"` | User clicks the shape |
| `"mouse-enter"` | Cursor moves over the shape |
| `"mouse-leave"` | Cursor moves away from the shape |
| `"after-delay"` | Fires after specified delay (ms) — requires `delay` parameter |

## Actions

### Navigate To

Navigate to a different board (screen):

```javascript
shape.addInteraction('click', {
  type: 'navigate-to',
  destination: targetBoard,
  preserveScrollPosition: false,
  animation: { type: 'dissolve', duration: 300, easing: 'ease-in-out' }
});
```

Properties:
- `type` — `"navigate-to"`
- `destination` — Board to navigate to
- `preserveScrollPosition` — boolean, keep scroll position
- `animation` — transition animation (optional)

### Open Overlay

Display a board as an overlay:

```javascript
shape.addInteraction('click', {
  type: 'open-overlay',
  destination: overlayBoard,
  position: 'center',
  closeWhenClickOutside: true,
  addBackgroundOverlay: true,
  animation: { type: 'slide', direction: 'right', duration: 300, easing: 'ease-in-out' }
});
```

Properties:
- `type` — `"open-overlay"`
- `destination` — Board to show as overlay
- `relativeTo` — Shape to position relative to (optional)
- `position` — `"center"` | `"manual"` | `"top-left"` | `"top-right"` | `"top-center"` | `"bottom-left"` | `"bottom-right"` | `"bottom-center"`
- `manualPositionLocation` — `{x, y}` point when position is `"manual"`
- `closeWhenClickOutside` — boolean
- `addBackgroundOverlay` — boolean, adds semi-transparent background
- `animation` — transition animation (optional)

### Toggle Overlay

Toggle overlay visibility:

```javascript
shape.addInteraction('click', {
  type: 'toggle-overlay',
  destination: overlayBoard,
  position: 'top-right',
  closeWhenClickOutside: true
});
```

Same properties as Open Overlay.

### Close Overlay

Close the current overlay:

```javascript
shape.addInteraction('click', {
  type: 'close-overlay',
  destination: overlayBoard  // the overlay to close
});
```

### Previous Screen

Navigate back:

```javascript
shape.addInteraction('click', { type: 'previous-screen' });
```

### Open URL

Open external link:

```javascript
shape.addInteraction('click', {
  type: 'open-url',
  url: 'https://example.com'
});
```

## Animations

Three animation types available for navigation and overlay actions:

### Dissolve

```javascript
{ type: 'dissolve', duration: 300, easing: 'ease-in-out' }
```

### Slide

```javascript
{ type: 'slide', direction: 'right', duration: 300, easing: 'ease-in-out', offsetEffect: true }
```

Direction: `"right"` | `"left"` | `"up"` | `"down"`

### Push

```javascript
{ type: 'push', direction: 'right', duration: 300, easing: 'ease-in-out' }
```

Direction: `"right"` | `"left"` | `"up"` | `"down"`

## Flows

Flows define entry points for prototyping sequences in view mode:

```javascript
// Create a flow (entry point for view mode)
const flow = penpot.currentPage.createFlow('Onboarding', startBoard);

// List existing flows
const flows = penpot.currentPage.flows;

// Remove a flow
penpot.currentPage.removeFlow(flow);
```

A Flow has:
- `name` — string, flow name
- `startingBoard` — Board, the entry board

## Common Patterns

### Multi-screen navigation flow

```javascript
const screens = penpotUtils.findShapes(s => s.type === 'board', penpot.root);
const [screen1, screen2, screen3] = screens;

// Find "Next" buttons on each screen
const nextBtn1 = penpotUtils.findShapes(s => s.name === 'btn-next', screen1)[0];
const nextBtn2 = penpotUtils.findShapes(s => s.name === 'btn-next', screen2)[0];

// Wire up navigation
nextBtn1.addInteraction('click', {
  type: 'navigate-to',
  destination: screen2,
  animation: { type: 'slide', direction: 'left', duration: 300, easing: 'ease-in-out' }
});

nextBtn2.addInteraction('click', {
  type: 'navigate-to',
  destination: screen3,
  animation: { type: 'slide', direction: 'left', duration: 300, easing: 'ease-in-out' }
});

// Add back buttons
const backBtn2 = penpotUtils.findShapes(s => s.name === 'btn-back', screen2)[0];
backBtn2.addInteraction('click', { type: 'previous-screen' });

// Create flow entry point
penpot.currentPage.createFlow('Main Flow', screen1);

return 'Navigation flow created with 3 screens';
```

### Modal dialog with overlay

```javascript
const triggerBtn = penpotUtils.findShapes(s => s.name === 'open-modal', penpot.root)[0];
const modalBoard = penpotUtils.findShapes(s => s.name === 'modal-dialog', penpot.root)[0];

triggerBtn.addInteraction('click', {
  type: 'open-overlay',
  destination: modalBoard,
  position: 'center',
  closeWhenClickOutside: true,
  addBackgroundOverlay: true,
  animation: { type: 'dissolve', duration: 200, easing: 'ease-in-out' }
});

// Close button inside the modal
const closeBtn = penpotUtils.findShapes(s => s.name === 'btn-close', modalBoard)[0];
closeBtn.addInteraction('click', {
  type: 'close-overlay',
  destination: modalBoard
});

return 'Modal dialog interaction set up';
```

### Hover tooltip

```javascript
const icon = penpotUtils.findShapes(s => s.name === 'info-icon', penpot.root)[0];
const tooltip = penpotUtils.findShapes(s => s.name === 'tooltip', penpot.root)[0];

icon.addInteraction('mouse-enter', {
  type: 'open-overlay',
  destination: tooltip,
  relativeTo: icon,
  position: 'top-center',
  closeWhenClickOutside: false,
  addBackgroundOverlay: false
});

icon.addInteraction('mouse-leave', {
  type: 'close-overlay',
  destination: tooltip
});

return 'Hover tooltip added';
```

### Auto-play splash screen

```javascript
const splashBoard = penpotUtils.findShapes(s => s.name === 'splash', penpot.root)[0];
const mainBoard = penpotUtils.findShapes(s => s.name === 'main', penpot.root)[0];

// Auto-navigate after 3 seconds
splashBoard.addInteraction('after-delay', {
  type: 'navigate-to',
  destination: mainBoard,
  animation: { type: 'dissolve', duration: 500, easing: 'ease-in-out' }
}, 3000); // 3000ms delay

return 'Splash screen auto-advance set up';
```
