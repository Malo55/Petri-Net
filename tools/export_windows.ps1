# Exporte PetriNetLearn.exe (Godot 4.3 + templates requis)
$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
$godot = Join-Path $root "tools\godot\Godot_v4.3-stable_win64_console.exe"
if (-not (Test-Path $godot)) {
    Write-Error "Godot introuvable: $godot"
}
$buildDir = Join-Path $root "build"
New-Item -ItemType Directory -Force -Path $buildDir | Out-Null
$out = Join-Path $buildDir "PetriNetLearn.exe"
& $godot --path (Join-Path $root "godot_project") --headless --export-release "Windows Desktop" $out
if (-not (Test-Path $out)) {
    Write-Error "Export échoué"
}
Write-Host "OK: $out ($((Get-Item $out).Length) octets)"
