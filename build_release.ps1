param(
    [string]$ExeName = "MCW Launcher.exe",
    [switch]$SkipTests,
    [switch]$AllowDirty
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

function Write-Step {
    param([string]$Message)
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-Checked {
    param([string]$Description, [scriptblock]$Command)
    & $Command
    if ($LASTEXITCODE -ne 0) {
        throw "$Description failed with exit code $LASTEXITCODE."
    }
}

if (-not (Test-Path ".\mcw_launcher.spec")) {
    throw "mcw_launcher.spec was not found. Run this script from the project root."
}
if (-not (Test-Path ".\tools\build_release_zip.py")) {
    throw "tools/build_release_zip.py was not found."
}
if (-not (Test-Path ".\tools\release_preflight.py")) {
    throw "tools/release_preflight.py was not found."
}

$Version = (python -c "from src.config import VERSION_ID; print(VERSION_ID)").Trim()
$VersionTag = (python -c "from src.config import VERSION_TAG; print(VERSION_TAG)").Trim()
if ($LASTEXITCODE -ne 0 -or -not $Version -or -not $VersionTag) {
    throw "Unable to read release version from src/config.py."
}

Write-Step "Preparing MCW Launcher $VersionTag"

if (-not $AllowDirty) {
    $gitStatus = git status --porcelain
    if ($LASTEXITCODE -ne 0) {
        throw "Unable to read Git status."
    }
    if ($gitStatus) {
        Write-Host $gitStatus
        throw "Working tree is not clean. Commit or restore changes, or pass -AllowDirty for a local test build."
    }
}

Write-Step "Running release preflight"
Invoke-Checked "Release preflight" { python -m tools.release_preflight }
Invoke-Checked "Python compilation" { python -m compileall -q launcher.py src tools }

if (-not $SkipTests) {
    Write-Step "Running complete regression suite"
    Invoke-Checked "Tests" { python -m pytest test -q }
}

Write-Step "Removing previous build output"
Remove-Item ".\build" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item ".\dist" -Recurse -Force -ErrorAction SilentlyContinue
Remove-Item ".\release" -Recurse -Force -ErrorAction SilentlyContinue

Write-Step "Building one-file windowed EXE"
Invoke-Checked "PyInstaller build" { python -m PyInstaller --clean --noconfirm mcw_launcher.spec }

$ExePath = Join-Path ".\dist" $ExeName
if (-not (Test-Path $ExePath)) {
    throw "Expected EXE was not created: $ExePath"
}

Write-Step "Creating updater-compatible ZIP"
Invoke-Checked "Release package build" { python -m tools.build_release_zip --exe $ExePath --version $Version }

$ZipName = "MCW-Launcher-v$Version-windows-x64.zip"
$ZipPath = Join-Path ".\release" $ZipName
$ShaPath = "$ZipPath.sha256"
$ReleaseNotes = ".\docs\RELEASE-$VersionTag.md"

if (-not (Test-Path $ZipPath)) {
    throw "Expected release ZIP was not created: $ZipPath"
}
if (-not (Test-Path $ShaPath)) {
    throw "Expected checksum file was not created: $ShaPath"
}
if (-not (Test-Path $ReleaseNotes)) {
    throw "Release notes were not found: $ReleaseNotes"
}

$ExeHash = (Get-FileHash $ExePath -Algorithm SHA256).Hash.ToLowerInvariant()
$ZipHash = (Get-FileHash $ZipPath -Algorithm SHA256).Hash.ToLowerInvariant()

Write-Host ""
Write-Host "Release build completed successfully." -ForegroundColor Green
Write-Host "Version: $VersionTag"
Write-Host "EXE: $ExePath"
Write-Host "EXE SHA-256: $ExeHash"
Write-Host "ZIP: $ZipPath"
Write-Host "ZIP SHA-256: $ZipHash"
Write-Host "Checksum: $ShaPath"
Write-Host "Release notes: $ReleaseNotes"
Write-Host ""
Write-Host "The API JSON publication/update time is intentionally not modified by this script."
