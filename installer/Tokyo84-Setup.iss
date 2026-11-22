; ============================================================================
; Tokyo84 — Native Windows Installer Script (Inno Setup 6)
; Build: iscc installer\Tokyo84-Setup.iss
; Output: dist\Tokyo84-USDX-Setup-1.0.0.exe
; ============================================================================

#define MyAppName "Tokyo84 Theme for UltraStar Deluxe"
#define MyAppVersion "1.0.0"
#define MyAppPublisher "Tokyo84 Design System"
#define MyAppURL "https://github.com/UltraStar-Deluxe/USDX"

[Setup]
AppId={{84C0E8B4-1984-4F9A-9D84-CAB0C1C08400}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
DefaultDirName={code:GetDefaultUSDXDir}
DisableProgramGroupPage=yes
DirExistsWarning=no
OutputDir=..\dist
OutputBaseFilename=Tokyo84-USDX-Setup-{#MyAppVersion}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Types]
Name: "full"; Description: "Full Installation (Theme + 1984 Synth Sounds + Auto-Activate)"
Name: "themeonly"; Description: "Theme Only (Visuals & Layout)"
Name: "custom"; Description: "Custom Installation"; Flags: iscustom

[Components]
Name: "theme"; Description: "Tokyo84 Theme (Kabukicho Midnight — Material 3 x 1984 Shinjuku Neon)"; Types: full themeonly custom; Flags: fixed
Name: "sounds"; Description: "Custom 1984 FM/Synth UI Sound Effects (DX7 & Analog SFX)"; Types: full custom
Name: "activate"; Description: "Automatically activate Tokyo84 in config.ini (creates backup)"; Types: full custom

[Files]
Source: "..\themes\Tokyo84.ini"; DestDir: "{app}\themes"; Components: theme; Flags: ignoreversion
Source: "..\themes\Tokyo84\*"; DestDir: "{app}\themes\Tokyo84"; Components: theme; Flags: ignoreversion recursesubdirs createallsubdirs
Source: "..\sounds\*.wav"; DestDir: "{app}\sounds"; Components: sounds; Flags: ignoreversion

[Code]
function GetDefaultUSDXDir(Param: String): String;
var
  Candidate: String;
begin
  Candidate := ExpandConstant('{userappdata}\ultrastardx');
  if DirExists(Candidate) then begin
    Result := Candidate;
    Exit;
  end;
  Candidate := ExpandConstant('{autopf}\UltraStar Deluxe');
  if DirExists(Candidate) then begin
    Result := Candidate;
    Exit;
  end;
  Candidate := ExpandConstant('{autopf32}\UltraStar Deluxe');
  if DirExists(Candidate) then begin
    Result := Candidate;
    Exit;
  end;
  Result := ExpandConstant('{userappdata}\ultrastardx');
end;

procedure ActivateTokyo84Config();
var
  CfgPath: String;
  Lines: TArrayOfString;
  I: Integer;
  HasTheme, HasSkin: Boolean;
begin
  CfgPath := ExpandConstant('{app}\config.ini');
  if not FileExists(CfgPath) then
    CfgPath := ExpandConstant('{userappdata}\ultrastardx\config.ini');

  if not FileExists(CfgPath) then
    Exit;

  FileCopy(CfgPath, CfgPath + '.tokyo84.bak', False);
  if LoadStringsFromFile(CfgPath, Lines) then begin
    HasTheme := False;
    HasSkin := False;
    for I := 0 to GetArrayLength(Lines) - 1 do begin
      if Pos('theme=', LowerCase(Trim(Lines[I]))) = 1 then begin
        Lines[I] := 'Theme=Tokyo84';
        HasTheme := True;
      end else if Pos('skin=', LowerCase(Trim(Lines[I]))) = 1 then begin
        Lines[I] := 'Skin=KabukichoMidnight';
        HasSkin := True;
      end;
    end;
    if not HasTheme then begin
      SetArrayLength(Lines, GetArrayLength(Lines) + 1);
      Lines[GetArrayLength(Lines) - 1] := 'Theme=Tokyo84';
    end;
    if not HasSkin then begin
      SetArrayLength(Lines, GetArrayLength(Lines) + 1);
      Lines[GetArrayLength(Lines) - 1] := 'Skin=KabukichoMidnight';
    end;
    SaveStringsToFile(CfgPath, Lines, False);
  end;
end;

procedure CurStepChanged(CurStep: TSetupStep);
begin
  if (CurStep = ssPostInstall) and WizardIsComponentSelected('activate') then
    ActivateTokyo84Config();
end;
