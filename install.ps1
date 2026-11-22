<#
.SYNOPSIS
    Tokyo84 — UltraStar Deluxe Theme & 80s Synth Sound Pack Installer (Windows)
.DESCRIPTION
    Auto-detects UltraStar Deluxe installation paths, installs the Tokyo84 theme
    (Kabukicho Midnight colorway), optionally installs custom 1984 FM/synth UI sounds
    with automatic backup, and activates the theme in config.ini.
#>
[CmdletBinding()]
param(
    [string]$Path = "",
    [switch]$NoSounds,
    [switch]$NoActivate,
    [switch]$Yes
)

$ErrorActionPreference = "Stop"
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$ThemeName = "Tokyo84"
$SkinName = "KabukichoMidnight"

Write-Host ""
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  TOKYO84  —  UltraStar Deluxe Theme Installer (Windows)" -ForegroundColor Cyan
Write-Host "  Kabukicho Midnight | Material Design 3 x 1984 Shinjuku Neon" -ForegroundColor DarkGray
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host ""

function Find-USDXDirectory {
    $candidates = @(
        (Join-Path $env:APPDATA "ultrastardx"),
        (Join-Path $env:ProgramFiles "UltraStar Deluxe"),
        (Join-Path ${env:ProgramFiles(x86)} "UltraStar Deluxe"),
        (Join-Path $env:LOCALAPPDATA "Programs\UltraStar Deluxe")
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path $c)) {
            return $c
        }
    }
    return $null
}

if (-not $Path) {
    $detected = Find-USDXDirectory
    if ($detected) {
        $Path = $detected
        Write-Host "  Detected UltraStar Deluxe folder: $Path" -ForegroundColor Cyan
    } else {
        $Path = Join-Path $env:APPDATA "ultrastardx"
        Write-Host "  [!] Could not auto-detect an existing USDX folder." -ForegroundColor Yellow
        Write-Host "      Defaulting to: $Path" -ForegroundColor DarkGray
    }

    if (-not $Yes) {
        $custom = Read-Host "Press Enter to install to [$Path], or type a custom path"
        if ($custom) { $Path = $custom.Trim('"') }
    }
}

$ThemesDest = Join-Path $Path "themes"
$ThemeFolder = Join-Path $ThemesDest $ThemeName
$SoundsDest = Join-Path $Path "sounds"

Write-Host ""
Write-Host "Installing theme files..." -ForegroundColor Cyan
New-Item -ItemType Directory -Force -Path $ThemeFolder | Out-Null
Copy-Item -Force (Join-Path $ScriptDir "themes\Tokyo84.ini") (Join-Path $ThemesDest "Tokyo84.ini")
Copy-Item -Recurse -Force (Join-Path $ScriptDir "themes\Tokyo84\*") $ThemeFolder
Write-Host "  [OK] Theme installed to: $ThemeFolder" -ForegroundColor Green

if (-not $NoSounds -and (Test-Path (Join-Path $ScriptDir "sounds"))) {
    New-Item -ItemType Directory -Force -Path $SoundsDest | Out-Null
    $BackupDir = Join-Path $SoundsDest ".tokyo84_backup"
    if (-not (Test-Path $BackupDir)) {
        New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
        Get-ChildItem (Join-Path $ScriptDir "sounds\*.wav") | ForEach-Object {
            $existing = Join-Path $SoundsDest $_.Name
            if (Test-Path $existing) {
                Copy-Item -Force $existing (Join-Path $BackupDir $_.Name)
            }
        }
    }
    Copy-Item -Force (Join-Path $ScriptDir "sounds\*.wav") $SoundsDest
    Write-Host "  [OK] 1984 Tokyo FM/Synth UI sounds installed to: $SoundsDest" -ForegroundColor Green
}

if (-not $NoActivate) {
    $cfgCandidates = @(
        (Join-Path $Path "config.ini"),
        (Join-Path $env:APPDATA "ultrastardx\config.ini")
    )
    $cfg = $cfgCandidates | Where-Object { Test-Path $_ } | Select-Object -First 1
    if ($cfg) {
        Copy-Item -Force $cfg "$cfg.tokyo84.bak"
        $content = Get-Content -Raw -Encoding UTF8 $cfg
        if ($content -match "(?im)^Theme\s*=.*$") {
            $content = $content -replace "(?im)^Theme\s*=.*$", "Theme=$ThemeName"
        } else {
            $content += "`r`n[Themes]`r`nTheme=$ThemeName`r`n"
        }
        if ($content -match "(?im)^Skin\s*=.*$") {
            $content = $content -replace "(?im)^Skin\s*=.*$", "Skin=$SkinName"
        } else {
            $content += "Skin=$SkinName`r`n"
        }
        Set-Content -Path $cfg -Value $content -Encoding UTF8
        Write-Host "  [OK] Activated Tokyo84 / KabukichoMidnight in: $cfg" -ForegroundColor Green
        Write-Host "       Backup saved to: $cfg.tokyo84.bak" -ForegroundColor DarkGray
    } else {
        Write-Host "  [!] config.ini not found — choose 'Tokyo84' in USDX Options > Themes." -ForegroundColor Yellow
    }
}

Write-Host ""
Write-Host "============================================================" -ForegroundColor Magenta
Write-Host "  Installation complete! Launch UltraStar Deluxe to enjoy." -ForegroundColor Green
Write-Host "============================================================" -ForegroundColor Magenta
