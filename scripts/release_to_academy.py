#!/usr/bin/env python3
"""Publish an APPROVED Kasa browser build to Kasa Learning Academy, atomically.

No paid GitHub Actions runner is necessary. Run locally after Emscripten build
and independent tests. Uses GitHub Git Data REST API with a fine-grained token
allowed to write the Academy repository. Requires explicit --publish.

Examples:
  bash native/wasm/build.sh
  node --test tests/test_kasa_wasm.cjs tests/test_kasa_browser.cjs
  python playground/build_site.py --require-wasm
  python scripts/release_to_academy.py --academy ../kasa-learning-academy
  GITHUB_TOKEN=... python scripts/release_to_academy.py --academy ../kasa-learning-academy --publish
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys
from urllib.error import HTTPError
from urllib.request import Request, urlopen
from playground.build_site import packaged_pinned_modules

ROOT = Path(__file__).resolve().parents[1]
FILES = (
    "index.html", "style.css", "app.js", "diagnostics.js", "worker.js", "kasa-runtime.js",
    "sw.js", "manifest.webmanifest",
    "icons/kasa-192.png", "icons/kasa-512.png",
    "native/kasa-native.js", "native/kasa-native.wasm",
)
MODULE_ASSET = "kasa-pinned-modules.js"
BINARIES = {"native/kasa-native.wasm", "icons/kasa-192.png", "icons/kasa-512.png"}
STUDIO = "public/kasa-studio/"
GITHUB_API = "https://api.github.com"


def digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def build_payload() -> tuple[dict[str, bytes], dict]:
    source = ROOT / "playground"
    inputs = {name: (source / name).read_bytes() for name in FILES}
    wasm = inputs["native/kasa-native.wasm"]
    if len(wasm) < 4096 or wasm[:8] != b"\x00asm\x01\x00\x00\x00":
        raise ValueError("Refusing to publish missing, invalid or stubbed native WASM")
    if len(inputs["native/kasa-native.js"]) < 1000:
        raise ValueError("Missing native JavaScript loader")
    # Verify the pinned catalog source hashes before building ANY release files.
    # Keep this generated asset consistent with the browser ZIP builder.
    inputs[MODULE_ASSET] = packaged_pinned_modules(ROOT)
    worker = inputs["worker.js"].decode("utf-8")
    flag = "const KASA_HAS_WASM = false;"
    if worker.count(flag) != 1:
        raise ValueError("Unexpected worker flag; update release script for changed worker")
    worker = worker.replace(flag, "const KASA_HAS_WASM = true;")
    module_flag = "const KASA_HAS_PINNED_MODULES = false;"
    if worker.count(module_flag) != 1:
        raise ValueError("Unexpected pinned module flag; refusing incompatible Academy release")
    worker = worker.replace(module_flag, "const KASA_HAS_PINNED_MODULES = true;")
    inputs["worker.js"] = worker.encode("utf-8")
    html = inputs["index.html"].decode("utf-8")
    html = html.replace(
        "<title>Kasa Playground — Kasa Programming Language</title>",
        "<title>Kasa Playground — Kasa Learning Academy</title>",
    )
    html = html.replace(
        '<div class="topbar-right">',
        '<div class="topbar-right"><a class="academy-back-link" href="/learn">← Back to Academy</a>',
    )
    css = inputs["style.css"].decode("utf-8")
    css += "\n.academy-back-link{color:#c8efb6;font-weight:750;font-size:13px;border:1px solid #597965;border-radius:9px;padding:9px 12px}.academy-back-link:hover{background:#315344}\n"
    inputs["style.css"] = css.encode("utf-8")
    # Include locally pinned libraries and native runtime in the revision hash.
    version = hashlib.sha256(b"".join(
        name.encode("utf-8") + inputs[name]
        for name in (*FILES, MODULE_ASSET)
    )).hexdigest()[:12]
    html = html.replace('href="./style.css"', f'href="./style.css?v={version}"')
    # Enforce one unambiguous revision for the Academy-hosted HTML links.
    import re
    html = re.sub(r'(href="./style\.css)(?:\?v=[^"]*)?(")', rf'\g<1>?v={version}\g<2>', html)
    html = re.sub(r'(src="./app\.js)(?:\?v=[^"]*)?(")', rf'\g<1>?v={version}\g<2>', html)
    html = re.sub(r'(src="./diagnostics\.js)(?:\?v=[^"]*)?(")', rf'\g<1>?v={version}\g<2>', html)
    # App's versioned worker URL must also change when its source changes.
    app = inputs["app.js"].decode("utf-8")
    app, worker_refs = re.subn(
        r'new Worker\("\./worker\.js\?v=[^"]+"\)',
        f'new Worker("./worker.js?v={version}")',
        app,
    )
    if worker_refs != 1:
        raise ValueError("Expected exactly one versioned worker initialization")
    inputs["app.js"] = app.encode("utf-8")
    inputs["index.html"] = html.encode("utf-8")
    sw = inputs["sw.js"].decode("utf-8")
    if sw.count("__KASA_BUILD_HASH__") != 1:
        raise ValueError("Offline-cache revision placeholder missing")
    sw_flag = "const KASA_PACKAGED_MODULES = false;"
    if sw.count(sw_flag) != 1:
        raise ValueError("Missing offline-cache pinned module guard")
    sw = sw.replace(sw_flag, "const KASA_PACKAGED_MODULES = true;")
    inputs["sw.js"] = sw.replace("__KASA_BUILD_HASH__", version).encode("utf-8")
    if not all(inputs.values()):
        raise ValueError("Empty file in browser release")
    manifest = {
        "format": "kasa-studio-release-v1",
        "release": version,
        "source_repo": "fosterb1/kasa_programming_language",
        "files": {name: {"sha256": digest(inputs[name]), "bytes": len(inputs[name])} for name in (*FILES, MODULE_ASSET)},
    }
    inputs["release-manifest.json"] = (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode("utf-8")
    return inputs, manifest


def verify_files(inputs: dict[str, bytes], academy: Path) -> list[str]:
    changes = []
    for name, data in inputs.items():
        dest = academy / STUDIO / name
        if not dest.exists() or dest.read_bytes() != data:
            changes.append(name)
    return changes


def api(method: str, endpoint: str, token: str, body: dict | None = None) -> dict:
    url = GITHUB_API + endpoint
    request = Request(
        url,
        data=None if body is None else json.dumps(body).encode("utf-8"),
        method=method,
        headers={
            "Accept": "application/vnd.github+json",
            "Authorization": "Bearer " + token,
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "Kasa-approved-release-publisher",
        },
    )
    try:
        with urlopen(request, timeout=40) as result:
            return json.load(result)
    except HTTPError as error:
        detail = error.read(800).decode("utf-8", errors="replace")
        raise RuntimeError(f"GitHub {method} {endpoint}: HTTP {error.code}; {detail}") from error


def publish(payload: dict[str, bytes], manifest: dict, repo: str, branch: str, token: str) -> str:
    base = f"/repos/{repo}"
    ref = api("GET", f"{base}/git/ref/heads/{branch}", token)
    head = ref["object"]["sha"]
    commit = api("GET", f"{base}/git/commits/{head}", token)
    tree_entries = []
    for filename, data in payload.items():
        encoded = base64.b64encode(data).decode("ascii")
        blob = api("POST", f"{base}/git/blobs", token, {"content": encoded, "encoding": "base64"})
        tree_entries.append({"path": STUDIO + filename, "mode": "100644", "type": "blob", "sha": blob["sha"]})
    tree = api("POST", f"{base}/git/trees", token, {
        "base_tree": commit["tree"]["sha"], "tree": tree_entries,
    })
    next_commit = api("POST", f"{base}/git/commits", token, {
        "message": f"Release Kasa Studio {manifest['release']} from approved language build",
        "tree": tree["sha"], "parents": [head],
    })
    # No force update: concurrent commits stop publication instead of being overwritten.
    api("PATCH", f"{base}/git/refs/heads/{branch}", token, {
        "sha": next_commit["sha"], "force": False,
    })
    return next_commit["sha"]


def run_local_gates() -> None:
    """No release publication until local language and native artifact checks pass."""
    checks = [
        ["node", "native/wasm/validate_artifacts.mjs"],
        ["node", "--test", "tests/test_kasa_wasm.cjs", "tests/test_kasa_browser.cjs"],
        [sys.executable, "playground/build_site.py", "--require-wasm"],
        [sys.executable, "-m", "unittest", "discover", "-s", "tests", "-p", "test_release_to_academy.py"],
        ["node", "tests/test_js_experimental_modules.js"],
        ["node", "tests/test_js_worker_modules.js"],
        [sys.executable, "-m", "pytest", "-q", "tests/test_experimental_module_source.py", "tests/test_playground.py"],
    ]
    for command in checks:
        print("Checking:", " ".join(command), flush=True)
        subprocess.run(command, cwd=ROOT, check=True)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--academy", type=Path, help="Local Academy checkout for file comparison")
    parser.add_argument("--repo", default="fosterb1/kasa-learning-academy")
    parser.add_argument("--branch", default="main")
    parser.add_argument("--publish", action="store_true", help="Publish the verified bundle to GitHub")
    parser.add_argument("--yes-reviewed", action="store_true", help="Confirm tests and native build were reviewed")
    args = parser.parse_args()
    payload, manifest = build_payload()
    print("Kasa release:", manifest["release"], "| native WASM:", manifest["files"]["native/kasa-native.wasm"]["bytes"], "bytes")
    if args.academy:
        changes = verify_files(payload, args.academy)
        print("Academy differences:", ", ".join(changes) if changes else "none")
    else:
        print("Files to synchronize:", len(payload))
    if not args.publish:
        print("DRY RUN only. No network write; use --publish --yes-reviewed after testing.")
        return 0
    if not args.yes_reviewed:
        parser.error("Use --yes-reviewed after completing local tests and native browser verification")
    run_local_gates()
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        parser.error("GITHUB_TOKEN is required to publish; do not commit credentials")
    sha = publish(payload, manifest, args.repo, args.branch, token)
    print("Published approved release commit:", sha)
    return 0


if __name__ == "__main__":
    sys.exit(main())
