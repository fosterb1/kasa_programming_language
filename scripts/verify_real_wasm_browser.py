"""Execute REAL compiled Emscripten Kasa WASM inside a Chromium Web Worker.

Fails closed unless a completed WASM-enabled ZIP is present. Exercises the
packaged site (never the JS-only source worker), and verifies native engine
selection plus exact output, input, syntax checking, errors and JS fallback.

Prerequisites: python -m pip install playwright; on macOS use installed Google Chrome\n(Linux: python -m playwright install chromium). Optional KASA_BROWSER_CHANNEL=chrome|chromium|msedge.
Build: bash native/wasm/build.sh; python playground/build_site.py --require-wasm
Run: python scripts/verify_real_wasm_browser.py
"""
from __future__ import annotations

from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
import os
import sys
import tempfile
import threading
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
BUNDLE = ROOT / "dist" / "Kasa_Playground_Web.zip"


class QuietHandler(SimpleHTTPRequestHandler):
    def log_message(self, *_args):
        return


@contextmanager
def serve(directory: Path):
    server = ThreadingHTTPServer(
        ("127.0.0.1", 0), partial(QuietHandler, directory=str(directory))
    )
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    try:
        yield "http://127.0.0.1:" + str(server.server_address[1])
    finally:
        server.shutdown()
        server.server_close()
        thread.join(timeout=5)


def run():
    from playwright.sync_api import sync_playwright

    if not BUNDLE.exists():
        raise RuntimeError("WASM-enabled ZIP missing; run bash native/wasm/build.sh then "
                           "python playground/build_site.py --require-wasm")
    with tempfile.TemporaryDirectory(prefix="kasa-wasm-real-browser-") as tmp:
        directory = Path(tmp)
        with ZipFile(BUNDLE) as archive:
            required = {"index.html", "app.js", "worker.js", "kasa-runtime.js",
                        "native/kasa-native.js", "native/kasa-native.wasm",
                        "kasa-pinned-modules.js"}
            if not required.issubset(archive.namelist()):
                raise RuntimeError("Incomplete native WASM ZIP")
            worker = archive.read("worker.js").decode("utf-8")
            if "const KASA_HAS_WASM = true;" not in worker:
                raise RuntimeError("Packaged worker does not enable native WASM")
            if "const KASA_HAS_PINNED_MODULES = true;" not in worker:
                raise RuntimeError("Packaged worker does not enable pinned modules")
            sw = archive.read("sw.js").decode("utf-8")
            if "const KASA_PACKAGED_MODULES = true;" not in sw:
                raise RuntimeError("Packaged offline cache omits pinned modules")
            archive.extractall(directory)
        errors = []
        with sync_playwright() as pw:
            # Playwright 1.65+ no longer distributes Chromium for macOS 13.
            # Use an already installed, supported Chrome channel on macOS;
            # retain Playwright-managed Chromium on Linux. Never skip the test.
            channel = os.environ.get("KASA_BROWSER_CHANNEL") or (
                "chrome" if sys.platform == "darwin" else "chromium"
            )
            if channel not in {"chrome", "chromium", "msedge"}:
                raise ValueError(
                    "KASA_BROWSER_CHANNEL must be chrome, chromium, or msedge"
                )
            try:
                if channel == "chromium":
                    browser = pw.chromium.launch(headless=True)
                else:
                    browser = pw.chromium.launch(headless=True, channel=channel)
            except Exception as error:
                raise RuntimeError(
                    f"Cannot launch Playwright browser channel {channel!r}. "
                    "On macOS 13 use an installed Google Chrome and "
                    "KASA_BROWSER_CHANNEL=chrome; on supported Linux install "
                    "the Chromium browser with python -m playwright install chromium. "
                    "The real-browser release gate remains mandatory."
                ) from error
            print(f"Real Kasa release browser: {channel}; version {browser.version}")
            context = browser.new_context(service_workers="block")
            page = context.new_page()
            page.on("pageerror", lambda error: errors.append(str(error)))
            with serve(directory) as url:
                page.goto(url, wait_until="load", timeout=30000)
                page.wait_for_function("!document.querySelector('#run').disabled", timeout=25000)
                page.wait_for_function("!document.querySelector('#engine option[value=native]').disabled",
                                       timeout=60000)
                assert "Native WebAssembly available" in page.locator("#status").inner_text()

                page.locator("#engine").select_option("native")
                page.locator("#run").click()
                page.wait_for_function("document.querySelector('#status').textContent.includes('Run completed')",
                                       timeout=25000)
                assert page.locator("#output").inner_text().strip() == "Maakye, Ghana!"
                assert "Native WebAssembly" in page.locator("#status").inner_text()

                page.locator("#source").fill('ka "Meda wo ase"')
                page.locator("#check").click()
                page.wait_for_function("document.querySelector('#status').textContent.includes('Syntax valid')",
                                       timeout=25000)
                assert "Meda wo ase" not in page.locator("#output").inner_text()
                assert "Native WebAssembly" in page.locator("#status").inner_text()

                page.locator("#source").fill('ma edin = bisa()\nka "Akwaaba, " + edin\n')
                page.locator("#input").fill("Ama")
                page.locator("#run").click()
                page.wait_for_function("document.querySelector('#status').textContent.includes('Run completed')",
                                       timeout=25000)
                assert page.locator("#output").inner_text().strip() == "Akwaaba, Ama"
                assert "Native WebAssembly" in page.locator("#status").inner_text()

                page.locator("#source").fill("ka 1 / 0")
                page.locator("#run").click()
                page.wait_for_function("document.querySelector('#status').dataset.state === 'error'",
                                       timeout=25000)
                assert "ZeroDivisionError" in page.locator("#output").inner_text()

                # Both engines must agree for the supported shared subset.
                shared_programs = [
                    'ka "Ɛyɛ Kasa!"',
                    'dwumadie fa_bi(a, b)\n    sanma a + b\nawiei\nka fa_bi(25, 15)',
                    'ma aba = [10, 20, 30]\nka aba[1]',
                    'mpɛn 3\n    ka "Meda wo ase"\nawiei',
                ]
                for program in shared_programs:
                    outputs = {}
                    for engine in ("native", "javascript"):
                        page.locator("#engine").select_option(engine)
                        page.locator("#source").fill(program)
                        page.locator("#run").click()
                        page.wait_for_function(
                            "document.querySelector('#status').textContent.includes('Run completed')",
                            timeout=25000,
                        )
                        outputs[engine] = page.locator("#output").inner_text()
                    assert outputs["native"] == outputs["javascript"], (
                        f"Native/JS browser differential mismatch: {program}: {outputs}"
                    )

                page.locator("#engine").select_option("javascript")
                page.locator("#source").fill('ka "JS fallback"')
                page.locator("#run").click()
                page.wait_for_function("document.querySelector('#status').textContent.includes('Run completed')",
                                       timeout=25000)
                assert page.locator("#output").inner_text().strip() == "JS fallback"
                assert "JavaScript" in page.locator("#status").inner_text()
                # The pinned catalog is a separate, opt-in JavaScript mode.
                # Verify real browser importScripts() and member execution, not
                # just a simulated worker protocol.
                page.locator("#experimental-modules").check()
                page.locator("#engine").select_option("javascript")
                page.locator("#source").fill(
                    "fa math firi stdlib: m\\n"
                    "fa collections firi stdlib: c\\n"
                    "ma nneɛma = [10, 20, 30]\\n"
                    "ka m.kasa_sum(nneɛma)\\n"
                    "ka c.kasa_contains(nneɛma, 20)\\n"
                )
                page.locator("#run").click()
                page.wait_for_function(
                    "document.querySelector('#status').textContent.includes('Run completed')",
                    timeout=25000,
                )
                assert page.locator("#output").inner_text().strip() == "60\\nnokware"
                assert "JavaScript" in page.locator("#status").inner_text()
                assert page.locator("#engine option[value=native]").is_disabled()

                # Disabling imports returns to the independent native runner.
                page.locator("#experimental-modules").uncheck()
                page.wait_for_function(
                    "!document.querySelector('#engine option[value=native]').disabled",
                    timeout=25000,
                )
                page.locator("#engine").select_option("native")
                page.locator("#source").fill('ka "Akwaaba Ghana!"\\nka 25 + 15')
                page.locator("#run").click()
                page.wait_for_function(
                    "document.querySelector('#status').textContent.includes('Run completed')",
                    timeout=25000,
                )
                assert page.locator("#output").inner_text().strip() == "Akwaaba Ghana!\\n40"
                assert "Native WebAssembly" in page.locator("#status").inner_text()
                assert not errors, f"Uncaught browser page errors: {errors}"
            context.close()
            browser.close()
    print("PASS genuine Chromium Emscripten WASM + pinned JavaScript modules: "
          "native load, run, check, input, errors, differential parity, "
          "module imports, native recovery")


if __name__ == "__main__":
    run()
