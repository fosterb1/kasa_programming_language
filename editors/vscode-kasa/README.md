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
