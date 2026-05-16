# Circuit DNA — stability & UX specification (v2)

**Status:** Approved for implementation  
**Scope:** Single-page app — [`index.html`](../index.html) only (vanilla JS, Chart.js + D3 from cdnjs).  
**Constraints:** No build step; OpenF1 base URL `https://api.openf1.org/v1/`; keep existing dark theme and fingerprint concept.

---

## 1. Problem statement

Users observe **both panels stuck on the loading skeleton indefinitely**. That indicates the startup async chain (`init` → sessions → panel loads) **does not reliably settle**: typically a **`fetch` that never resolves or rejects** (network stall, blocking, flaky connectivity), less commonly unhandled promise paths leaving UI in a loading state.

Separately, the product benefits from **clearer loading semantics**, **recoverability**, and **comparison-focused UI polish**.

---

## 2. Goals & non-goals

### Goals

1. **Every load attempt terminates** in one of: success, empty telemetry, no clean lap, HTTP error, or timeout—with UI updated accordingly.
2. **Observable progress** across logical stages (sessions catalog → laps → lap-window telemetry).
3. **User-recoverable failures** via retry (per panel or global).
4. **Optional diagnostics** for debugging without polluting default UI.
5. **UX improvements** that reinforce the “fingerprint comparison” thesis without breaking the single-file constraint.

### Non-goals

- Backend proxy or auth changes.
- Replacing Chart.js/D3 with a bundler-based stack.
- Persisting user preferences beyond URL/query flags (unless trivial `localStorage` later—out of scope for v2).

---

## 3. Root-cause hypotheses (ordered)

| Rank | Hypothesis | Why it matches “both skeletons forever” |
|------|------------|----------------------------------------|
| 1 | `fetch` to OpenF1 **hangs** (no timeout in browser) | Entire chain waits; both panels never leave loading if failure is before first paint swap |
| 2 | Network / VPN / firewall blocks `api.openf1.org` | Same as above |
| 3 | Rare: early uncaught exception before error UI | Should be logged; mitigate with defensive `try/finally` |

**Note:** Live API verification showed `car_data` **must** use `date>` and `date<` (not `date>=` / `date<=`), and Monaco is named **`Monte Carlo`** in 2024 sessions. Implementation already aligns; this spec assumes that behavior.

---

## 4. Architecture (logical modules in one file)

Keep one IIFE but **group responsibilities** clearly (comments or section headers):

1. **Http** — `fetchJson` with timeout, abort, and structured errors.
2. **OpenF1** — sessions, drivers, laps, `car_data` (date-bounded).
3. **Fingerprint** — fastest clean lap, resample 360, cosine similarity.
4. **Charts** — Chart.js radar + reference ring; D3 difference plot.
5. **UI state** — panels, primary selection, registry grid, loading stepper messages.
6. **Bootstrap** — Monaco/Mont Carlo + Monza + Leclerc #16.

---

## 5. Phased implementation

### Phase 1 — Stop infinite loading (required)

**5.1 Fetch timeout & abort**

- Wrap all API calls in a helper, e.g. `fetchWithTimeout(url, { timeoutMs, signal })`.
- Default timeout: **20s** per request (tune after field test: 15–30s range).
- Use **`AbortController`**: pass `signal` to `fetch`; on timeout, **abort** so promises reject reliably.

**5.2 Structured errors**

- Distinguish in UI copy where possible:
  - **Timeout:** “Request timed out — check network or retry.”
  - **HTTP ≥400:** include status code in dev-facing detail.
  - **Empty JSON arrays** where unexpected: reuse existing telemetry / lap messages.

**5.3 Guaranteed loading teardown**

- For each panel load path, use **`try` / `catch` / `finally`**:
  - `finally`: `state.panels[panel].loading = false`, hide skeleton, stop step spinner state.
- Ensure **`bootWithThesisPair`** errors surface on **both** panels if startup fails globally (already partially handled — audit for gaps).

**5.4 Retry**

- Add **Retry** control per panel (button near chart area or inline on error banner).
- Retry re-runs `loadPanelBySelection` for that panel’s current session + driver.

**Deliverable:** User never sees infinite skeleton without an explicit error + retry path.

---

### Phase 2 — Loading UX & diagnostics (high value)

**5.5 Stage labels (“pipeline”)**

Replace generic “Fetching telemetry…” with explicit stages:

1. `Sessions` — only if blocking initial catalog (usually instant after cache).
2. `Drivers` — when repopulating driver list after session change.
3. `Laps` — fetching lap list for fastest clean lap.
4. `Telemetry` — bounded `car_data` for lap window.

Show **current stage + elapsed seconds** (updated via `requestAnimationFrame` or simple `setInterval` cleared on completion).

**5.6 Debug mode**

- Enable when URL contains `debug=1` (query string).
- Show compact panel: last request URL (sanitized length), HTTP status, duration, error name/message.
- Toggle off by default.

**Deliverable:** Easier support + faster confirmation of network vs API vs logic bugs.

---

### Phase 3 — Comparison UX & performance polish

**5.7 Panel actions**

- **Swap panels:** exchange left/right session + driver + reload charts from cache when possible (`dnaByPair` hit), else refetch.
- **Sync driver:** optional checkbox — when changing driver on primary panel, mirror driver number on secondary if same session key pair logic allows (define: sync only driver number, not session).

**5.8 Difference visualization**

- Keep `|a − b|` polar plot; add subtle caption: “radius = throttle delta (0–100 scale).”
- Optional: list **top K degrees** by delta (small text under chart) — **K ≤ 5**.

**5.9 Chart rendering performance**

- Maintain **360-length DNA vectors** for cosine similarity (spec invariant).
- Optional display decimation for Chart.js radar (e.g. render every **2nd** point) **only if** profiling shows main-thread pain — document decision in code comment.

**Deliverable:** Faster comprehension + smoother interaction on modest hardware.

---

## 6. UI / copy guidelines

- Loading: neutral teal accent; errors: existing red/error styling.
- Timeout vs generic failure: **different primary sentence**, same retry affordance.
- Do not add axis labels on fingerprint charts (per product thesis); reference ring at 50% throttle remains.

---

## 7. Testing checklist (manual)

1. **Happy path:** Open file via local static server (recommended) — Monte Carlo vs Monza + #16 loads without interaction.
2. **Timeout simulation:** throttle network to “Offline” mid-load — panel shows timeout, retry works when back online.
3. **Telemetry empty:** pick a session/driver known to lack `car_data` — message matches spec.
4. **No clean lap:** if reproducible with a synthetic session/driver — handled.
5. **Debug=1:** URLs and timings appear; no layout break on mobile width.
6. **Swap / sync (Phase 3):** state and charts remain consistent; registry grid updates.

---

## 8. Implementation order (recommended)

1. `fetchWithTimeout` + refactor `fetchJson`.
2. Panel `finally` teardown + per-panel Retry.
3. Stage messaging + timers.
4. `?debug=1` overlay.
5. Swap panels (+ cache-aware reload).
6. Optional sync driver + chart decimation if needed.

---

## 9. Open questions (resolve during implementation)

- **Exact timeout constants** per endpoint (`sessions` vs `car_data`) — start uniform, split if telemetry consistently slower.
- Whether **swap** should clear errors or preserve them until retry — default: clear errors on swap success path.

---

## 10. References

- OpenF1 docs / endpoint examples (comparison filters on fields).
- Existing app entry: [`index.html`](../index.html).
