# Circuit DNA — Race Engineering Bench UI Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Restyle `circuit_dna/index.html` to match the approved **Race engineering bench** visual system (graphite surfaces, amber accent, Fira typography, flat instrument panels, no generic teal-on-navy SaaS template look) without changing OpenF1 logic, chart semantics, or DOM IDs relied on by `scripts/verify_headless.py`.

**Architecture:** All presentation changes stay in the single-page file: Google Fonts in `<head>`, `:root` design tokens and component rules in the existing `<style>` block, and minimal semantic/markup additions (lane labels, similarity module wrapper) in static HTML. Chart.js/D3 data paths and element IDs (`#similarity-value`, `#diff-peaks`, `#left-chart`, `#right-chart`, `#diff-chart`, session/driver selects, retry buttons) remain stable. One JS edit aligns the **fallback** trace colour constant with the new accent when API team colour is missing.

**Tech Stack:** Static HTML, embedded CSS, vanilla JS (unchanged behaviour), Chart.js 4.x, D3 v7, optional Playwright verification via `circuit_dna/scripts/verify_headless.py`.

---

## Approved design specification (do not drift)

| Token | Role |
|--------|------|
| Page BG | `#0c0d10`–`#12141a` flat (optional ≤3% noise overlay on `body` only—not per chart well) |
| Panel BG | `#16181f`–`#1a1d26`, border `#2a2f3a` (neutral graphite, not blue-purple) |
| Primary accent (chrome, focus, active segment, key strokes) | Amber `#e8b84a` (hover slightly brighter; avoid neon glow) |
| Secondary “OK” | Muted `#7d9a7e` sparingly (pills, subtle positive hints—not dominant) |
| Danger | Desaturated red, readable on dark (reuse logical role of current `--danger`, tune hue if needed) |
| Typography | **Fira Sans** UI/body; **Fira Code** for similarity, lap/speed lines, table numerics, debug |
| Chart wells | **No** radial spotlight gradients; flat panel + thin inner frame (border or inset) |
| Motion | Transitions 150–220ms on color/border/opacity; **no** `translateY` on buttons; skeleton respects `prefers-reduced-motion` |
| Layout copy | Surface **Fingerprint A \| bridge \| Fingerprint B** (or Primary / Compare) so columns are labeled |

**Explicit non-goals:** No build step, no component framework, no HUD neon/scanlines, no change to v2 loading/timeout/retry behaviour described in `docs/circuit-dna-v2-design.md`.

---

## File map

| File | Responsibility |
|------|----------------|
| `circuit_dna/index.html` | Fonts, CSS tokens, HTML shell tweaks, optional class hooks, single JS constant rename/comment for fallback colour |
| `circuit_dna/scripts/verify_headless.py` | **Do not** change selectors `#similarity-value`, `#diff-peaks` text expectation `"Largest deltas"` unless implementation unavoidably rewrites copy (then update script in same PR) |

---

### Task 1: Design tokens and font loading

**Files:**
- Modify: `circuit_dna/index.html` ( `<head>` through `:root` )

- [ ] **Step 1: Add Fira Sans + Fira Code**

Insert before `<style>`:

```html
<link rel="preconnect" href="https://fonts.googleapis.com" />
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
<link
  href="https://fonts.googleapis.com/css2?family=Fira+Code:wght@400;500;600&family=Fira+Sans:wght@400;500;600;700&display=swap"
  rel="stylesheet"
/>
```

- [ ] **Step 2: Replace `:root` token block** with graphite + amber system (remove `--teal` as primary; keep semantic names):

```css
:root {
  color-scheme: dark;
  --bg-page: #0e1016;
  --bg-panel: #181b24;
  --bg-well: #14161d;
  --bg-soft: #1e222c;
  --border: #2e3440;
  --border-strong: #3d4654;
  --text: #eceef2;
  --muted: #8b93a6;
  --accent: #e8b84a;
  --accent-hover: #f0ca6a;
  --accent-muted: rgba(232, 184, 74, 0.22);
  --ok: #7d9a7e;
  --ok-muted: rgba(125, 154, 126, 0.2);
  --danger: #e85d6f;
  --danger-bg: rgba(232, 93, 111, 0.14);
  --font-ui: "Fira Sans", -apple-system, system-ui, sans-serif;
  --font-data: "Fira Code", ui-monospace, monospace;
}
```

- [ ] **Step 3: Smoke-check in browser**

Open `index.html` via local server; confirm fonts load (network tab) and no flash of wrong scheme.

---

### Task 2: Global base styles

**Files:**
- Modify: `circuit_dna/index.html` (`body`, `*`, `.app`)

- [ ] **Step 1: Wire body to tokens**

```css
body {
  margin: 0;
  font-family: var(--font-ui);
  background: var(--bg-page);
  color: var(--text);
}
```

- [ ] **Step 2: Optional single noise layer** (YAGNI default: skip unless you want texture—if added, use `body::before` fixed inset pointer-events-none opacity ~0.03 only)

---

### Task 3: Header toolbar and lane labels

**Files:**
- Modify: `circuit_dna/index.html` (header HTML + `.header`, `.title-row`, `.subtitle`)

- [ ] **Step 1: Add lane headings inside each column**

Inside `<article class="panel" id="left-panel">`, before `.selectors`, add:

```html
<p class="lane-label"><span class="lane-tag">A</span> Fingerprint</p>
```

Inside `<article class="panel" id="right-panel">`, before `.selectors`, add:

```html
<p class="lane-label"><span class="lane-tag">B</span> Fingerprint</p>
```

Inside `<article class="middle">`, as first child (or after wrapper), add bridge label:

```html
<p class="lane-label lane-label-center"><span class="lane-tag">Δ</span> Compare</p>
```

- [ ] **Step 2: CSS for lane labels**

```css
.lane-label {
  margin: 0 0 10px;
  font-size: 11px;
  font-weight: 600;
  letter-spacing: 0.12em;
  text-transform: uppercase;
  color: var(--muted);
  display: flex;
  align-items: center;
  gap: 8px;
}
.lane-label-center {
  justify-content: center;
}
.lane-tag {
  font-family: var(--font-data);
  font-size: 12px;
  letter-spacing: 0;
  color: var(--accent);
  border: 1px solid var(--border-strong);
  border-radius: 4px;
  padding: 2px 6px;
  background: var(--bg-well);
}
```

- [ ] **Step 3: Unify header control bar**

Replace inline `style="display: flex; ..."` on the controls wrapper with a class `.header-actions` and style `gap`, `flex-wrap`, `align-items: center`; add top border or padding so header reads as one **bench strip**.

---

### Task 4: Panels, chart wells, skeleton

**Files:**
- Modify: `circuit_dna/index.html` (`.panel`, `.middle`, `.grid-panel`, `.chart-wrap`, skeleton keyframes)

- [ ] **Step 1: Flatten chart wells**

Remove radial-gradient backgrounds from `.chart-wrap` and `.diff-chart`; use:

```css
.chart-wrap,
.diff-chart {
  background: var(--bg-well);
  border: 1px solid var(--border);
}
```

Add inner frame feel:

```css
.chart-wrap {
  box-shadow: inset 0 0 0 1px rgba(255, 255, 255, 0.03);
}
```

- [ ] **Step 2: Update skeleton ring** to amber-based conic stops (replace teal RGBA references with `rgba(232, 184, 74, …)`).

- [ ] **Step 3: `prefers-reduced-motion`**

```css
@media (prefers-reduced-motion: reduce) {
  .skeleton-ring {
    animation: none;
    opacity: 0.85;
  }
}
```

---

### Task 5: Similarity readout module and middle column

**Files:**
- Modify: `circuit_dna/index.html` (wrap similarity block + CSS)

- [ ] **Step 1: Wrap headline metric**

Wrap the similarity label + value in:

```html
<div class="readout-card">
  <div class="similarity-label">Cosine Similarity</div>
  <div class="similarity-value" id="similarity-value">--</div>
</div>
```

- [ ] **Step 2: Readout styling**

```css
.readout-card {
  border: 1px solid var(--border);
  border-radius: 10px;
  padding: 12px 14px;
  background: var(--bg-well);
}
.similarity-value {
  font-family: var(--font-data);
  font-variant-numeric: tabular-nums;
}
```

Keep `#similarity-value` id on the inner element for Playwright.

---

### Task 6: Buttons, segmented control, selects, sync checkbox

**Files:**
- Modify: `circuit_dna/index.html` (rules for `button`, `select`, `.mode-toggle`, `.sync-driver-label`)

- [ ] **Step 1: Remove layout-shift hover**

Delete `transform: translateY(-1px)` from `button:hover`; use border-color + background only.

- [ ] **Step 2: Amber active state for mode toggle**

`.mode-toggle button.active` should use `background: var(--accent-muted)` and `color: var(--accent-hover)` (or `--text` if contrast cleaner).

- [ ] **Step 3: Focus-visible**

```css
button:focus-visible,
select:focus-visible {
  outline: 2px solid var(--accent);
  outline-offset: 2px;
}
```

- [ ] **Step 4: Checkbox accent**

`accent-color: var(--accent);` on `.sync-driver-label input`.

---

### Task 7: Stats, pills, table, row hover

**Files:**
- Modify: `circuit_dna/index.html`

- [ ] **Step 1: Monospace stats**

```css
.stats .meta,
.stats .name {
  font-family: var(--font-data);
  font-variant-numeric: tabular-nums;
}
.stats .name {
  font-family: var(--font-ui);
  font-weight: 700;
  font-size: 17px;
}
```

(Adjust: circuit name can stay sans if preferred; lap/speed monospace minimum.)

- [ ] **Step 2: Pills use OK muted**

`.pill`: background `var(--ok-muted)`, color `var(--ok)` or lightened OK—not teal.

- [ ] **Step 3: Table**

`thead` background `var(--bg-soft)`; borders `var(--border)`; row hover:

```css
tbody tr:hover {
  background: rgba(232, 184, 74, 0.06);
  box-shadow: inset 3px 0 0 var(--accent);
}
```

Add `font-variant-numeric: tabular-nums` on `td` for numeric columns via class or `tbody td:nth-child(...)` if stable.

- [ ] **Step 4: Sort buttons**

Ensure `th button:focus-visible` matches global focus ring.

---

### Task 8: Panel status, retry, debug log

**Files:**
- Modify: `circuit_dna/index.html`

- [ ] **Step 1: Panel status/error**

Map `.panel-status.error` to `--danger` text and `--danger-bg`; success/neutral uses `--muted` on dark translucent bar.

- [ ] **Step 2: `.panel-retry`**

Align with outlined button style (border `--accent`, transparent BG).

- [ ] **Step 3: `.debug-log`**

Border/font consistent with bench (Fira Code already appropriate).

---

### Task 9: Chart fallback colour constant (JS)

**Files:**
- Modify: `circuit_dna/index.html` (script section only)

- [ ] **Step 1: Rename and retune**

Replace:

```javascript
const TEAL = "#1D9E75";
```

with:

```javascript
/** Fallback fingerprint stroke when team_colour missing — matches bench accent family */
const ACCENT_FALLBACK = "#D4A24C";
```

- [ ] **Step 2: Update references**

Every use of `TEAL` as fallback (e.g. `sanitizeColor` default, `driverObj ? … : TEAL`) → `ACCENT_FALLBACK`.

Do **not** change behaviour of `sanitizeColor` beyond default hex.

- [ ] **Step 3: Chart.js plugin / grid colours**

Search script for hardcoded `#1D9E75`, teal RGBA, or old grey hex tied to previous theme; align grid/ticks to `--border` / muted equivalents **only if** they are theme literals (avoid breaking data-driven team colours).

---

### Task 10: Verification

**Files:**
- Read: `circuit_dna/scripts/verify_headless.py`

- [ ] **Step 1: Manual checklist**

  - [ ] 375px / 768px / 1200px+: stacked vs 3-column breakpoint unchanged functionally
  - [ ] Keyboard tab through controls shows visible focus rings
  - [ ] Reduced motion: OS setting suppresses skeleton pulse
  - [ ] Load success path: both radars + similarity `%` + diff peaks text `"Largest deltas"` still appears

- [ ] **Step 2: Headless (optional if Playwright installed)**

```bash
cd circuit_dna && python3 scripts/verify_headless.py
```

Expected: exit code `0`; screenshots written under `circuit_dna/docs/` if script configures them; no JS console errors.

If OpenF1 returns 429 repeatedly, rely on script backoff; failure after retries is environment/API—not CSS regression.

- [ ] **Step 3: Git**

Stage changes and commit **only when** the repository owner explicitly requests a commit (project convention).

---

## Self-review (plan vs spec)

| Spec requirement | Task coverage |
|-------------------|---------------|
| Graphite surfaces, neutral borders | Task 1–2, 4 |
| Amber accent, spare OK green | Task 1, 6–7 |
| Fira Sans / Fira Code | Task 1, 5, 7 |
| Flat wells, no radial fills | Task 4 |
| Lane labels A / Δ / B | Task 3 |
| Similarity readout module | Task 5 |
| Motion + reduced motion | Task 4, 6 |
| JS fallback colour cohesion | Task 9 |
| Preserve verify_headless IDs/copy | Tasks 3–5, 10 |

**Placeholder scan:** No TBD/TODO left in tasks above.

---

Plan complete and saved to `circuit_dna/docs/superpowers/plans/2026-05-15-race-engineering-bench-ui.md`.

**Two execution options:**

1. **Subagent-driven (recommended)** — Dispatch a fresh subagent per task, review between tasks, fast iteration (`superpowers:subagent-driven-development`).

2. **Inline execution** — Run tasks in this session with checkpoints (`superpowers:executing-plans`).

Which approach do you want?
