"""Release-packaging metadata and offline shell checks, no web access required."""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT/'playground'))
from build_site import build_bundle  # noqa: E402


def test_offline_bundle_has_versioned_cache_and_icons(tmp_path):
    path=build_bundle(tmp_path/'kasa.zip')
    with ZipFile(path) as archive:
        entries=set(archive.namelist())
        assert {'sw.js','manifest.webmanifest','icons/kasa-192.png','icons/kasa-512.png'}.issubset(entries)
        sw=archive.read('sw.js').decode('utf-8')
        assert '__KASA_BUILD_HASH__' not in sw
        assert re.search(r'kasa-playground-[a-f0-9]{12}',sw)
        assert 'cache.addAll(CORE)' in sw
        assert 'cache.match(request, { ignoreSearch: true })' in sw
        assert b'navigator.serviceWorker.register' in archive.read('app.js')
        manifest=json.loads(archive.read('manifest.webmanifest'))
        assert manifest['display']=='standalone'
        assert len(manifest['icons'])>=2
        for size in (192,512):
            assert archive.read(f'icons/kasa-{size}.png').startswith(b'\x89PNG\r\n\x1a\n')


def test_release_docs_keep_stable_claims_out_of_alpha():
    checklist=(ROOT/'docs/RELEASE_CHECKLIST.md').read_text(encoding='utf-8')
    assert 'LICENSE' in checklist
    assert '.wasm' in checklist
    assert (ROOT/'docs/SEMANTICS.md').is_file()
    assert len(list((ROOT/'examples').glob('*.kasa')))>=15
