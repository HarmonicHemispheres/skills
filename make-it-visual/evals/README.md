# make-it-visual evals

An A/B test: the same dashboard prompt, run once with the skill and once without, then measured against the skill's own rules.

```
evals/
├── evals.json              the prompt (skill-creator schema)
├── measure.py              renders, screenshots, scores, and builds compare.html
├── compare_template.html
└── app-dashboard/
    ├── compare.html        open this: both dashboards live, side by side, with scores
    ├── with_skill/         dashboard.html, screenshots, metrics.json, grading.json
    └── without_skill/
```

This folder is left out of the `.skill` package, so none of it ships to users.

## Checks

Each check is one rule from `SKILL.md`, measured on the rendered page in headless Chrome:

| Check | Skill rule |
|---|---|
| No visible text block over 25 words | Paragraphs: almost never |
| Opening the info popups reveals 30+ words | Explanations go behind info popups |
| Popups open by focus or click, mouse parked elsewhere | Hover and click/tap, never hover only |
| ≤ 3 distinct text sizes (chart labels excluded) | Type scale: display, body, caption |
| `prefers-reduced-motion` handled if anything animates | Respect reduced motion |
| No emoji in visible text | No emoji as icons |
| Saturated pixels ≤ 10% of the page | Over ~10% accent isn't an accent |
| ≤ 4 hue families | One accent + good / warning / bad |

Design quality ("would someone get the point in 5 seconds?") isn't scored. Judge that yourself in `compare.html`.

## Rerun

1. Generate both dashboards from the prompt in `evals.json`, each in a fresh session:
   - **with_skill**: tell Claude to read `make-it-visual/SKILL.md` and follow it.
   - **without_skill**: the prompt alone, no skills.

   Save each as `app-dashboard/<with_skill|without_skill>/dashboard.html`. Optionally add a `timing.json` (`total_tokens`, `total_duration_seconds`) to each folder.
2. Measure:

   ```bash
   pip install playwright pillow   # uses your installed Chrome
   python make-it-visual/evals/measure.py make-it-visual/evals/app-dashboard
   ```

Each side is a single run, so treat the numbers as a demo, not a benchmark. For a real benchmark, run several samples per side with skill-creator's eval loop. `grading.json` already uses its schema.
