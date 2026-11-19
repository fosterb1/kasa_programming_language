"use strict";

const vscode = require('vscode');
const { spawn } = require('node:child_process');
const path = require('node:path');

/**
 * Launch the installed Kasa CLI as an argument-vector subprocess, NOT via a shell.
 * Kasa programs deliberately execute only when the user invokes Run.
 */
async function invoke(mode, channel) {
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
  const executable = vscode.workspace.getConfiguration('kasa').get('executablePath', 'kasa');
  const file = editor.document.uri.fsPath;
  const cwd = vscode.workspace.getWorkspaceFolder(editor.document.uri)?.uri.fsPath || path.dirname(file);
  channel.clear(); channel.show(true);
  channel.appendLine(`Kasa ${mode}: ${path.basename(file)}`);
  channel.appendLine('');
  let child;
  try {
    child = spawn(executable, [mode, file], {
      cwd, shell: false, windowsHide: true, stdio: ['ignore','pipe','pipe'],
    });
  } catch (error) {
    channel.appendLine(String(error.message || error));
    return;
  }
  let written = 0;
  const maxOutput = 128 * 1024;
  for (const stream of [child.stdout, child.stderr]) {
    stream.on('data', bytes => {
      if (written >= maxOutput) return;
      const text=bytes.toString('utf8').slice(0, maxOutput - written);
      written += text.length;
      channel.append(text);
      if (written >= maxOutput) channel.appendLine('\n[Output truncated by VS Code extension]');
    });
  }
  const watchdog = setTimeout(() => child.kill(), 15000);
  child.on('error', error => {\n    channel.appendLine(`Unable to start Kasa: ${error.message}`);\n    if (error.code === 'ENOENT') {\n      channel.appendLine('Install Kasa or set kasa.executablePath to the full path of the installed kasa executable.');\n    }\n  });
  child.on('close', code => {
    clearTimeout(watchdog);
    channel.appendLine(`\nKasa process exited: ${code}`);
  });
}

function activate(context) {
  const channel = vscode.window.createOutputChannel('Kasa');
  context.subscriptions.push(channel);
  context.subscriptions.push(vscode.commands.registerCommand('kasa.runFile', () => invoke('run', channel)));
  context.subscriptions.push(vscode.commands.registerCommand('kasa.checkFile', () => invoke('check', channel)));
}

function deactivate() {}
module.exports = {activate,deactivate};
