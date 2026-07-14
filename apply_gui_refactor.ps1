param(
    [Parameter(Mandatory = $false)]
    [string]$RepoPath = "."
)

$ErrorActionPreference = "Stop"
$RepoPath = (Resolve-Path $RepoPath).Path
$SourceRoot = $PSScriptRoot
$SourceSrc = Join-Path $SourceRoot "src"
$DestinationSrc = Join-Path $RepoPath "src"
$SourceTest = Join-Path $SourceRoot "test"
$DestinationTest = Join-Path $RepoPath "test"

if (-not (Test-Path $DestinationSrc)) {
    throw "Repo path does not contain a src folder: $RepoPath"
}

Copy-Item (Join-Path $SourceSrc "*") $DestinationSrc -Recurse -Force
Copy-Item (Join-Path $SourceRoot "launcher.py") (Join-Path $RepoPath "launcher.py") -Force

if (Test-Path $SourceTest) {
    New-Item -ItemType Directory -Force -Path $DestinationTest | Out-Null
    Copy-Item (Join-Path $SourceTest "*") $DestinationTest -Recurse -Force
}

Write-Host "MCW Launcher GUI + managed Java refactor copied to: $RepoPath"
Write-Host "Run tests: pytest test/core/java"
Write-Host "Run launcher: python launcher.py"
