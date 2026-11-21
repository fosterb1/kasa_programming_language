# Offline Kasa Studio verification (Linux / Google Cloud Shell)

Kasa development does **not** require a Netlify deploy or GitHub Actions job.
This workflow checks the existing native runtime and packaged browser Studio
using the repository's maintained verification scripts.

## Setup (Google Cloud Shell)

```bash
cd ~/kasa_programming_language
git fetch origin
git switch dev/offline-studio-verification
python3 -m venv .venv                 # omit if .venv already exists
source .venv/bin/activate
python -m pip install -e ".[dev]" playwright
python -m playwright install chromium
source ~/emsdk/emsdk_env.sh          # requires installed Emscripten SDK
```

## Run

```bash
python scripts/verify_studio_offline.py --dry-run
python scripts/verify_studio_offline.py --profile native
python scripts/verify_studio_offline.py --profile browser
# Or execute both stages in order:
python scripts/verify_studio_offline.py --profile all
```

The command generates `build/offline-studio-verification.json`.
The native stage also saves `build/offline-native-evidence.json`.
The browser stage compiles real Emscripten WASM, packages a required-WASM ZIP
in `dist/`, and runs real Chromium playground, experimental JavaScript
module, and WASM browser checks. It does **not** deploy, push, merge,
install dependencies, or expose the experimental G0.5 trusted-local compiler
to public visitors.

A dry run prints the plan and records `not_run`; it is **not** evidence
of tests passing. The command fails on the first unsuccessful stage.
See the individual reports/logs for diagnostic details. Release/security
review still applies; the G0.5 release collector can remain
`REVIEW_REQUIRED` for platform-specific skips.

## Windows

Keep Windows junction testing separate. Execute the corresponding test
from the G0.5-reviewed checkout with the virtual environment's Python
directly to avoid PowerShell activation policy issues:

```powershell
C:\Users\User\kasa_programming_language\.venv\Scripts\python.exe -m pytest -q -rs tests/test_g05_windows_junctions.py
```

Do not use the offline browser runner as a replacement for platform-specific
Windows file-system or native Studio checks.
