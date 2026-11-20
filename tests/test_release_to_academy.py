"""Independent, no-network unit checks for the Kasa Academy release publisher."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

SCRIPT = Path(__file__).resolve().parents[1] / "scripts" / "release_to_academy.py"
spec = importlib.util.spec_from_file_location("kasa_release", SCRIPT)
release = importlib.util.module_from_spec(spec)
spec.loader.exec_module(release)

class ReleaseSafetyTest(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.source = self.root / "playground"
        for name in release.FILES:
            dest = self.source / name
            dest.parent.mkdir(parents=True, exist_ok=True)
            if name == "native/kasa-native.wasm":
                dest.write_bytes(b"\x00asm\x01\x00\x00\x00" + b"X" * 5000)
            elif name == "native/kasa-native.js":
                dest.write_text("createKasaModule;" + "a" * 2000)
            elif name == "worker.js":
                dest.write_text("const KASA_HAS_WASM = false;\nconst KASA_HAS_PINNED_MODULES = false;")
            elif name == "sw.js":
                dest.write_text("const CACHE_NAME='__KASA_BUILD_HASH__';\nconst KASA_PACKAGED_MODULES = false;")
            elif name == "index.html":
                dest.write_text('<title>Kasa Playground — Kasa Programming Language</title><div class="topbar-right"><link href="./style.css"><script src="./app.js?v=0.4.0"></script>')
            elif name == "app.js":
                dest.write_text('const worker = new Worker("./worker.js?v=0.4.0");')
            else:
                dest.write_text("dummy content")
        self.patcher = patch.object(release, "ROOT", self.root)
        self.patcher.start()
        self.modules_patcher = patch.object(release, "packaged_pinned_modules", return_value=b"self.KasaPinnedModules = Object.freeze({});\n")
        self.modules_patcher.start()

    def tearDown(self):
        self.modules_patcher.stop()
        self.patcher.stop()
        self.temp.cleanup()

    def test_valid_release_manifest_and_assets(self):
        payload, manifest = release.build_payload()
        self.assertEqual(payload["native/kasa-native.wasm"][:8], bytes([0, 97, 115, 109, 1, 0, 0, 0]))
        self.assertIn(b"KASA_HAS_WASM = true", payload["worker.js"])
        self.assertIn(b"KASA_HAS_PINNED_MODULES = true", payload["worker.js"])
        self.assertIn(b"KASA_PACKAGED_MODULES = true", payload["sw.js"])
        self.assertIn(release.MODULE_ASSET, payload)
        self.assertIn(release.MODULE_ASSET, manifest["files"])
        self.assertIn(b"worker.js?v=", payload["app.js"])
        self.assertNotIn(b"__KASA_BUILD_HASH__", payload["sw.js"])
        self.assertIn(b"Back to Academy", payload["index.html"])
        self.assertEqual(manifest["files"]["native/kasa-native.wasm"]["sha256"], release.digest(payload["native/kasa-native.wasm"]))
        self.assertEqual(json.loads(payload["release-manifest.json"])["release"], manifest["release"])
        self.assertEqual(set(release.verify_files(payload,self.root)), set(payload))

    def test_bad_binary_stops_release(self):
        (self.source / "native/kasa-native.wasm").write_bytes(b"fake wasm" * 700)
        with self.assertRaises(ValueError):
            release.build_payload()

    def test_partial_native_js_stops_release(self):
        (self.source / "native/kasa-native.js").write_text("missing")
        with self.assertRaises(ValueError):
            release.build_payload()

    def test_worker_without_expected_flag_stops_release(self):
        (self.source / "worker.js").write_text("const KASA_HAS_WASM = true;")
        with self.assertRaises(ValueError):
            release.build_payload()

    def test_module_flag_is_required(self):
        (self.source / "worker.js").write_text("const KASA_HAS_WASM = false;")
        with self.assertRaisesRegex(ValueError, "module flag"):
            release.build_payload()

    def test_sw_module_guard_is_required(self):
        (self.source / "sw.js").write_text("const CACHE_NAME='__KASA_BUILD_HASH__';")
        with self.assertRaisesRegex(ValueError, "offline-cache pinned module guard"):
            release.build_payload()

    def test_library_validation_refuses_release(self):
        with patch.object(release, "packaged_pinned_modules", side_effect=RuntimeError("catalog digest mismatch")):
            with self.assertRaisesRegex(RuntimeError, "catalog digest mismatch"):
                release.build_payload()

    def test_worker_url_requires_exactly_one_revision_target(self):
        (self.source / "app.js").write_text("no worker")
        with self.assertRaisesRegex(ValueError, "versioned worker initialization"):
            release.build_payload()

    def test_revision_changes_when_module_asset_changes(self):
        first, original = release.build_payload()
        with patch.object(release, "packaged_pinned_modules", return_value=b"self.KasaPinnedModules={math:{}};\\n"):
            changed, modified = release.build_payload()
        self.assertNotEqual(original["release"], modified["release"])
        self.assertNotEqual(first[release.MODULE_ASSET], changed[release.MODULE_ASSET])

    def test_api_publish_builds_one_commit_without_force(self):
        payload,manifest=release.build_payload()
        calls=[]
        def fake_api(method,path,token,body=None):
            calls.append((method,path,body))
            if path.endswith("/git/ref/heads/main"):return {"object":{"sha":"HEAD"}}
            if path.endswith("/git/commits/HEAD"):return {"tree":{"sha":"TREE"}}
            if path.endswith("/git/blobs"):return {"sha":"blob"+str(len(calls))}
            if path.endswith("/git/trees"):return {"sha":"TREE2"}
            if path.endswith("/git/commits"):return {"sha":"NEW"}
            return {"object":{"sha":"NEW"}}
        with patch.object(release,"api",side_effect=fake_api):
            sha=release.publish(payload,manifest,"test/repo","main","redacted")
        self.assertEqual(sha,"NEW")
        tree_call=next(x for x in calls if x[1].endswith("/git/trees"))
        self.assertEqual(len(tree_call[2]["tree"]),len(payload))
        self.assertTrue(all(e["path"].startswith("public/kasa-studio/") for e in tree_call[2]["tree"]))
        self.assertEqual(calls[-1][2]["force"],False)

if __name__ == "__main__":
    unittest.main()
