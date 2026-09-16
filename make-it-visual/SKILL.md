---
name: make-it-visual
description: Visual-first design rules for any "visual" deliverable — app mockups, reports, slide decks, dashboards, one-pagers, docs, landing pages. Use whenever you are about to produce something a human will LOOK at rather than read line by line, or when asked to redesign something that is too text-heavy. Enforces show-don't-tell, minimal text, icons, diagrams, plots, accent color discipline, info popups for instructional text, and subtle motion.
---

# Make It Visual

AI-generated deliverables default to walls of text. Humans don't read walls of text; they scan. This skill flips the default: **every unit of information starts as a visual, and text is what's left over.**

## The one rule

> If it can be shown, show it. If it must be said, say it in under ten words. If it needs more than that, hide it behind an info popup.

## Decision ladder

Before writing any block of text, walk down this ladder and stop at the first rung that works:

1. **Image / screenshot / mockup** — the actual thing
2. **Diagram / workflow / flow arrows** — how things connect or move
3. **Plot / chart / sparkline** — anything with numbers over time or categories
4. **Big number + label** — a single metric (`42%` / `conversion`)
5. **Icon + 2–4 word label** — a feature, status, category, or step
6. **One short sentence** — a claim or instruction
7. **Info popup (ⓘ)** — anything longer than one sentence
8. **Paragraph** — almost never. If you write one, you probably skipped a rung.

## Text budget

| Surface | Hard limit |
|---|---|
| Headline | ≤ 6 words |
| Subhead / label | ≤ 10 words |
| Card / tile body | ≤ 1 sentence |
| Slide | ≤ 25 words visible |
| Report section | 1 visual + ≤ 2 sentences |
| Anything else | → info popup |

Cut filler first: "In order to", "It is important to note", "This section describes", adjectives, hedges. Then cut again.

## Show, don't tell — conversions

| Instead of… | Do this |
|---|---|
| Describing a process in prose | Numbered flow with arrows and icons |
| Listing features as bullets | Icon grid, 1 icon + 2–3 word label each |
| Explaining a comparison | Side-by-side table, or two-column before/after |
| Quoting statistics in a sentence | Stat tile (big number, small label, optional sparkline) |
| Narrating a trend | Line or bar chart with the takeaway as the title |
| Describing UI behavior | Mockup or annotated screenshot |
| Listing steps to use something | Numbered stepper with one verb per step |
| A "how it works" paragraph | Architecture / workflow diagram |
| Caveats, methodology, definitions | Info popup or footnote, never inline |
| Status text ("completed", "in progress") | Colored dot / badge / progress bar |

## Icons and logos

- Use a **single consistent icon set** (Lucide, Phosphor, Heroicons, Tabler). Never mix sets.
- **Stroke icons, one weight**, monochrome. Color only when the icon carries meaning (status, category).
- Every icon gets a label. Icons alone are ambiguous; labels alone are boring.
- Real logos for real products/vendors when identifying them (integrations, stacks, partners). Keep them grayscale unless the logo *is* the point.
- No emoji as icons in polished deliverables. Emoji are fine in chat and quick internal notes.

## Diagrams, workflows, plots

- **Diagram title = the takeaway**, not the subject. "Latency drops 60% after caching", not "Latency chart".
- Left→right or top→bottom flow. One direction per diagram.
- ≤ 7 nodes per diagram. More than that, split it or zoom out.
- Plots: one message per chart, direct labels over legends, no gridline clutter, no 3D, no pie charts with > 3 slices.
- Highlight the one series or bar that matters with the accent color; everything else neutral.
- Prefer real data. If mocking data, make it plausible and label it as illustrative.

## Images and mockups

- A real screenshot beats a description of the screen every time.
- Mockups: realistic content, not lorem ipsum. Realistic numbers, names, states.
- Annotate with numbered callouts, keep the explanation for each in a popup or side rail.
- Give every image room to breathe. Don't crowd it with text.

## Accent color

- **One accent color.** Two at most (primary + one semantic like success/danger).
- Accent goes on: the CTA, the key number, the highlighted series, the active state, the one thing you want eyes on first.
- Accent does *not* go on: headings, body text, backgrounds, borders, every icon.
- Everything else is a neutral scale (grays, off-whites, near-blacks). If more than ~10% of the surface is accent, it's not an accent anymore.
- Semantic colors are fixed: green = good/done, amber = warning/pending, red = bad/blocked. Don't reuse them decoratively.
- Check contrast. Accent on white needs to hit 4.5:1 for text, 3:1 for large text and UI.

## Info popups

Instructional and explanatory text that is genuinely needed still shouldn't be visible by default.

- Attach a small **ⓘ** (or `?`) trigger next to the element it explains.
- Reveal on hover (desktop) **and** click/tap (touch). Never hover-only.
- Popup content: ≤ 3 short sentences, or a tiny list. If it needs more, link out.
- Use for: definitions, methodology, "why this number", caveats, keyboard shortcuts, how-to-use.
- Do not use for: anything the user must know to avoid a mistake. That stays visible, in one line.
- Give the same instruction once, not on every instance.

## Subtle motion

Motion should confirm, guide, or reveal. It should never perform.

- **Durations:** 150–300 ms for UI feedback, 300–600 ms for reveals and diagram builds. Nothing over 1 s.
- **Easing:** ease-out for entering, ease-in for leaving. No bounce, no elastic.
- Good uses: fade-and-rise on scroll, count-up on stat tiles, sequential reveal of workflow steps, animated path drawing on diagrams, hover lift on cards, chart bars growing in.
- Bad uses: looping background animations, parallax, spinning logos, anything that moves while the user is trying to read.
- Animate **once** on entry, then hold still. Respect `prefers-reduced-motion` and drop motion entirely when set.
- Slides: builds are fine (one element per click). Transitions between slides: fade or none.

## Layout defaults

- Generous whitespace. When in doubt, double the padding.
- Grid, not stack. Cards in 2–4 columns on desktop, single column on mobile.
- One visual focal point per screen / slide / section.
- Type scale of 3 sizes max: display, body, caption. Weight does the rest.
- Align everything to the grid. Misalignment reads as sloppy faster than any other flaw.

## Per-format quick rules

**Slide deck** — 1 idea per slide. Title is the takeaway. One visual fills the slide. Speaker notes hold the words.

**Report** — Lead with a summary of 3–5 stat tiles. Each section: takeaway title, one visual, ≤ 2 sentences. Appendix for the long stuff.

**Dashboard** — Top row is KPIs. Charts below, each answering one question. Filters and definitions behind popups.

**App mockup** — Realistic data, real states (empty, loading, error, success). Annotate with callouts, not paragraphs.

**Doc / one-pager** — Hero visual or diagram at top. Sections as icon-led cards. Instructions as a stepper. Details collapsed or in popups.

**Landing page** — Show the product in the first viewport. Every feature is an icon + label + visual, not a paragraph.

## Before you ship — checklist

- [ ] Could any block of text be a visual instead? (Walk the ladder.)
- [ ] Is every visible text element under its budget?
- [ ] One icon set, one weight, all labeled?
- [ ] Does every chart/diagram title state the takeaway?
- [ ] One accent color, used only on what matters?
- [ ] Is instructional / explanatory text behind a popup?
- [ ] Does motion run once, under 600 ms, and respect reduced-motion?
- [ ] One focal point per screen?
- [ ] Would someone get the point in 5 seconds without reading anything?

If the last one fails, you're not done.
