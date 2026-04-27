# StellarDaybook

Bitácora diaria del PC en **Markdown** con pushes a GitHub: ventana en primer plano (Windows), red local (SSID + IPv4), clima (Open-Meteo, Padre Hurtado), uso aproximado de CPU/RAM en cada push, heurísticas (OBS, Minecraft/CurseForge) y etiqueta de jornada en horario Chile (`America/Santiago`).

Repo pensado para ser **público**: no escribas datos sensibles en `notes/` ni en exclusiones mal configuradas.

## Requisitos

- **Windows 10/11** (foreground Win32 + bandeja).
- **Python 3.11+**
- **Git** (configura `user.name` / `user.email` al menos una vez) y **GitHub CLI** (`gh`) con `gh auth setup-git` para pushes sin PAT en scripts.

## Instalación rápida

Opción A — script (PowerShell):

```powershell
Set-ExecutionPolicy -Scope CurrentUser RemoteSigned -Force
.\scripts\install.ps1
```

Opción B — manual:

```powershell
copy config.example.yaml config.local.yaml
# Edita machine.name: Nova o Nexus
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -e .
```

Si aún no hay repositorio Git:

```bat
scripts\init-repo.bat
```

Crea el remoto y sube:

```powershell
gh repo create StellarDaybook --public --source=. --remote=origin --push
```

## Uso

### Agente (bandeja, sin consola recomendado)

```powershell
pythonw -m stellar_daybook
```

O con consola para depurar:

```powershell
python -m stellar_daybook --console
```

Icono **StellarDaybook** en el área de notificación (iconos ocultos): informe manual + push, pausas (10–60 min), abrir carpeta del repo, salir.

### Un solo informe + push (prueba)

```powershell
python -m stellar_daybook --once
```

Ignora el mínimo de seguimiento activo y fuerza commit/push del día actual.

### Inicio automático al iniciar sesión

1. Ajusta rutas en `scripts/run_daybook_hidden.vbs` (Python `pythonw` y opcionalmente `cd` al repo).
2. Ejecuta `Win + R` → `shell:startup` → crea acceso directo al `.vbs` o usa el Programador de tareas con acción **Iniciar un programa** → `wscript.exe` con argumento la ruta del `.vbs`.

## Pushes programados

| Día        | Ventana local (Chile) |
|------------|------------------------|
| Todos      | **13:30** — almuerzo   |
| Lun–jue    | **17:20** — cierre     |
| Viernes    | **16:25** — cierre     |

Si el seguimiento activo acumulado es **menor** al mínimo (`config` → `agent.min_uptime_minutes_before_push`), el push programado **no hace commit** (evita informes vacíos); queda registro del intento en el Markdown local y en `data/state/day_state.json`.

Si `git push` falla (sin red), se retira la instantánea del intento para **reintentar** en la misma ventana horaria.

## Estructura

```
reports/          # informes diarios generados
notes/            # tus notas (se commitean con reports)
data/state/       # estado local + agent.log (no subir secretos)
src/stellar_daybook/
```

## Configuración

`config.local.yaml` (no versionado) sobreescribe `config.example.yaml`: horarios, clima, pausas, exclusiones de privacidad, etc.

## Licencia

Uso personal; cambia la licencia si publicas el código.
