"""Real Chromium G1 worker acceptance, using a local offline ZIP only.

Requires Playwright Chromium. No Netlify, production site, or native KBC claim.
"""
from __future__ import annotations

import json
import os
from pathlib import Path
import re
import sys
import tempfile
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "playground"))
from build_site import build_bundle  # noqa: E402
sys.path.insert(0, str(ROOT / "scripts"))
from verify_real_wasm_browser import serve  # noqa: E402

CONTRACT = ROOT / "tests/g1_contract_fixtures.json"
MATH = {"kasa_min_or", "kasa_max_or", "kasa_total", "kasa_average_or", "kasa_count_above"}
FUNCTION = re.compile(r"\b(kasa_(?:min_or|max_or|total|average_or|count_above|first_index|last_index|count_distinct|all_equal))(?=\s*\()")
PRELUDE = "fa math firi stdlib: m\nfa collections firi stdlib: c\n"


def qualified_source(source: str) -> str:
    """Adapt direct reference fixtures to G1 namespaced imports."""
    return PRELUDE + FUNCTION.sub(
        lambda match: ("m." if match.group(1) in MATH else "c.") + match.group(1),
        source,
    )


INIT_WORKER = """async () => {
  window.__kasaG1Worker = new Worker('./worker.js');
  window.__kasaG1NextId = 1;
  await new Promise((resolve, reject) => {
    const worker = window.__kasaG1Worker;
    const deadline = setTimeout(() => reject(new Error('Worker READY timed out')), 10000);
    function ready(event) {
      if (event.data?.type === 'READY') {
        clearTimeout(deadline);
        worker.removeEventListener('message', ready);
        resolve();
      }
      if (event.data?.type === 'BOOT_ERROR') {
        clearTimeout(deadline);
        worker.removeEventListener('message', ready);
        reject(new Error(event.data.message));
      }
    }
    worker.addEventListener('message', ready);
  });
}"""

RUN_WORKER = """async ({source, experimentalModules, experimentalGeneration, engine}) => {
  const worker = window.__kasaG1Worker;
  const requestId = window.__kasaG1NextId++;
  return await new Promise((resolve, reject) => {
    const deadline = setTimeout(() => {
      worker.removeEventListener('message', receive);
      reject(new Error('Worker RESULT timed out: ' + requestId));
    }, 12000);
    function receive(event) {
      if (event.data?.requestId !== requestId) return;
      if (event.data?.type === 'RESULT') {
        clearTimeout(deadline);
        worker.removeEventListener('message', receive);
        resolve(event.data.result);
      } else if (event.data?.type === 'EXECUTION_ERROR') {
        clearTimeout(deadline);
        worker.removeEventListener('message', receive);
        reject(new Error(event.data.message));
      }
    }
    worker.addEventListener('message', receive);
    worker.postMessage({
      type: 'EXECUTE', requestId, source, input: '', mode: 'run',
      experimentalModules, experimentalGeneration, engine
    });
  });
}"""


def verify() -> None:
    from playwright.sync_api import sync_playwright

    cases = json.loads(CONTRACT.read_text(encoding="utf-8"))["cases"]
    assert len(cases) == 19
    with tempfile.TemporaryDirectory(prefix="kasa-g1-real-chromium-") as folder:
        root = Path(folder)
        enabled_zip = build_bundle(root / "with-g1.zip", include_g1=True)
        baseline_zip = build_bundle(root / "default.zip")
        with ZipFile(baseline_zip) as archive:
            assert "kasa-g1-pinned-modules.js" not in archive.namelist()
            assert b"const KASA_HAS_G1_PINNED_MODULES = false;" in archive.read("worker.js")
        site = root / "site"
        site.mkdir()
        with ZipFile(enabled_zip) as archive:
            assert "kasa-g1-pinned-modules.js" in archive.namelist()
            assert b"const KASA_HAS_G1_PINNED_MODULES = true;" in archive.read("worker.js")
            assert b"const KASA_PACKAGED_G1_MODULES = true;" in archive.read("sw.js")
            assert b"const KASA_HAS_PINNED_MODULES = true;" in archive.read("worker.js")
            archive.extractall(site)
        # Scope to the JS execution path even if developer has a native WASM build.
        worker_file = site / "worker.js"
        worker = worker_file.read_text(encoding="utf-8")
        worker_file.write_text(worker.replace(
            "const KASA_HAS_WASM = true;", "const KASA_HAS_WASM = false;"
        ), encoding="utf-8")

        channel = os.environ.get("KASA_BROWSER_CHANNEL", "chromium")
        if channel not in {"chromium", "chrome", "msedge"}:
            raise ValueError("Unsupported KASA_BROWSER_CHANNEL")
        with sync_playwright() as playwright:
            launch = {"headless": True}
            if channel != "chromium":
                launch["channel"] = channel
            browser = playwright.chromium.launch(**launch)
            context = browser.new_context(service_workers="block")
            page = context.new_page()
            errors = []
            page.on("pageerror", lambda error: errors.append(str(error)))
            with serve(site) as url:
                page.goto(url, wait_until="load", timeout=30000)
                page.evaluate(INIT_WORKER)
                def run(source: str, generation: str = "g1", enabled: bool = True,
                        engine: str = "javascript"):
                    return page.evaluate(RUN_WORKER, {
                        "source": source, "experimentalModules": enabled,
                        "experimentalGeneration": generation, "engine": engine,
                    })

                for case in cases:
                    result = run(qualified_source(case["source"]))
                    assert result["ok"], (case["id"], result["error"])
                    assert result["output"] == case["output"], (case["id"], result["output"])
                    print("PASS real G1 Chromium worker " + case["id"])

                default_g0 = run(
                    "fa math firi stdlib: m\nka m.kasa_sum([1, 2, 3])\n",
                    generation="g0",
                )
                assert default_g0["ok"] and default_g0["output"] == "6\n", default_g0
                unavailable_g0_export = run("fa math firi stdlib: m\nka m.kasa_total([1])\n", generation="g0")
                assert not unavailable_g0_export["ok"] and "does not export" in unavailable_g0_export["error"]
                default_syntax = run("fa math firi stdlib: m\nka m.kasa_total([1])\n", enabled=False)
                assert not default_syntax["ok"] and "SyntaxError" in default_syntax["error"]
                explicit_native = run(qualified_source("ka kasa_total([1])\n"), engine="native")
                assert not explicit_native["ok"] and "JavaScript engine" in explicit_native["error"]
                wrong_generation = run(qualified_source("ka kasa_total([1])\n"), generation="g2")
                assert not wrong_generation["ok"] and "Unknown experimental" in wrong_generation["error"]
                private = run(PRELUDE + "ka m.kasa_sum([1])\n")
                assert not private["ok"] and "does not export" in private["error"]
                assert not errors, errors
                page.evaluate("() => window.__kasaG1Worker.terminate()")
            context.close()
            browser.close()
    print("PASS real Chromium: 19 G1 fixtures + G0, opt-in, native rejection, and error checks")


if __name__ == "__main__":
    verify()
