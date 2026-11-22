<#
.SYNOPSIS
    Tokyo84 — UltraStar Deluxe Theme Uninstaller (Windows)
#>
param(
    [string]$Path = ""
)

$ErrorActionPreference = "Stop"
$ThemeName = "Tokyo84"

if (-not $Path) {
    $candidates = @(
        (Join-Path $env:APPDATA "ultrastardx"),
        (Join-Path $env:ProgramFiles "UltraStar Deluxe"),
        (Join-Path ${env:ProgramFiles(x86)} "UltraStar Deluxe")
    )
    foreach ($c in $candidates) {
        if ($c -and (Test-Path (Join-Path $c "themes\$ThemeName"))) {
            $Path = $c
            break
        }
    }
}

if (-not $Path) {
    Write-Host "Could not locate Tokyo84 installation. Pass -Path 'C:\path\to\ultrastardx'." -ForegroundColor Yellow
    exit 1
}

Write-Host "Uninstalling Tokyo84 from $Path..." -ForegroundColor Cyan
Remove-Item -Recurse -Force -ErrorAction SilentlyContinue (Join-Path $Path "themes\$ThemeName")
Remove-Item -Force -ErrorAction SilentlyContinue (Join-Path $Path "themes\$ThemeName.ini")

$BackupSounds = Join-Path $Path "sounds\.tokyo84_backup"
if (Test-Path $BackupSounds) {
    Copy-Item -Force (Join-Path $BackupSounds "*") (Join-Path $Path "sounds")
    Remove-Item -Recurse -Force $BackupSounds
    Write-Host "  [OK] Restored original sound files." -ForegroundColor Green
}

foreach ($bak in @((Join-Path $Path "config.ini.tokyo84.bak"), (Join-Path $env:APPDATA "ultrastardx\config.ini.tokyo84.bak"))) {
    if (Test-Path $bak) {
        Move-Item -Force $bak ($bak -replace "\.tokyo84\.bak$", "")
        Write-Host "  [OK] Restored original config.ini." -ForegroundColor Green
    }
}

Write-Host "Done! Tokyo84 has been cleanly uninstalled." -ForegroundColor Green
