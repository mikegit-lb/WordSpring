#define AppVersion "1.0.1"
#define ProjectRoot AddBackslash(SourcePath) + ".."

[Setup]
AppId={{7C8D4B14-90C1-46EF-9BE7-6CFF9F3CC8B4}
AppName=WordSpring
AppVersion={#AppVersion}
AppVerName=WordSpring {#AppVersion}
AppPublisher=WordSpring
AppPublisherURL=https://github.com/mikegit-lb/WordSpring
AppSupportURL=https://github.com/mikegit-lb/WordSpring/issues
AppUpdatesURL=https://github.com/mikegit-lb/WordSpring/releases
DefaultDirName={localappdata}\Programs\WordSpring
DefaultGroupName=WordSpring
DisableProgramGroupPage=yes
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
CloseApplications=yes
RestartApplications=no
SetupIconFile={#ProjectRoot}\store\Assets\WordSpring.ico
UninstallDisplayIcon={app}\WordSpring.exe
OutputDir={#ProjectRoot}\dist
OutputBaseFilename=WordSpring-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
VersionInfoVersion=1.0.1.0
VersionInfoCompany=WordSpring
VersionInfoDescription=WordSpring Setup
VersionInfoProductName=WordSpring
SetupLogging=yes

[Languages]
Name: "turkish"; MessagesFile: "compiler:Languages\Turkish.isl"

[Files]
Source: "{#ProjectRoot}\dist\WordSpring.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectRoot}\THIRD_PARTY_NOTICES.md"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#ProjectRoot}\store\Licenses\LGPL-3.0.txt"; DestDir: "{app}\Licenses"; Flags: ignoreversion

[Icons]
Name: "{group}\WordSpring"; Filename: "{app}\WordSpring.exe"; WorkingDir: "{app}"
Name: "{userdesktop}\WordSpring"; Filename: "{app}\WordSpring.exe"; WorkingDir: "{app}"
Name: "{group}\WordSpring'i kaldır"; Filename: "{uninstallexe}"

[Run]
Filename: "{app}\WordSpring.exe"; Description: "WordSpring'i başlat"; Flags: postinstall nowait skipifsilent
