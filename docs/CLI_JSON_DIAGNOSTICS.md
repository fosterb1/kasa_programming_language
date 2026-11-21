# CLI JSON diagnostics — experimental editor integration

The Python reference CLI has an **opt-in**, versioned, machine-readable error
format. The default text error display and `--explain` behavior are unchanged.

```bash
python -m kasa check examples/hello.kasa --diagnostics-json
python -m kasa run examples/hello.kasa --diagnostics-json
```

When a Kasa error occurs, the CLI emits exactly one JSON object on **stderr**
with fields `schema_version` (1), `category`, `message`, `file`,
`line`, and `column`. Source-coordinate positions are 1-based Unicode
code-point columns. Missing or unreadable files use `FileError` and null
coordinates. Exit statuses remain 0 for success, 1 for a language error, and
2 for a source-file read error. Success emits no JSON diagnostic.

`--diagnostics-json` and `--explain` are mutually exclusive. The
`run` command can still emit program output to stdout on execution; editors
must read diagnostics from stderr and respect exit status.

This is a **Python CLI protocol**, not a claim that the browser worker or
native C++ executable already accepts this flag. It does not add Twi
keywords, module permissions, new bytecode, or a public compiler endpoint.

## Independent verification — Google Cloud Shell

```bash
cd ~/kasa_programming_language
git fetch origin
git switch dev/cli-json-diagnostics
source .venv/bin/activate
python -m pytest -q tests/test_cli_json_diagnostics.py
python scripts/verify_local.py --profile full
```

Record the exact Git revision and any failures before considering a merge.
Netlify remains paused.
