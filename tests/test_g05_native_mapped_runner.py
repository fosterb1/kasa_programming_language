"""G0.5 opt-in map sidecar and real native diagnostic acceptance."""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
import sys
import uuid

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
try:
    from link_kasa_modules_hygienic import HygienicLinkError, write_linked_source
    from run_g05_native_mapped import run_mapped, DEFAULT_NATIVE
finally:
    sys.path.remove(str(ROOT / "scripts"))


def _source():
    return "fa math firi stdlib: m\nka m.kasa_sum([1, 2])\n"


def test_explicit_map_sidecar_and_no_overwrite(tmp_path):
    application = tmp_path / "source.kasa"
    application.write_text(_source(), encoding="utf-8")
    output = ROOT / "build" / "g05-linked" / ("sidecar-test-" + uuid.uuid4().hex + ".kasa")
    map_file = Path(str(output) + ".map.json")
    try:
        assert write_linked_source(application, output, map_output=map_file) == output
        linked = output.read_text(encoding="utf-8")
        mapping = json.loads(map_file.read_text(encoding="utf-8"))
        assert mapping["generated_sha256"] == hashlib.sha256(linked.encode("utf-8")).hexdigest()
        assert len(mapping["lines"]) == len(linked.splitlines())
        assert any(line["file"] == str(application) for line in mapping["lines"])
        before = output.read_bytes()
        with pytest.raises(HygienicLinkError, match="overwrite"):
            write_linked_source(application, output, map_output=map_file)
        assert output.read_bytes() == before
    finally:
        map_file.unlink(missing_ok=True)
        output.unlink(missing_ok=True)


def test_existing_sidecar_does_not_create_source(tmp_path):
    application = tmp_path / "source.kasa"
    application.write_text(_source(), encoding="utf-8")
    output_dir = ROOT / "build" / "g05-linked"
    output_dir.mkdir(parents=True, exist_ok=True)
    output = output_dir / ("sidecar-preexisting-" + uuid.uuid4().hex + ".kasa")
    map_file = Path(str(output) + ".map.json")
    try:
        map_file.write_text("keep me", encoding="utf-8")
        with pytest.raises(HygienicLinkError, match="source map"):
            write_linked_source(application, output, map_output=map_file)
        assert not output.exists()
        assert map_file.read_text(encoding="utf-8") == "keep me"
    finally:
        map_file.unlink(missing_ok=True)


def test_unrelated_map_path_is_rejected(tmp_path):
    application = tmp_path / "source.kasa"
    application.write_text(_source(), encoding="utf-8")
    output = ROOT / "build" / "g05-linked" / ("bad-map-" + uuid.uuid4().hex + ".kasa")
    with pytest.raises(HygienicLinkError, match="sidecar"):
        write_linked_source(application, output, map_output=tmp_path / "unrelated.json")
    assert not output.exists()


@pytest.mark.skipif(not DEFAULT_NATIVE.is_file(), reason="Build native first with verify_local parity")
def test_real_native_error_maps_to_original_application_statement():
    source = (
        "fa math firi stdlib: m\n"
        "ka m.kasa_sum([1, 2])\n"
        "ka 1 / 0\n"
    )
    code, stdout, stderr = run_mapped(source, "lesson.kasa", DEFAULT_NATIVE)
    assert code != 0
    assert stdout == "3\n"
    assert "ZeroDivisionError" in stderr
    assert "Kasa source statement: lesson.kasa:3:1" in stderr


@pytest.mark.skipif(not DEFAULT_NATIVE.is_file(), reason="Build native first with verify_local parity")
def test_real_native_success_has_no_mapping_noise():
    code, stdout, stderr = run_mapped(_source(), "lesson.kasa", DEFAULT_NATIVE)
    assert code == 0
    assert stdout == "3\n"
    assert stderr == ""
