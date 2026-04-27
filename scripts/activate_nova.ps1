# Activa StellarDaybook en la laptop (Nova): venv, config, arranque ahora + Inicio de Windows.
# Ejecutar desde cualquier sitio:
#   powershell -ExecutionPolicy Bypass -File "C:\Users\Jack\Documents\GitHub\Experimentos\StellarDaybook\scripts\activate_nova.ps1"
$ErrorActionPreference = "Continue"
$repo = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$log = Join-Path $repo "_nova_activation_log.txt"

function Write-Log {
    param([string]$Message)
    $line = "$(Get-Date -Format 'o') $Message"
    Add-Content -Path $log -Value $line -Encoding UTF8
    Write-Host $line
}

Set-Location -LiteralPath $repo
"=== StellarDaybook Nova $(Get-Date -Format o) ===" | Out-File -FilePath $log -Encoding utf8
Write-Log "Repo: $repo"

# config.local.yaml -> Nova
$cfg = Join-Path $repo "config.local.yaml"
$ex = Join-Path $repo "config.example.yaml"
if (-not (Test-Path -LiteralPath $cfg) -and (Test-Path -LiteralPath $ex)) {
    Copy-Item -LiteralPath $ex -Destination $cfg
    Write-Log "Creado config.local.yaml desde example."
}
if (Test-Path -LiteralPath $cfg) {
    $raw = Get-Content -LiteralPath $cfg -Raw
    if ($raw -match "(?m)^(\s*name:\s*)Nexus\s*$") {
        $raw2 = $raw -replace "(?m)^(\s*name:\s*)Nexus\s*$", '${1}Nova'
        Set-Content -LiteralPath $cfg -Value $raw2 -Encoding UTF8
        Write-Log "machine.name -> Nova"
    } else {
        Write-Log "config.local.yaml listo (name ya Nova u otro)."
    }
}

$installScript = Join-Path $PSScriptRoot "install.ps1"
if (Test-Path -LiteralPath $installScript) {
    try {
        & $installScript 2>&1 | ForEach-Object { Write-Log $_.ToString() }
    } catch {
        Write-Log "install.ps1 error: $($_.Exception.Message)"
    }
} else {
    Write-Log "ERROR: No se encuentra install.ps1 en $PSScriptRoot"
}

$pip = Join-Path $repo ".venv\Scripts\pip.exe"
if (Test-Path -LiteralPath $pip) {
    Push-Location $repo
    & $pip install -e . 2>&1 | ForEach-Object { Write-Log $_.ToString() }
    Pop-Location
} else {
    Write-Log "ERROR: No hay .venv\Scripts\pip.exe. Revisa Python en PATH y ejecuta .\scripts\install.ps1"
}

$pyw = Join-Path $repo ".venv\Scripts\pythonw.exe"
$vbs = Join-Path $repo "scripts\run_daybook_hidden.vbs"
Write-Log "pythonw existe: $(Test-Path -LiteralPath $pyw)"
Write-Log "vbs existe: $(Test-Path -LiteralPath $vbs)"

if (-not (Test-Path -LiteralPath $pyw)) {
    Write-Log "No se arranca wscript: falta $pyw (venv no creado o install fallo)."
}

if ((Test-Path -LiteralPath $vbs) -and (Test-Path -LiteralPath $pyw)) {
    $vbsFull = (Resolve-Path -LiteralPath $vbs).Path
    $p = Start-Process -FilePath "C:\Windows\System32\wscript.exe" -ArgumentList "`"$vbsFull`"" -WindowStyle Hidden -PassThru
    Write-Log "wscript PID $($p.Id)"
} elseif (Test-Path -LiteralPath $vbs) {
    Write-Log "Omitido arranque del agente hasta que exista pythonw."
}

if ((Test-Path -LiteralPath $vbs) -and (Test-Path -LiteralPath $pyw)) {
    $startup = [Environment]::GetFolderPath("Startup")
    $lnkPath = Join-Path $startup "StellarDaybook.lnk"
    if (Test-Path -LiteralPath $lnkPath) { Remove-Item -LiteralPath $lnkPath -Force }
    $wsh = New-Object -ComObject WScript.Shell
    $sc = $wsh.CreateShortcut($lnkPath)
    $sc.TargetPath = "C:\Windows\System32\wscript.exe"
    $vbsResolved = (Resolve-Path -LiteralPath $vbs).Path
    $sc.Arguments = "`"$vbsResolved`""
    $sc.WorkingDirectory = $repo
    $sc.Save()
    Write-Log "Acceso directo Inicio: $lnkPath"
} else {
    Write-Log "No se creo acceso directo en Inicio: falta venv o VBS."
}

Get-Process -Name wscript, pythonw -ErrorAction SilentlyContinue | Select-Object -First 8 Name, Id | ForEach-Object { Write-Log "proc $($_.Name) $($_.Id)" }
Write-Log "Fin. Log: $log"
