; Inno Setup Script for PCAD Parametric CAD Application
#define MyAppName "PCAD"
#define MyAppVersion "0.2.0"
#define MyAppPublisher "Meslek CAD Systems"
#define MyAppURL "https://github.com/mesleken/parametric-cad"
#define MyAppExeName "pcad.exe"

[Setup]
AppId={{D37B4821-6A42-4A7B-9021-9E8620F24CB1}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}
DefaultDirName={autopf}\{#MyAppName}
DisableProgramGroupPage=yes
LicenseFile=..\docs\THIRD_PARTY_LICENSES.md
OutputDir=..\dist\installer
OutputBaseFilename=PCAD_Setup_{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesInstallIn64BitMode=x64compatible
ChangesAssociations=yes

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"

[Files]
Source: "..\dist\pcad\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
Source: "..\dist\pcad\*"; DestDir: "{app}"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{autoprograms}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; Associate .pcad.json file extension with PCAD
Root: HKA; Subkey: "Software\Classes\.pcad.json"; ValueType: string; ValueName: ""; ValueData: "PCAD.ProjectFile"; Flags: uninsdeletevalue
Root: HKA; Subkey: "Software\Classes\PCAD.ProjectFile"; ValueType: string; ValueName: ""; ValueData: "PCAD Parametric CAD Project"; Flags: uninsdeletekey
Root: HKA; Subkey: "Software\Classes\PCAD.ProjectFile\DefaultIcon"; ValueType: string; ValueName: ""; ValueData: "{app}\{#MyAppExeName},0"
Root: HKA; Subkey: "Software\Classes\PCAD.ProjectFile\shell\open\command"; ValueType: string; ValueName: ""; ValueData: """{app}\{#MyAppExeName}"" ""%1"""

[Run]
Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; Filename: "{app}\{#MyAppExeName}"; Flags: nowait postinstall skipifsilent
