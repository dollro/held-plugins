# Working in Claude for PowerPoint (add-in)

In the add-in there is no Python and no file system: you edit the open presentation directly. The method is the same; only the hands change.

## Order of work

1. **Read the master first.** Before creating any slide, inspect the slide master and its layouts: names, placeholders, theme colours, fonts, artwork (logo, bands, footer). If a `design-guide.md` was uploaded with the skill or pasted into the add-in's Instructions, follow it; it overrides your own reading.
2. **Agree the spine in the side panel.** Write the action titles (consult) or the slide-by-slide lines (keynote) as text in the chat and get a yes before touching slides, unless the user asked you to just build.
3. **One slide at a time, from layouts.** Insert each slide from the layout that fits its role (Title Only for consult content, Section Header for dividers, Blank or Picture layouts for keynote statements and images). Fill placeholders; do not draw text boxes over them.
4. **Exhibits as native objects.** Native charts and tables, theme colours (accent1 for the one highlight, greys for context), theme fonts.
5. **Speaker notes.** In keynote mode, write the talk into the notes of every slide.
6. **Review pass.** Run the `deck-review` checklist on the finished deck (no script here): read titles top to bottom, look at every slide for overflow, overlap with master artwork, more than one accent, sources and illustrative labels.

## Pinpoint edits

When the user asks to fix one slide, change that slide only. Keep its layout and placeholders; do not regenerate neighbours.

## Persistent setup for a team or brand

Put the short form of the design guide into the add-in's Instructions field (Settings), for example:

```
Template-first: use our master layouts and placeholders; never add fonts or colours.
Accent = accent1, only for the one thing per slide. Body 12-16 pt, titles are full-sentence action titles.
Keep clear of the logo (bottom right) and the red band (bottom).
Keynote slides: Blank layout, template fonts, statements 40-96 pt, one number per slide, notes carry the talk.
```

## Limits to state to the user

- Complex masters can still produce off-template output; always review.
- Animations and transitions: suggest them in the notes; do not rely on them for the story (use one-slide-per-step reveals instead).
- Images: only what the user provides; otherwise insert a labelled placeholder shape.
