"""Run Kasa Playground end-to-end in a REAL Chromium browser.

Optional development dependency: python -m pip install playwright
Then: python -m playwright install chromium

This starts a loopback static HTTP server with no internet requests. Tests
the worker and DOM, not just Node's simulated Worker protocol.
It does NOT claim Emscripten WebAssembly ran: JS-only worker is checked here.
"""
from __future__ import annotations

from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
import os
from pathlib import Path
import threading

ROOT = Path(__file__).resolve().parents[1]
PLAYGROUND = ROOT / "playground"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        return


@contextmanager
def local_site():
    server = ThreadingHTTPServer(("127.0.0.1", 0),
                                 partial(QuietHandler, directory=str(PLAYGROUND)))
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:" + str(server.server_address[1])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def verify():
    from playwright.sync_api import sync_playwright

    with sync_playwright() as playwright:
        # Create a fresh, isolated profile so local drafts from previous runs
        # cannot influence the tests.
        browser = playwright.chromium.launch(headless=True, args=["--no-sandbox"])
        context = browser.new_context(service_workers="block")
        errors = []
        page = context.new_page()
        page.on("pageerror", lambda error: errors.append(str(error)))
        # The server port is chosen dynamically for concurrent test runs.
        with local_site() as url:
            page.goto(url, wait_until="load", timeout=20000)
            page.locator("#run").wait_for(state="visible")
            page.wait_for_function("!document.querySelector('#run').disabled", timeout=15000)
            assert page.locator("#engine option[value=native]").is_disabled(), "JS-only deployment must not advertise WASM"
            page.locator("#run").click()
            page.wait_for_function("document.querySelector('#output').textContent.includes('Maakye, Ghana!')", timeout=15000)
            assert "JavaScript" in page.locator("#status").inner_text()

            # Actual syntax check with no program execution.
            page.locator("#source").fill('ka "Meda wo ase"')
            page.locator("#check").click()
            page.wait_for_function("document.querySelector('#status').textContent.includes('Syntax valid')", timeout=15000)
            assert "Meda wo ase" not in page.locator("#output").inner_text()

            # Source persists locally across reloads; private program input doesn't.
            page.locator("#source").fill('ka "Akwaaba, Ghana!"')
            page.locator("#input").fill("private input should not persist")
            page.reload(wait_until="load")
            page.wait_for_function("!document.querySelector('#run').disabled", timeout=15000)
            assert page.locator("#source").input_value() == 'ka "Akwaaba, Ghana!"'
            assert page.locator("#input").input_value() == ""

            # Import an actual UTF-8 .kasa file through a browser File input.
            page.locator("#upload").set_input_files({
                "name": "akwaaba.kasa",
                "mimeType": "text/plain",
                "buffer": 'ka "Ɛyɛ Kasa!"\n'.encode("utf-8"),
            })
            page.wait_for_function("document.querySelector('#source').value.includes('Ɛyɛ Kasa!')", timeout=15000)
            page.locator("#run").click()
            page.wait_for_function("document.querySelector('#output').textContent.includes('Ɛyɛ Kasa!')", timeout=15000)
            assert "Run completed" in page.locator("#status").inner_text()

            page.locator("#reset").click()
            assert page.locator("#source").input_value() == 'ka "Maakye, Ghana!"\n'
            page.reload(wait_until="load")
            page.wait_for_function("!document.querySelector('#run').disabled", timeout=15000)
            assert page.locator("#source").input_value() == 'ka "Maakye, Ghana!"\n'
            assert page.evaluate("localStorage.getItem('kasa.playground.source.v1')") is None
            assert not errors, f"Browser JavaScript errors: {errors}"
        context.close()
        browser.close()
    print("PASS real Chromium playground: worker, run, check, persistence/privacy, UTF-8 upload, reset, JS-only engine")


if __name__ == "__main__":
    verify()
