; Kasa 0.4 alpha Windows per-user installer preview.
; Compile with Inno Setup 7 on Windows. Never run unsigned installers automatically.
#define KasaVersion "0.4.0"
#define KasaStage "..\build\windows-installer-stage"
[Setup]
AppId={{1DA69BE3-F55F-4A32-AF5D-40A740834D84}
AppName=Kasa Programming Language Preview
AppVersion={#KasaVersion}
AppVerName=Kasa Programming Language 0.4.0-alpha Preview
AppPublisher=Kasa Language Project
DefaultDirName={localappdata}\Programs\Kasa Preview
DefaultGroupName=Kasa Preview
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
UsePreviousAppDir=no
OutputDir=..\build\dist
OutputBaseFilename=kasa-0.4.0-alpha-windows-x64-UNSIGNED-Setup-guarded
Compression=lzma
SolidCompression=yes
ArchitecturesAllowed=x64compatible
Uninstallable=yes
CreateUninstallRegKey=yes
SetupLogging=yes
WizardStyle=modern
ChangesEnvironment=no
DisableDirPage=no
DirExistsWarning=yes
[Files]
Source: "{#KasaStage}\kasa-native.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#KasaStage}\kasa.cmd"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#KasaStage}\manifest.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#KasaStage}\README.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#KasaStage}\kasa-install-identity.txt"; DestDir: "{app}"; Flags: ignoreversion
[Icons]
Name: "{group}\Uninstall Kasa Preview"; Filename: "{uninstallexe}"
[Code]
// Phase 6E: deliberately first-install-only. Never overwrite a folder that
// contains any file or subdirectory, even if it contains our identity marker.
// Run at PrepareToInstall, *after* any custom /DIR and wizard selection.
// This also covers /SILENT installs, unlike a default-path-only startup test.
function IsEmptyInstallDirectory(const Directory: String): Boolean;
var
  FindRec: TFindRec;
begin
  Result := True;
  if not DirExists(Directory) then
    Exit;
  if FindFirst(AddBackslash(Directory) + '*', FindRec) then
  begin
    try
      repeat
        if (FindRec.Name <> '.') and (FindRec.Name <> '..') then
        begin
          Result := False;
          Break;
        end;
      until not FindNext(FindRec);
    finally
      FindClose(FindRec);
    end;
  end;
end;

function PrepareToInstall(var NeedsRestart: Boolean): String;
begin
  Result := '';
  if not IsEmptyInstallDirectory(WizardDirValue) then
    Result := 'Kasa preview refuses to install over an existing non-empty folder: ' +
      WizardDirValue + #13#10 +
      'No application files were installed. Choose a new empty folder. ' +
      'Upgrades are not supported in this prototype.';
end;
