@echo off
cd /d "%~dp0"
if exist "build\PetriNetLearn.exe" (
  start "" "build\PetriNetLearn.exe"
) else (
  echo Executable introuvable. Ouvrez godot_project dans Godot 4.3 ou lancez tools\export_windows.ps1
  pause
)
