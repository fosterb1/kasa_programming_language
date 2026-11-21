"use strict";

const vscode = require('vscode');
const { spawn } = require('node:child_process');
const path = require('node:path');
const { parseKasaDiagnostic } = require('./diagnostic-protocol');

/**
 * Launch installed Kasa without a shell. Structured diagnostics are strictly
 * opt-in because the native kasa-native CLI does not support this Python flag.
 */
async function invoke(mode, channel, diagnostics) {
  const editor = vscode.window.activeTextEditor;
  if (!editor || editor.document.languageId !== 'kasa') {
    vscode.window.showWarningMessage('Open a .kasa file first.');
    return;
  }
  if (editor.document.isUntitled) {
    vscode.window.showWarningMessage('Save your .kasa program before running it.');
    return;
  }
  if (editor.document.isDirty) await editor.document.save();
  const config = vscode.workspace.getConfiguration('kasa');
  const executable = config.get('executablePath', 'kasa');
  const jsonEnabled = config.get('jsonDiagnostics', false);
  const file = editor.document.uri.fsPath;
  const cwd = vscode.workspace.getWorkspaceFolder(editor.document.uri)?.uri.fsPath || path.dirname(file);
  diagnostics.delete(editor.document.uri);
  channel.clear(); channel.show(true);
  channel.appendLine(`Kasa ${mode}: ${path.basename(file)}`);
  channel.appendLine('');
  const args = [mode, file, ...(jsonEnabled ? ['--diagnostics-json'] : [])];
  let child;
  try {
    child = spawn(executable, args, {
      cwd, shell: false, windowsHide: true, stdio: ['ignore','pipe','pipe'],
    });
  } catch (error) {
    channel.appendLine(String(error.message || error));
    return;
  }
  let written = 0;
  let errorText = '';
  const maxOutput = 128 * 1024;
  function appendBounded(text) {
    if (written >= maxOutput) return;
    const slice = text.slice(0, maxOutput - written);
    written += slice.length;
    channel.append(slice);
    if (written >= maxOutput) channel.appendLine('\n[Output truncated by VS Code extension]');
  }
  child.stdout.on('data', bytes => appendBounded(bytes.toString('utf8')));
  child.stderr.on('data', bytes => {
    const text = bytes.toString('utf8');
    if (jsonEnabled) errorText += text.slice(0, maxOutput + 1 - errorText.length);
    else appendBounded(text);
  });
  const watchdog = setTimeout(() => child.kill(), 15000);
  child.on('error', error => {
    channel.appendLine(`Unable to start Kasa: ${error.message}`);
    if (error.code === 'ENOENT') {
      channel.appendLine('Install Kasa or set kasa.executablePath to the full path of the installed kasa executable.');
    }
  });
  child.on('close', code => {
    clearTimeout(watchdog);
    if (jsonEnabled && errorText) {
      const record = parseKasaDiagnostic(errorText, file);
      if (record) {
        const line = record.line === null ? 0 : record.line - 1;
        const column = record.column === null ? 0 : record.column - 1;
        const location = new vscode.Range(line, column, line, column + 1);
        const diagnostic = new vscode.Diagnostic(location,
          `${record.category}: ${record.message}`, vscode.DiagnosticSeverity.Error);
        diagnostic.source = 'Kasa';
        diagnostics.set(editor.document.uri, [diagnostic]);
        channel.appendLine(`Kasa ${record.category}: ${record.message}`);
      } else {
        channel.appendLine(errorText);
        channel.appendLine('Structured Kasa diagnostic unavailable; verify the configured executable is the Python kasa CLI.');
      }
    }
    channel.appendLine(`\nKasa process exited: ${code}`);
  });
}

function activate(context) {
  const channel = vscode.window.createOutputChannel('Kasa');
  const diagnostics = vscode.languages.createDiagnosticCollection('kasa');
  context.subscriptions.push(channel, diagnostics);
  context.subscriptions.push(vscode.commands.registerCommand('kasa.runFile', () => invoke('run', channel, diagnostics)));
  context.subscriptions.push(vscode.commands.registerCommand('kasa.checkFile', () => invoke('check', channel, diagnostics)));
}
function deactivate() {}
module.exports = {activate,deactivate};
