param(
    [switch]$SkipTests,
    [switch]$AllowDirty
)

Write-Warning "build_beta9_release.ps1 is kept only as a compatibility entry point. Use build_release.ps1 for current releases."
& "$PSScriptRoot\build_release.ps1" -SkipTests:$SkipTests -AllowDirty:$AllowDirty
exit $LASTEXITCODE
