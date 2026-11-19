"""Offline Windows installer staging invariants; no Inno Setup executable needed."""
import importlib.util
from pathlib import Path
import hashlib
import json
import zipfile
import pytest

FILE = Path(__file__).resolve().parents[1] / "scripts/stage_windows_installer.py"
spec=importlib.util.spec_from_file_location("win_stage",FILE)
tool=importlib.util.module_from_spec(spec)
spec.loader.exec_module(tool)

def archive(tmp_path):
    file=tmp_path/"kasa-0.4.0-alpha-windows-x64-UNSIGNED-dev.zip"
    folder=file.stem
    binary=b"MZ"+b"k"*2000
    manifest={"release":"0.4.0-alpha","platform":"Windows","architecture":"x64",
              "binary_sha256":hashlib.sha256(binary).hexdigest()}
    with zipfile.ZipFile(file,"w") as z:
        z.writestr(f"{folder}/kasa-native.exe",binary)
        z.writestr(f"{folder}/kasa.cmd",b"@echo off\r\n")
        z.writestr(f"{folder}/manifest.json",json.dumps(manifest))
        z.writestr(f"{folder}/README.txt",b"preview")
    (tmp_path/(file.name+".sha256")).write_text(tool.sha256(file.read_bytes())+"  "+file.name+"\n")
    return file

def test_stage_archive_integrity_and_identity(tmp_path):
    zipfile_path=archive(tmp_path)
    out=tool.stage(zipfile_path,tmp_path/"stage")
    assert sorted(x.name for x in out.iterdir())==sorted([*tool.REQUIRED,"kasa-install-identity.txt"])
    assert (out/"kasa-install-identity.txt").read_text()==tool.IDENTITY

def test_stage_refuses_existing_directory(tmp_path):
    zipfile_path=archive(tmp_path)
    out=tmp_path/"stage"
    out.mkdir()
    (out/"important.txt").write_text("preserve")
    with pytest.raises(ValueError,match="overwritten"):
        tool.stage(zipfile_path,out)
    assert (out/"important.txt").read_text()=="preserve"

def test_stage_refuses_bad_sha(tmp_path):
    zipfile_path=archive(tmp_path)
    zipfile_path.with_name(zipfile_path.name+".sha256").write_text("0"*64+"  "+zipfile_path.name+"\n")
    with pytest.raises(ValueError,match="SHA-256"):
        tool.stage(zipfile_path,tmp_path/"stage")
    assert not (tmp_path/"stage").exists()

def test_stage_refuses_foreign_extra_files(tmp_path):
    zipfile_path=archive(tmp_path)
    with zipfile.ZipFile(zipfile_path,"a") as z:
        z.writestr(zipfile_path.stem+"/foreign.exe",b"bad")
    zipfile_path.with_name(zipfile_path.name+".sha256").write_text(tool.sha256(zipfile_path.read_bytes())+"  "+zipfile_path.name+"\n")
    with pytest.raises(ValueError,match="unexpected"):
        tool.stage(zipfile_path,tmp_path/"stage")
    assert not (tmp_path/"stage").exists()

def test_inno_script_per_user_and_no_path_mutation():
    script=(FILE.parent/"kasa_windows_preview.iss").read_text()
    assert "PrivilegesRequired=lowest" in script
    assert "ChangesEnvironment=no" in script
    assert "Uninstallable=yes" in script
    assert "kasa-install-identity.txt" in script
    assert "[Registry]" not in script
    assert "[Run]" not in script
