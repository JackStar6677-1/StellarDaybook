# Instala venv + paquete editable en la raiz del repo.
# Ejecutar: powershell -ExecutionPolicy Bypass -File .\scripts\install.ps1
$ErrorActionPreference = "Stop"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
Set-Location -LiteralPath $repo

if (-not (Test-Path -LiteralPath ".\config.local.yaml") -and (Test-Path ".\config.example.yaml")) {
    Copy-Item ".\config.example.yaml" ".\config.local.yaml"
    Write-Host "Creado config.local.yaml - edita machine.name (Nova/Nexus)."
}

$venvPy = Join-Path $repo ".venv\Scripts\python.exe"
if ((Test-Path ".\.venv") -and -not (Test-Path -LiteralPath $venvPy)) {
    Write-Host "Eliminando .venv incompleto..."
    Remove-Item -Recurse -Force ".\.venv"
}

if (-not (Test-Path -LiteralPath $venvPy)) {
    $ok = $false
    if (Get-Command py -ErrorAction SilentlyContinue) {
        & py -3 -m venv .venv
        if (Test-Path -LiteralPath $venvPy) { $ok = $true }
    }
    if (-not $ok -and (Get-Command python -ErrorAction SilentlyContinue)) {
        & python -m venv .venv
        if (Test-Path -LiteralPath $venvPy) { $ok = $true }
    }
    if (-not $ok) {
        Write-Error "No se pudo crear .venv. Instala Python 3.11+ desde https://www.python.org/downloads/ y marca 'Add python.exe to PATH'. Cierra y abre PowerShell."
        exit 1
    }
}

& $venvPy -m pip install -U pip
& $venvPy -m pip install -e .

function Ensure-GitIdentity {
    $name = (git config --get user.name 2>$null)
    if ([string]::IsNullOrWhiteSpace($name)) {
        $name = if ($env:USERNAME) { $env:USERNAME } else { "StellarDaybook" }
        & git config user.name $name | Out-Null
        Write-Host "Git user.name configurado localmente como: $name"
    }

    $email = (git config --get user.email 2>$null)
    if ([string]::IsNullOrWhiteSpace($email)) {
        $user = if ($env:USERNAME) { $env:USERNAME } else { "stellar-daybook" }
        $machine = if ($env:COMPUTERNAME) { $env:COMPUTERNAME.ToLowerInvariant() } else { "local" }
        $email = "$user@$machine.local"
        & git config user.email $email | Out-Null
        Write-Host "Git user.email configurado localmente como: $email"
    }
}

Ensure-GitIdentity
Write-Host "Listo. Activa con: .\.venv\Scripts\Activate.ps1"
Write-Host "Prueba: $venvPy -m stellar_daybook --console"
