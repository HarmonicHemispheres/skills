#!/usr/bin/env python3
"""Score make-it-visual A/B runs against the skill's own rules.

Each run folder (e.g. app-dashboard/with_skill/) holds a dashboard.html built
from the same prompt. This renders each one in headless Chrome, saves
screenshots, measures the rendered page, and writes metrics.json + grading.json
per run (grading.json uses skill-creator's schema), plus a side-by-side
compare.html for the whole eval.

    pip install playwright pillow   # drives your installed Chrome; no browser download
    python make-it-visual/evals/measure.py make-it-visual/evals/app-dashboard
"""

import colorsys
import json
import re
import sys
from datetime import date
from pathlib import Path

from PIL import Image
from playwright.sync_api import sync_playwright

VIEWPORT = {"width": 1440, "height": 900}
RUNS = {"without_skill": "Without skill", "with_skill": "With make-it-visual"}
PAGE = "dashboard.html"

# Visible words in the rendered DOM. A word counts only if its element is
# rendered, non-transparent and bigger than 1px (so sr-only text, closed
# popovers and opacity:0 tooltips don't count). Text inside <svg> is
# skipped so chart labels aren't counted as prose; canvas charts have no DOM
# text, so this keeps SVG and canvas charts comparable.
TEXT_JS = r"""
() => {
  const words = s => (s.match(/[\p{L}\p{N}]\S*/gu) || []).length;
  const shown = el => {
    if (!el.checkVisibility({ checkOpacity: true, checkVisibilityCSS: true })) return false;
    const r = el.getBoundingClientRect();
    return r.width > 1 && r.height > 1;
  };
  const blockOf = el => {
    for (let n = el; n && n !== document.body; n = n.parentElement) {
      const d = getComputedStyle(n).display;
      if (!d.startsWith('inline') && d !== 'contents') return n;
    }
    return document.body;
  };
  const out = { visible: 0, longest: 0, longestText: '', paragraphs: 0, sizes: {} };
  const blocks = new Map();
  const texts = [];
  const walker = document.createTreeWalker(document.body, NodeFilter.SHOW_TEXT);
  for (let t = walker.nextNode(); t; t = walker.nextNode()) {
    const el = t.parentElement;
    if (!el || el.closest('script,style,noscript,template,svg')) continue;
    const n = words(t.textContent);
    if (!n) continue;
    if (!shown(el)) continue;
    out.visible += n;
    texts.push(t.textContent);
    const b = blockOf(el);
    blocks.set(b, (blocks.get(b) || 0) + n);
    const fs = getComputedStyle(el).fontSize;
    out.sizes[fs] = (out.sizes[fs] || 0) + n;
  }
  for (const [b, n] of blocks) {
    if (n > 25) out.paragraphs++;
    if (n > out.longest) {
      out.longest = n;
      out.longestText = b.innerText.replace(/\s+/g, ' ').trim().slice(0, 160);
    }
  }
  const text = texts.join(' ');
  out.emoji = [...new Set(text.match(/\p{Emoji_Presentation}|\p{Extended_Pictographic}\u{FE0F}/gu) || [])];

  // Small standalone SVGs are icons. (Charts aren't counted: CSS-drawn bars
  // would be missed, and the screenshots show them anyway.)
  out.icons = [...document.querySelectorAll('svg')].filter(s => {
    if ((s.parentElement && s.parentElement.closest('svg')) || !shown(s)) return false;
    const r = s.getBoundingClientRect();
    return Math.max(r.width, r.height) <= 32;
  }).length;
  out.height = document.documentElement.scrollHeight;
  return out;
}
"""

# Candidate info-popup triggers: clickable or focusable elements that are small
# "i"/"?" buttons, or whose label or class says info/help/tip. Links are skipped
# so the test never navigates.
TRIGGERS = ('button, [role="button"], summary, [tabindex]:not([tabindex="-1"]), '
            '[popovertarget], [aria-describedby], [data-tip], [data-tooltip]')
IS_TRIGGER_JS = r"""
el => {
  if (!(el instanceof HTMLElement) || el.closest('a[href]')) return false;
  const text = el.innerText.trim();
  const label = `${el.getAttribute('aria-label') || ''} ${el.getAttribute('title') || ''}`;
  const cls = el.getAttribute('class') || '';
  return ['i', 'ⓘ', '?', 'ℹ', 'ℹ\u{FE0F}'].includes(text)
    || (text.split(/\s+/).length <= 3 && /\b(info|help|tips?|hints?)\b/i.test(text))
    || /\b(info|about|what|explain|help|tips?|hint|means?|how|learn)\b/i.test(label)
    || /(^|[\s_-])(info|tip|tooltip|help|hint|popover)/i.test(cls)
    || el.hasAttribute('popovertarget') || el.hasAttribute('data-tip') || el.hasAttribute('data-tooltip');
}
"""

MOTION = re.compile(r"@keyframes|animation\s*:|transition\s*:|requestAnimationFrame|\.animate\(|chart\.js|apexcharts|echarts", re.I)


def visible_words(page):
    return page.evaluate(TEXT_JS)["visible"]


def probe_popups(page, limit=40):
    """Open each info popup and count the words it reveals.

    Popups often build their text only when opened, so hidden DOM text says
    little; opening them is the real test. The mouse is parked away and each
    trigger is focused, then clicked, so a hover-only tooltip reveals nothing:
    the skill wants popups that also work on tap and keyboard.
    """
    # Stop live-updating demos (new orders every few seconds) so their changes
    # aren't mistaken for popup text. Timers set after this still run.
    page.evaluate("() => { const last = setTimeout(() => {}, 0); for (let i = 0; i <= last; i++) { clearTimeout(i); clearInterval(i); } }")
    found = opened = words = 0
    via = set()
    for handle in page.query_selector_all(TRIGGERS):
        if found >= limit:
            break
        if not handle.is_visible() or not handle.evaluate(IS_TRIGGER_JS):
            continue
        found += 1
        handle.scroll_into_view_if_needed()
        page.mouse.move(0, 0)
        base = visible_words(page)
        handle.focus()
        page.wait_for_timeout(250)
        gained, how = visible_words(page) - base, "focus"
        if gained < 5:
            handle.evaluate("el => { el.blur(); el.click(); }")
            page.wait_for_timeout(350)
            gained, how = visible_words(page) - base, "click"
            handle.evaluate("el => el.click()")
        page.keyboard.press("Escape")
        handle.evaluate("el => el.blur()")
        page.wait_for_timeout(200)
        if gained >= 5:
            opened += 1
            words += gained
            via.add(how)
    return {"triggers": found, "opened": opened, "words": words, "via": sorted(via)}


def color_profile(png):
    """Share of strongly saturated pixels, and the hue families they fall into."""
    img = Image.open(png).convert("RGB")
    img = img.resize((max(1, img.width // 3), max(1, img.height // 3)), Image.NEAREST)
    bins = [0] * 24
    sums = [[0, 0, 0] for _ in range(24)]
    total = saturated = 0
    data = img.tobytes()
    for k in range(0, len(data), 3):
        r, g, b = data[k], data[k + 1], data[k + 2]
        total += 1
        h, s, v = colorsys.rgb_to_hsv(r / 255, g / 255, b / 255)
        if s < 0.35 or v < 0.35:
            continue
        saturated += 1
        i = int(h * 24) % 24
        bins[i] += 1
        sums[i][0] += r
        sums[i][1] += g
        sums[i][2] += b

    # A family is a run of adjacent 15-degree hue bins that each hold >= 2% of
    # the saturated pixels, so one accent's light and dark shades count once.
    keep = [saturated and n / saturated >= 0.02 for n in bins]
    families = []
    if all(keep):
        runs = [list(range(24))]
    else:
        start = keep.index(False)
        runs, run = [], []
        for k in range(24):
            i = (start + k) % 24
            if keep[i]:
                run.append(i)
            elif run:
                runs.append(run)
                run = []
        if run:
            runs.append(run)
    for run in runs:
        n = sum(bins[i] for i in run)
        rgb = [sum(sums[i][c] for i in run) // n for c in range(3)]
        families.append({"hex": "#%02x%02x%02x" % tuple(rgb), "share": round(n / saturated, 3)})
    families.sort(key=lambda f: -f["share"])
    return round(saturated / total, 4) if total else 0.0, families


def measure_run(page, run_dir):
    html_path = run_dir / PAGE
    source = html_path.read_text(encoding="utf-8")
    page.goto(html_path.resolve().as_uri(), wait_until="networkidle")
    page.wait_for_timeout(1500)
    # Scroll through once so scroll-triggered reveals and count-ups finish.
    height = page.evaluate("document.documentElement.scrollHeight")
    for y in range(0, height, 600):
        page.evaluate(f"window.scrollTo(0, {y})")
        page.wait_for_timeout(120)
    page.evaluate("window.scrollTo(0, 0)")
    page.wait_for_timeout(1500)

    page.screenshot(path=run_dir / "viewport.png")
    page.screenshot(path=run_dir / "full.png", full_page=True)
    text = page.evaluate(TEXT_JS)
    popups = probe_popups(page)
    saturation, families = color_profile(run_dir / "full.png")

    has_motion = bool(MOTION.search(source))
    reduced = "prefers-reduced-motion" in source
    timing_file = run_dir / "timing.json"
    return {
        "visible_words": text["visible"],
        "popup_words": popups["words"],
        "popups_opened": popups["opened"],
        "popup_triggers": popups["triggers"],
        "popups_open_via": popups["via"],
        "longest_block_words": text["longest"],
        "longest_block_text": text["longestText"],
        "blocks_over_25_words": text["paragraphs"],
        "text_sizes": sorted(text["sizes"], key=lambda s: -float(s.rstrip("px"))),
        "emoji": text["emoji"],
        "icons": text["icons"],
        "page_height_px": text["height"],
        "screens_tall": round(text["height"] / VIEWPORT["height"], 1),
        "has_motion": has_motion,
        "reduced_motion": reduced,
        "saturated_share": saturation,
        "color_families": families,
        "file_kb": round(html_path.stat().st_size / 1024, 1),
        "timing": json.loads(timing_file.read_text()) if timing_file.exists() else None,
    }


def grade(m):
    """Pass/fail checks, each taken straight from a rule in SKILL.md."""
    def check(text, passed, evidence):
        return {"text": text, "passed": bool(passed), "evidence": evidence}

    fams = m["color_families"]
    return [
        check("No paragraphs: every visible text block is 25 words or fewer",
              m["blocks_over_25_words"] == 0,
              f"{m['blocks_over_25_words']} blocks over 25 words; longest is {m['longest_block_words']}: "
              f"\"{m['longest_block_text'][:100]}\""),
        check("Explanations and tips are on demand: popups reveal 30+ words",
              m["popup_words"] >= 30,
              f"{m['popups_opened']} popups revealed {m['popup_words']} words; {m['visible_words']} words always visible"),
        check("Info popups open on click or tap, not hover only",
              m["popups_opened"] > 0,
              f"{m['popups_opened']} of {m['popup_triggers']} info triggers opened via {' and '.join(m['popups_open_via'])}"
              if m["popups_opened"] else f"None of {m['popup_triggers']} info triggers opened without hovering"),
        check("Type scale: 3 text sizes or fewer (display, body, caption)",
              len(m["text_sizes"]) <= 3,
              f"{len(m['text_sizes'])} sizes: {', '.join(m['text_sizes'])}"),
        check("Motion respects prefers-reduced-motion",
              m["reduced_motion"] or not m["has_motion"],
              "Has a prefers-reduced-motion rule" if m["reduced_motion"]
              else ("No motion found" if not m["has_motion"] else "Animates, with no prefers-reduced-motion rule")),
        check("No emoji used as icons",
              not m["emoji"],
              f"Found {' '.join(m['emoji'])}" if m["emoji"] else "No emoji in visible text"),
        check("Accent discipline: saturated color covers 10% of the page or less",
              m["saturated_share"] <= 0.10,
              f"{m['saturated_share']:.1%} of pixels are strongly saturated"),
        check("At most 4 color families (one accent plus good, warning, bad)",
              len(fams) <= 4,
              f"{len(fams)} families: {', '.join(f['hex'] + ' ' + format(f['share'], '.0%') for f in fams)}"),
    ]


def write_compare(eval_dir, prompt, runs):
    template = (Path(__file__).parent / "compare_template.html").read_text(encoding="utf-8")
    data = {"prompt": prompt, "date": date.today().isoformat(), "viewport": VIEWPORT, "runs": runs}
    payload = json.dumps(data, ensure_ascii=False).replace("</", "<\\/")
    (eval_dir / "compare.html").write_text(template.replace("__DATA__", payload), encoding="utf-8")


def main():
    if len(sys.argv) != 2:
        sys.exit(__doc__)
    eval_dir = Path(sys.argv[1])
    evals = json.loads((Path(__file__).parent / "evals.json").read_text(encoding="utf-8"))["evals"]
    prompt = next((e["prompt"] for e in evals if e.get("name") == eval_dir.name), "")

    runs = []
    with sync_playwright() as p:
        browser = p.chromium.launch(channel="chrome")
        for run_id, label in RUNS.items():
            run_dir = eval_dir / run_id
            if not (run_dir / PAGE).exists():
                print(f"skip {run_id}: no {PAGE}")
                continue
            page = browser.new_page(viewport=VIEWPORT)
            m = measure_run(page, run_dir)
            page.close()
            expectations = grade(m)
            passed = sum(e["passed"] for e in expectations)
            summary = {"passed": passed, "failed": len(expectations) - passed,
                       "total": len(expectations), "pass_rate": round(passed / len(expectations), 2)}
            (run_dir / "metrics.json").write_text(json.dumps(m, indent=2, ensure_ascii=False), encoding="utf-8")
            (run_dir / "grading.json").write_text(
                json.dumps({"expectations": expectations, "summary": summary}, indent=2, ensure_ascii=False),
                encoding="utf-8")
            runs.append({"id": run_id, "label": label, "metrics": m,
                         "expectations": expectations, "summary": summary})
            print(f"{label}: {passed}/{len(expectations)} checks, {m['visible_words']} visible words, "
                  f"longest block {m['longest_block_words']}, {m['saturated_share']:.1%} saturated")
        browser.close()

    write_compare(eval_dir, prompt, runs)
    print(f"wrote {eval_dir / 'compare.html'}")


if __name__ == "__main__":
    main()
