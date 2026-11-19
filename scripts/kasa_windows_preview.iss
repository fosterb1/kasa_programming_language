; Kasa 0.4 alpha Windows per-user installer preview.
; Build only with Inno Setup 6 on Windows. Never run unsigned installers automatically.
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
UsePreviousAppDir=yes
OutputDir=..\build\dist
OutputBaseFilename=kasa-0.4.0-alpha-windows-x64-UNSIGNED-Setup
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
function InitializeSetup(): Boolean;
var
  InstallDir, IdentityPath: String;
begin
  Result := True;
  InstallDir := ExpandConstant('{localappdata}\Programs\Kasa Preview');
  IdentityPath := InstallDir + '\kasa-install-identity.txt';
  if DirExists(InstallDir) and not FileExists(IdentityPath) then
  begin
    MsgBox('An existing directory at the default installation location does not belong to a recognized Kasa preview. No files were changed. Move the existing directory aside before using this installer.', mbError, MB_OK);
    Result := False;
  end;
end;
