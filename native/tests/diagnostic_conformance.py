"""Phase 4C.2 — run the same diagnostic-category fixtures in the linked native C++ VM.

Usage:
  python native/tests/diagnostic_conformance.py build/kasa-local/kasa-native

No hosted service, third-party dependency or browser is required.
"""
from __future__ import annotations
import json
from pathlib import Path
import re
import subprocess
import sys
import tempfile

ROOT = Path(__file__).resolve().parents[2]
CASES = json.loads((ROOT / "tests/conformance_diagnostics_4c.json").read_text(encoding="utf-8"))["cases"]

def main(argv: list[str]) -> int:
    if len(argv) != 2:
        print("Usage: python native/tests/diagnostic_conformance.py PATH_TO_KASA_NATIVE",file=sys.stderr)
        return 2
    binary=Path(argv[1]).resolve()
    if not binary.is_file():
        print("Native executable not found: "+str(binary),file=sys.stderr)
        return 2
    failed=[]
    with tempfile.TemporaryDirectory(prefix="kasa-diagnostics-") as work:
        for c in CASES:
            source=Path(work)/(c["name"]+".kasa")
            source.write_text(c["source"],encoding="utf-8")
            try:
                result=subprocess.run([str(binary),"run",str(source)],
                    input=b"",capture_output=True,timeout=12,check=False)
                stderr=result.stderr.decode("utf-8",errors="replace")
                category=c["error_category"]
                valid=result.returncode != 0 and re.search(
                    r":\d+:\d+: "+re.escape(category)+r":",stderr
                ) is not None
                if not valid:
                    failed.append((c["name"],result.returncode,stderr[-500:]))
                print(("PASS" if valid else "FAIL")+" native "+c["name"]+" "+category)
            except subprocess.TimeoutExpired:
                failed.append((c["name"],"timeout","native VM hung"))
    if failed:
        for name,code,details in failed:
            print(f"FAIL {name}: exit={code}: {details}",file=sys.stderr)
        return 1
    print(f"PASS: {len(CASES)} native Kasa error-category fixtures")
    return 0

if __name__=="__main__":
    raise SystemExit(main(sys.argv))
