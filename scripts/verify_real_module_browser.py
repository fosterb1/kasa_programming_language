"""G0.4.3: verify packaged Kasa modules inside a REAL Chromium Web Worker.

This is a JS-only, loopback-hosted browser acceptance gate. It builds a local
ZIP, verifies that the pinned module assets are in the package, and forces
native WASM OFF in the temporary test copy. It neither needs nor certifies
a live Netlify site or native WASM module-import support.

Dependencies: python -m pip install playwright
Browser: python -m playwright install chromium
Optional: KASA_BROWSER_CHANNEL=chrome|chromium|msedge
Run: python scripts/verify_real_module_browser.py
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import sys
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "playground"))
from build_site import build_bundle  # noqa: E402
sys.path.insert(0, str(ROOT / "scripts"))
from verify_real_wasm_browser import serve  # noqa: E402

FIXTURES = ROOT / "tests" / "conformance_experimental_modules.json"


def verify() -> None:
    from playwright.sync_api import sync_playwright

    fixture_data = json.loads(FIXTURES.read_text(encoding="utf-8"))
    assert fixture_data["schema_version"] == 1

    with tempfile.TemporaryDirectory(prefix="kasa-g04-real-worker-") as directory:
        temp = Path(directory)
        bundle = build_bundle(temp / "playground.zip")
        site = temp / "site"
        site.mkdir()
        with ZipFile(bundle) as archive:
            required = {"index.html", "worker.js", "kasa-runtime.js",
                        "kasa-pinned-modules.js", "app.js", "diagnostics.js"}
            assert required.issubset(set(archive.namelist())), "Incomplete playground package"
            archive.extractall(site)
        worker_path = site / "worker.js"
        worker = worker_path.read_text(encoding="utf-8")
        assert "const KASA_HAS_PINNED_MODULES = true;" in worker
        # Only test the module-capable JS path, even if this developer has
        # independently generated native WASM assets on disk.
        worker = worker.replace("const KASA_HAS_WASM = true;", "const KASA_HAS_WASM = false;")
        assert "const KASA_HAS_WASM = false;" in worker
        worker_path.write_text(worker, encoding="utf-8")

        channel = os.environ.get("KASA_BROWSER_CHANNEL", "chromium")
        if channel not in {"chromium", "chrome", "msedge"}:
            raise ValueError("KASA_BROWSER_CHANNEL must be chromium, chrome, or msedge")
        with sync_playwright() as playwright:
            browser_args = {"headless": True}
            if channel == "chromium":
                browser = playwright.chromium.launch(**browser_args)
            else:
                browser = playwright.chromium.launch(channel=channel, **browser_args)
            context = browser.new_context(service_workers="block")
            page = context.new_page()
            errors: list[str] = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            with serve(site) as url:
                page.goto(url, wait_until="load", timeout=30000)
                page.wait_for_function(
                    "!document.querySelector('#run').disabled", timeout=25000
                )
                assert page.locator("#engine option[value=native]").is_disabled()
                page.locator("#experimental-modules").check()
                page.locator("#engine").select_option("javascript")

                for case in fixture_data["cases"]:
                    page.locator("#source").fill(case["source"])
                    page.locator("#run").click()
                    page.wait_for_function(
                        "!document.querySelector('#run').disabled "
                        "&& ['ready','error'].includes(document.querySelector('#status').dataset.state)",
                        timeout=25000,
                    )
                    status = page.locator("#status").inner_text()
                    actual = page.locator("#output").text_content() or ""
                    if "output" in case:
                        assert "Run completed" in status, (case["id"], status, actual)
                        assert actual == case["output"], (case["id"], actual, case["output"])
                    else:
                        assert page.locator("#status").get_attribute("data-state") == "error", (
                            case["id"], status, actual
                        )
                        assert ": " + case["js_category"] + ":" in actual, (case["id"], actual)
                        assert case["error_contains"].lower() in actual.lower(), (case["id"], actual)
                        if "line" in case:
                            assert f"playground.kasa:{case['line']}:{case['column']}:" in actual, (
                                case["id"], actual
                            )
                        assert "not reached" not in actual, (case["id"], actual)
                    assert "JavaScript" in status or "error" in status.lower(), case["id"]
                    print("PASS real worker " + case["id"])

                # Disabling experimental mode must restore default Kasa grammar.
                page.locator("#experimental-modules").uncheck()
                page.locator("#source").fill(
                    "fa math firi stdlib: m\nka m.kasa_sum([1])\n"
                )
                page.locator("#run").click()
                page.wait_for_function(
                    "!document.querySelector('#run').disabled "
                    "&& document.querySelector('#status').dataset.state === 'error'",
                    timeout=25000,
                )
                assert "SyntaxError" in page.locator("#output").inner_text()
                assert page.locator("#engine option[value=native]").is_disabled()
                assert not errors, "Uncaught browser page errors: " + repr(errors)
            context.close()
            browser.close()
    print(f"PASS real Chromium worker: {len(fixture_data['cases'])} opt-in module "
          "fixtures, diagnostics, normal-mode rejection, JS-only engine")


if __name__ == "__main__":
    verify()
