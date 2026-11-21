# Kasa VS Code language support — prototype

This **unpublished** extension adds `.kasa` file recognition, highlighting,
Twi keyword snippets, indentation support, and commands **Kasa: Run Current File**
and **Kasa: Check Current File**.

## Local development

1. Install the standalone `kasa-native` compiler (see `../../native/README.md`).
2. Open this folder in VS Code, press `F5` to launch an Extension Development Host.
3. Open a `.kasa` file and run **Kasa: Run Current File** from the command palette.
4. If needed, set `kasa.executablePath` to the absolute path of `kasa-native`.

The extension does not bundle a native executable. The `check` command does
not run the program. `run` intentionally executes code from the file the user
chooses. Process invocation uses `spawn` without a shell to avoid command-string
injection; no source or telemetry is sent to a server.

Publishing to VS Code Marketplace requires a deliberate license decision,
publisher identity, packaging and Windows/macOS verification. This folder is
**not** a released marketplace extension.

## Experimental editor error highlights (Python CLI only)

The extension can now display source errors in VS Code's Problems panel and
underline the error position using the Python CLI's opt-in JSON protocol.

In VS Code settings, configure:

```json
{
  "kasa.executablePath": "kasa",
  "kasa.jsonDiagnostics": true
}
```

The executable must resolve to the **Python** Kasa CLI that supports
`--diagnostics-json`. Set an absolute executable path as appropriate if
your environment does not provide `kasa` on PATH. The default
`kasa.jsonDiagnostics` value is **false**, preserving existing behavior for
`kasa-native`, which does not implement this flag.

Save a `.kasa` file and run **Kasa: Check Current File** or
**Kasa: Run Current File**. On a recognized error, the extension displays
one diagnostic in the Problems panel for the current file. This is an
on-demand action, not live keystroke analysis, language-server support, or a
native C++ debugger. `Run` executes user code intentionally, while
`Check` only parses it.

Safety/limitations: diagnostics are accepted only for the selected file;
unrecognized, malformed, oversized or foreign-file JSON remains visible in
the output channel rather than silently accepted. A spawned process is
limited to 15 seconds with bounded output. No telemetry or public server
is involved. The extension remains an unpublished prototype.

Run the Node unit/metadata suite:

```bash
node --test editors/vscode-kasa/tests/*.test.cjs
```
