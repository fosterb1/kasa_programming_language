#!/usr/bin/env python3
"""Phase 6E: opt-in Windows *disposable VM* installer lifecycle audit.

Default mode only verifies the installer hash and prints a plan. It NEVER
executes setup without --execute-in-disposable-vm and a VM identity check.
No administrator elevation, PATH edits, deletes outside its dedicated temp
workspace, or bypassing security warnings.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import platform
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[1]
SETUP = ROOT / "build/dist/kasa-0.4.0-alpha-windows-x64-UNSIGNED-Setup-guarded-v2.exe"
EXPECTED_SHA256 = "2af6ac1347da03870fe1e80543c1fba1af78fac12d087103a52f230f1c003b87"
REPORT = ROOT / "build/windows-installer-lifecycle.json"
VM_TERMS = ("virtual machine", "vmware", "virtualbox", "qemu", "kvm", "hyper-v", "hyperv", "parallels", "bochs", "xen")

def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()

def check_setup(path: Path, expected: str) -> dict:
    result = {"path": str(path), "exists": path.is_file(), "actual_sha256": None,
              "expected_sha256": expected, "matches": False}
    if result["exists"]:
        result["actual_sha256"] = sha256(path)
        result["matches"] = result["actual_sha256"].lower() == expected.lower()
    return result

def detect_vm() -> tuple[bool, str]:
    """Only a heuristic, used as an additional refusal gate, never proof of safety."""
    if os.name != "nt":
        return False, "Non-Windows host"
    script = "(Get-CimInstance Win32_ComputerSystem | Select-Object Manufacturer,Model | ConvertTo-Json -Compress)"
    try:
        response = subprocess.run(["powershell", "-NoProfile", "-NonInteractive", "-Command", script],
                                  capture_output=True, text=True, timeout=15, check=False)
        if response.returncode != 0:
            return False, "Cannot query VM identity"
        values = json.loads(response.stdout)
        identity = f"{values.get('Manufacturer', '')} {values.get('Model', '')}".lower()
        return any(word in identity for word in VM_TERMS), identity
    except (OSError, ValueError, subprocess.TimeoutExpired):
        return False, "Cannot query VM identity"

def command(argv: list[str], timeout: int = 120) -> dict:
    result = {"command": argv, "exit_code": None, "stdout_tail": "", "stderr_tail": ""}
    try:
        p = subprocess.run(argv, capture_output=True, text=True, errors="replace",
                           timeout=timeout, check=False)
        result.update(exit_code=p.returncode, stdout_tail=p.stdout[-1500:],
                      stderr_tail=p.stderr[-1500:])
    except (OSError, subprocess.TimeoutExpired) as exc:
        result["stderr_tail"] = str(exc)
    return result

def run_lifecycle(setup: Path, workspace: Path) -> dict:
    """Run only after checking Windows, opt-in, VM identity and installer digest.

    Every test destination belongs to this newly created disposable VM workspace.
    Workspace deletion is intentionally disabled to preserve failure evidence;
    restore the VM snapshot to recover the machine.
    """
    workspace.mkdir(parents=False, exist_ok=False)
    events = []
    sentinel = workspace / "personal-program.kasa"
    sentinel.write_text('ka "Akwaaba Ghana!"\n', encoding="utf-8")
    personal_digest = sha256(sentinel)
    occupied = workspace / "occupied"
    occupied.mkdir()
    foreign = occupied / "keep-me.txt"
    foreign.write_text("protect this file", encoding="utf-8")
    foreign_digest = sha256(foreign)
    env_path_before = os.environ.get("PATH", "")  # Process-only; not a registry PATH audit.
    # An existing occupied target must not be touched by the guarded installer.
    blocked = command([str(setup), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
                       "/DIR=" + str(occupied), "/LOG=" + str(workspace / "blocked.log")])
    reject_ok = (blocked["exit_code"] is not None and blocked["exit_code"] != 0
                 and foreign.exists() and sha256(foreign) == foreign_digest)
    events.append({"name": "reject occupied custom destination", "passed": reject_ok,
                   "process": blocked})
    if not reject_ok:
        return {"events": events, "passed": False, "workspace": str(workspace)}
    target = workspace / "fresh-install"
    if target.exists():
        return {"events": events, "passed": False, "error": "Fresh directory exists"}
    installed = command([str(setup), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
                         "/DIR=" + str(target), "/LOG=" + str(workspace / "install.log")])
    files_ok = (installed["exit_code"] == 0 and
                all((target / name).is_file() for name in
                    ("kasa-native.exe", "kasa.cmd", "manifest.json",
                     "README.txt", "kasa-install-identity.txt")))
    events.append({"name": "fresh per-user installation", "passed": files_ok,
                   "process": installed})
    if not files_ok:
        return {"events": events, "passed": False, "workspace": str(workspace)}
    # A second installation must not overwrite an existing Kasa preview.
    installed_digest = sha256(target / "kasa-native.exe")
    reinstall = command([str(setup), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
                         "/DIR=" + str(target), "/LOG=" + str(workspace / "reinstall.log")])
    reinstall_ok = (reinstall["exit_code"] is not None and reinstall["exit_code"] != 0
                    and (target / "kasa-native.exe").is_file()
                    and sha256(target / "kasa-native.exe") == installed_digest)
    events.append({"name": "reject second installation", "passed": reinstall_ok,
                   "process": reinstall})
    if not reinstall_ok:
        return {"events": events, "passed": False, "workspace": str(workspace)}
    exe = target / "kasa-native.exe"
    version = command([str(exe), "--version"], timeout=20)
    run = command([str(exe), "run", str(sentinel)], timeout=20)
    # Check both direct native VM execution and the installed user-facing CMD launcher.
    launcher = command(["cmd.exe", "/d", "/c", str(target / "kasa.cmd"), "--version"], timeout=20)
    execution_ok = (version["exit_code"] == 0 and "Kasa Native 0.4.0-alpha" in version["stdout_tail"]
                    and run["exit_code"] == 0 and "Akwaaba Ghana!" in run["stdout_tail"]
                    and launcher["exit_code"] == 0 and "Kasa Native 0.4.0-alpha" in launcher["stdout_tail"])
    events.append({"name": "installed native execution", "passed": execution_ok,
                   "version": version, "program": run, "launcher": launcher})
    if not execution_ok:
        return {"events": events, "passed": False, "workspace": str(workspace)}
    uninstaller = target / "unins000.exe"
    if not uninstaller.is_file():
        events.append({"name": "uninstaller exists", "passed": False})
        return {"events": events, "passed": False, "workspace": str(workspace)}
    removed = command([str(uninstaller), "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART",
                       "/LOG=" + str(workspace / "uninstall.log")])
    safe = (removed["exit_code"] == 0 and not exe.exists()
            and sentinel.exists() and sha256(sentinel) == personal_digest
            and foreign.exists() and sha256(foreign) == foreign_digest
            and os.environ.get("PATH", "") == env_path_before)
    events.append({"name": "uninstall preserves external files", "passed": safe,
                   "process": removed})
    return {"events": events, "passed": all(e["passed"] for e in events),
            "workspace": str(workspace), "note": "VM test workspace and logs retained; reset VM snapshot for recovery"}

def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--setup", type=Path, default=SETUP)
    parser.add_argument("--sha256", default=EXPECTED_SHA256)
    parser.add_argument("--report", type=Path, default=REPORT)
    parser.add_argument("--execute-in-disposable-vm", action="store_true")
    parser.add_argument("--acknowledge-vm-snapshot", default="",
                        help="Must equal DISPOSABLE-VM-SNAPSHOT-CONFIRMED for execution")
    args = parser.parse_args(argv)
    info = check_setup(args.setup.resolve(), args.sha256)
    result = {"generated_at": datetime.now(timezone.utc).isoformat(),
              "platform": platform.platform(), "setup": info, "executed": False,
              "scope": "Disposable Windows VM only; unsigned local preview"}
    result["planned_checks"] = [
        "Reject occupied custom directory and preserve sentinel",
        "Install into previously nonexistent directory",
        "Reject second installation into existing Kasa preview",
        "Execute native Kasa version, CMD launcher and a Twi program",
        "Uninstall and preserve both external sentinel files",
    ]
    if args.execute_in_disposable_vm:
        vm, identity = detect_vm()
        result["vm_detected"] = vm
        result["vm_identity"] = identity
        if not (info["matches"] and vm and
                args.acknowledge_vm_snapshot == "DISPOSABLE-VM-SNAPSHOT-CONFIRMED"):
            result["error"] = "Execution refused: check SHA-256, VM identity and snapshot acknowledgment"
        else:
            # Preserve logs, partial files and test sentinels for failure diagnosis.
            # Do not delete the VM test tree automatically: only a snapshot reset
            # should restore the disposable Windows VM to its baseline.
            vm_root = Path(tempfile.mkdtemp(prefix="kasa-vm-root-"))
            base = vm_root / "lifecycle"
            result["executed"] = True
            result["vm_workspace"] = str(vm_root)
            try:
                result["lifecycle"] = run_lifecycle(args.setup.resolve(), base)
            except Exception as exc:
                result["lifecycle"] = {
                    "passed": False, "workspace": str(base),
                    "error": f"{type(exc).__name__}: {exc}",
                    "note": "Partial VM test files retained; inspect and reset VM snapshot",
                }
    else:
        result["note"] = "READ-ONLY preflight. No setup or uninstaller executed."
    report = args.report.resolve()
    report.parent.mkdir(parents=True, exist_ok=True)
    report.write_text(json.dumps(result, indent=2) + "\n", encoding="utf-8")
    print("Report:", report)
    print("Installer SHA-256 matches:", info["matches"])
    print("Installer executed:", result["executed"])
    if result.get("error"):
        print(result["error"], file=sys.stderr)
        return 2
    if not info["matches"]:
        return 1
    if result["executed"]:
        return 0 if result["lifecycle"]["passed"] else 1
    return 0

if __name__ == "__main__":
    raise SystemExit(main())
