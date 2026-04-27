# Instala venv + paquete editable en la raíz del repo.
$ErrorActionPreference = "Stop"
Set-Location (Resolve-Path (Join-Path $PSScriptRoot ".."))
if (-not (Test-Path ".\config.local.yaml")) {
    Copy-Item ".\config.example.yaml" ".\config.local.yaml"
    Write-Host "Creado config.local.yaml — edita machine.name (Nova/Nexus)."
}
$venvPy = ".\.venv\Scripts\python.exe"
if (Get-Command py -ErrorAction SilentlyContinue) {
    py -3 -m venv .venv
} else {
    python -m venv .venv
}
& $venvPy -m pip install -U pip
& $venvPy -m pip install -e .
Write-Host "Listo. Activa con: .\.venv\Scripts\Activate.ps1"
Write-Host "Prueba: $venvPy -m stellar_daybook --console"
