; Offline DAoC Remastered - the installer (Inno Setup 6, https://jrsoftware.org/isinfo.php)
;
; Owner 2026-11-11: "the installer will install the launcher and all necessary game files, and then in the future the
; launcher will check for updates". The installer is small: the launcher, the disclaimer and credits, the licences. On
; its first start the launcher downloads the game itself (about 45 GB) from the release - the same code path every
; later update takes, so there is one way the game's files arrive and one way they are checked.
;
; Build (after build_release.py, which writes the launcher's publish folder and the generated update.json):
;   "C:\Program Files (x86)\Inno Setup 6\ISCC.exe" /DVersion=0.1.0 /DSource="E:\Offline DAOC Release" OfflineDaocRemastered.iss
; -> E:\Offline DAOC Release\Offline-DAoC-Remastered-Setup-0.1.0.exe

#ifndef Version
  #define Version "0.1.0"
#endif
#ifndef Source
  #define Source "..\..\..\..\..\Offline DAOC Release"
#endif
#define Text "..\text"

[Setup]
AppId={{6C2E9C2B-7A51-4C8E-9E0B-0FDA0C4D2E36}
AppName=Offline DAoC Remastered
AppVersion={#Version}
AppPublisher=Offline DAoC Remastered (a free fan project)
DefaultDirName={sd}\Games\Offline DAoC Remastered
DefaultGroupName=Offline DAoC Remastered
DisableProgramGroupPage=yes
; the game writes beside itself (its world, your saves, its updates): a per-user install, no administrator needed
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog
LicenseFile={#Text}\DISCLAIMER.txt
InfoAfterFile={#Text}\CREDITS.txt
OutputDir={#Source}
OutputBaseFilename=Offline-DAoC-Remastered-Setup-{#Version}
SetupIconFile=..\..\..\new-client\godot\icon.ico
UninstallDisplayIcon={app}\client\launcher\OfflineDAoC.exe
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
DirExistsWarning=no
; the download that follows needs the room, not the installer
ExtraDiskSpaceRequired=50000000000

[Messages]
SelectDirDesc=Where should Offline DAoC Remastered be installed?
SelectDirBrowseLabel=The game downloads about 45 GB here the first time the launcher starts, and needs about 50 GB free. A fast drive (an SSD) is best.

[Files]
Source: "{#Source}\launcher\*"; DestDir: "{app}\client\launcher"; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "{#Source}\generated\server_root.txt"; DestDir: "{app}\client\launcher"; Flags: ignoreversion
Source: "{#Source}\generated\update.json"; DestDir: "{app}\client\launcher"; Flags: ignoreversion
Source: "{#Text}\DISCLAIMER.txt"; DestDir: "{app}"; Flags: ignoreversion
Source: "{#Text}\CREDITS.txt"; DestDir: "{app}"; Flags: ignoreversion

[Dirs]
Name: "{app}\client\save"
Name: "{app}\world\data"
Name: "{app}\world\logs"

[Icons]
Name: "{group}\Offline DAoC Remastered"; Filename: "{app}\client\launcher\OfflineDAoC.exe"; WorkingDir: "{app}\client\launcher"
Name: "{group}\Disclaimer"; Filename: "{app}\DISCLAIMER.txt"
Name: "{group}\Credits"; Filename: "{app}\CREDITS.txt"
Name: "{group}\Uninstall Offline DAoC Remastered"; Filename: "{uninstallexe}"
Name: "{autodesktop}\Offline DAoC Remastered"; Filename: "{app}\client\launcher\OfflineDAoC.exe"; WorkingDir: "{app}\client\launcher"; Tasks: desktopicon

[Tasks]
Name: "desktopicon"; Description: "Create a desktop shortcut"; GroupDescription: "Shortcuts:"

[Run]
Filename: "{app}\client\launcher\OfflineDAoC.exe"; Description: "Start the launcher (it downloads the game)"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
; everything the launcher downloaded (the uninstaller only knows the files it placed itself)
Type: filesandordirs; Name: "{app}\client\godot"
Type: filesandordirs; Name: "{app}\client\tools"
Type: filesandordirs; Name: "{app}\client\launcher"
Type: filesandordirs; Name: "{app}\world\server"
Type: filesandordirs; Name: "{app}\world\logs"
Type: filesandordirs; Name: "{app}\tools"
Type: filesandordirs; Name: "{app}\LICENSES"
Type: filesandordirs; Name: "{app}\.update"

[Code]
// Your characters and settings (the world database, the client's save, the cloud-sync records) stay unless you say
// otherwise - an uninstall to reinstall shouldn't cost a player their progress.
procedure CurUninstallStepChanged(CurUninstallStep: TUninstallStep);
begin
  if CurUninstallStep = usPostUninstall then
  begin
    if DirExists(ExpandConstant('{app}\world\data')) then
      if MsgBox('Also delete your characters, your world and your settings?' + #13#10#13#10 +
                'Choose No to keep them in ' + ExpandConstant('{app}') + ' for a later reinstall.',
                mbConfirmation, MB_YESNO or MB_DEFBUTTON2) = IDYES then
      begin
        DelTree(ExpandConstant('{app}\world'), True, True, True);
        DelTree(ExpandConstant('{app}\client'), True, True, True);
        DelTree(ExpandConstant('{app}'), True, True, True);
      end;
  end;
end;
