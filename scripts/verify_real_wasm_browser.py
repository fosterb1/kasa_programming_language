"""Execute REAL compiled Emscripten Kasa WASM inside a Chromium Web Worker.

Fails closed unless a completed WASM-enabled ZIP is present. Exercises the
packaged site (never the JS-only source worker), and verifies native engine
selection plus exact output, input, syntax checking, errors and JS fallback.

Prerequisites: python -m pip install playwright; python -m playwright install chromium
Build: bash native/wasm/build.sh; python playground/build_site.py --require-wasm
Run: python scripts/verify_real_wasm_browser.py
"""
from __future__ import annotations

from contextlib import contextmanager
from functools import partial
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
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
                        "native/kasa-native.js", "native/kasa-native.wasm"}
            if not required.issubset(archive.namelist()):
                raise RuntimeError("Incomplete native WASM ZIP")
            worker = archive.read("worker.js").decode("utf-8")
            if "const KASA_HAS_WASM = true;" not in worker:
                raise RuntimeError("Packaged worker does not enable native WASM")
            archive.extractall(directory)
        errors = []
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True, args=["--no-sandbox"])
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
                assert not errors, f"Uncaught browser page errors: {errors}"
            context.close()
            browser.close()
    print("PASS genuine Chromium native Emscripten WASM: load, run, check, input, "
          "error, explicit JavaScript fallback")


if __name__ == "__main__":
    run()
