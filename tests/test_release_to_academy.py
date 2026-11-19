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
                dest.write_text("const KASA_HAS_WASM = false;")
            elif name == "sw.js":
                dest.write_text("const CACHE_NAME='__KASA_BUILD_HASH__';")
            elif name == "index.html":
                dest.write_text('<title>Kasa Playground — Kasa Programming Language</title><div class="topbar-right"><link href="./style.css"><script src="./app.js?v=0.4.0"></script>')
            else:
                dest.write_text("dummy content")
        self.patcher = patch.object(release, "ROOT", self.root)
        self.patcher.start()

    def tearDown(self):
        self.patcher.stop()
        self.temp.cleanup()

    def test_valid_release_manifest_and_assets(self):
        payload, manifest = release.build_payload()
        self.assertEqual(payload["native/kasa-native.wasm"][:8], bytes([0, 97, 115, 109, 1, 0, 0, 0]))
        self.assertIn(b"KASA_HAS_WASM = true", payload["worker.js"])
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
