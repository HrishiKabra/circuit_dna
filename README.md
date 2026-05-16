# Circuit DNA

Throttle “fingerprints” per F1 circuit: compare 360° resampled telemetry from [OpenF1](https://openf1.org/), side by side.

## Run locally

Static single page — serve the folder over HTTP (required for `fetch`):

```bash
cd circuit_dna
python3 -m http.server 8080
```

Open `http://127.0.0.1:8080/index.html`.

## Verify (optional)

Requires Playwright:

```bash
pip install playwright && python3 -m playwright install chromium
python3 scripts/verify_headless.py
```

## Docs

- UX / reliability notes: [`docs/circuit-dna-v2-design.md`](docs/circuit-dna-v2-design.md)
- UI implementation plan: [`docs/superpowers/plans/2026-05-15-race-engineering-bench-ui.md`](docs/superpowers/plans/2026-05-15-race-engineering-bench-ui.md)
