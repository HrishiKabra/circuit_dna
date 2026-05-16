#!/usr/bin/env python3
"""
Headless browser verification for Circuit DNA.

Serves circuit_dna/ over HTTP, loads the app in Chromium, waits for OpenF1 + charts,
captures screenshots under docs/, and fails on JS errors or assertions.

Handles transient OpenF1 HTTP 429 (rate limit) by reloading with backoff.

Usage:
  cd circuit_dna && python3 scripts/verify_headless.py

Requires: pip install playwright && python3 -m playwright install chromium
"""

from __future__ import annotations

import sys
import threading
import traceback
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
PORT = 9888
DOCS = ROOT / "docs"


class QuietStaticHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def log_message(self, format, *args):
        pass


def resilient_open_ready(page, url: str, attempts: int = 8, backoff_ms: int = 4000) -> None:
    """Navigate until similarity + diff peaks render (retry on slow API / 429 bursts)."""
    from playwright.sync_api import TimeoutError as PlaywrightTimeoutError

    last_exc: BaseException | None = None
    for attempt in range(attempts):
        try:
            page.goto(url, wait_until="domcontentloaded", timeout=120000)
            page.wait_for_function(
                """() => {
                  const el = document.querySelector('#similarity-value');
                  return el && el.textContent && el.textContent.includes('%');
                }""",
                timeout=75000,
            )
            page.wait_for_function(
                """() => {
                  const t = document.querySelector('#diff-peaks')?.textContent || '';
                  return t.includes('Largest deltas');
                }""",
                timeout=75000,
            )
            return
        except PlaywrightTimeoutError as exc:
            last_exc = exc
            if attempt + 1 == attempts:
                raise
            page.wait_for_timeout(backoff_ms)
    raise AssertionError(last_exc)


def main() -> int:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "Install Playwright: pip install playwright && python3 -m playwright install chromium",
            file=sys.stderr,
        )
        return 2

    DOCS.mkdir(parents=True, exist_ok=True)
    httpd = ThreadingHTTPServer(("127.0.0.1", PORT), QuietStaticHandler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()

    console_errors: list[str] = []
    page_errors: list[str] = []

    def on_console(msg):
        if msg.type == "error":
            console_errors.append(msg.text)

    exit_code = 0

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1440, "height": 900})

            page.on("console", on_console)
            page.on("pageerror", lambda exc: page_errors.append(str(exc)))

            base = f"http://127.0.0.1:{PORT}/index.html"

            resilient_open_ready(page, base)
            console_errors.clear()

            left_circuit = page.locator("#left-circuit").inner_text(timeout=5000)
            right_circuit = page.locator("#right-circuit").inner_text(timeout=5000)
            if "Monte Carlo" not in left_circuit and "Monaco" not in left_circuit:
                print(f"unexpected left circuit label: {left_circuit!r}", file=sys.stderr)
                exit_code = 1
            if "Monza" not in right_circuit:
                print(f"unexpected right circuit label: {right_circuit!r}", file=sys.stderr)
                exit_code = 1

            charts_ok = page.evaluate(
                """() => typeof Chart !== 'undefined'
                  && typeof d3 !== 'undefined'
                  && document.querySelectorAll('#left-chart-wrap canvas').length > 0"""
            )
            if not charts_ok:
                print("Chart.js canvas or globals missing", file=sys.stderr)
                exit_code = 1

            page.screenshot(path=str(DOCS / "headless-01-loaded.png"), full_page=True)

            if exit_code == 0:
                left_sess = page.locator("#left-session").input_value()
                right_sess = page.locator("#right-session").input_value()

                page.click("#swap-btn")

                page.wait_for_function(
                    f"""() => {{
                      const l = document.querySelector('#left-session').value;
                      const r = document.querySelector('#right-session').value;
                      return l === '{right_sess}' && r === '{left_sess}';
                    }}""",
                    timeout=180000,
                )

                page.wait_for_function(
                    """() => {
                      const el = document.querySelector('#similarity-value');
                      return el && el.textContent && el.textContent.includes('%');
                    }""",
                    timeout=180000,
                )

                page.screenshot(path=str(DOCS / "headless-02-after-swap.png"), full_page=True)

                page.wait_for_timeout(8000)

                resilient_open_ready(page, f"{base}?debug=1")
                console_errors.clear()

                page.wait_for_function(
                    """() => {
                      const el = document.getElementById('debug-log');
                      return el && !el.hidden && el.textContent && el.textContent.length > 30;
                    }""",
                    timeout=180000,
                )

                page.screenshot(path=str(DOCS / "headless-03-debug.png"), full_page=True)

            browser.close()
    except Exception:
        traceback.print_exc()
        exit_code = 1
    finally:
        httpd.shutdown()

    filtered_console = [
        line
        for line in console_errors
        if "429" not in line
        and "Too Many Requests" not in line
        and not (
            "Failed to load resource" in line and "404 (Not Found)" in line
        )
    ]
    if page_errors:
        print("PAGE JS ERRORS:", *page_errors, sep="\n", file=sys.stderr)
        exit_code = 1
    if filtered_console:
        print("BROWSER console.error:", *filtered_console, sep="\n", file=sys.stderr)
        exit_code = 1

    if exit_code == 0:
        print("HEADLESS_VERIFY_OK")
        print(f"Screenshots: {DOCS}/headless-01-loaded.png (+ 02, 03)")
    return exit_code


if __name__ == "__main__":
    sys.exit(main())
