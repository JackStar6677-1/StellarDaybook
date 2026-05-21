@echo off
setlocal
cd /d "%~dp0.."
if exist ".git" (
  echo Ya existe .git — no se hace nada.
  exit /b 0
)
where git >nul 2>nul
if errorlevel 1 (
  echo Git no esta en PATH.
  exit /b 1
)
git init -b main
git config user.name "%USERNAME%"
git config user.email "%USERNAME%@%COMPUTERNAME%.local"
git add -A
git commit -m "chore: base del repo StellarDaybook (config, carpetas, plantilla)"
echo Listo. Siguiente paso opcional:
echo   gh repo create StellarDaybook --public --source=. --remote=origin --push
exit /b 0
