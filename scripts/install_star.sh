#!/usr/bin/env bash
# Instala y activa StellarDaybook en el servidor star (Ubuntu Linux).
# Uso: bash scripts/install_star.sh
set -euo pipefail

REPO_DIR="/opt/stacks/repos/stellardaybook"
LOG_DIR="/var/log/stellar-daybook"
SERVICE="stellardaybook-star"
GITHUB_REPO="https://github.com/JackStar6677-1/StellarDaybook.git"

echo "[INFO] StellarDaybook Star — instalador"

# Clonar o actualizar el repo
if [ -d "$REPO_DIR/.git" ]; then
    echo "[INFO] Repositorio existe — actualizando con git pull..."
    git -C "$REPO_DIR" pull --no-rebase
else
    echo "[INFO] Clonando repositorio en $REPO_DIR..."
    sudo mkdir -p "$(dirname "$REPO_DIR")"
    sudo chown jack:jack "$(dirname "$REPO_DIR")"
    git clone "$GITHUB_REPO" "$REPO_DIR"
fi

cd "$REPO_DIR"

# Entorno virtual
echo "[INFO] Creando entorno virtual..."
python3 -m venv .venv
.venv/bin/pip install --upgrade pip -q
.venv/bin/pip install -e ".[star]" -q 2>/dev/null || .venv/bin/pip install -e . -q

# Instalar psutil explícitamente (no requiere win32)
.venv/bin/pip install psutil requests PyYAML tzdata -q

# Config local para Star
if [ ! -f "config.local.yaml" ]; then
    cp config.example.yaml config.local.yaml
    sed -i 's/name: "Nova"/name: "Star"/' config.local.yaml
    # Ajustar ubicación Padre Hurtado (misma que Nova — ambos en Chile)
    echo "[INFO] config.local.yaml creado con machine.name=Star"
    echo "[ADVERTENCIA] Revisa config.local.yaml si quieres cambiar la ubicación del clima."
fi

# Identidad git
git config user.name  "Jack"        2>/dev/null || true
git config user.email "jack@star.local" 2>/dev/null || true

# Directorio de logs
sudo mkdir -p "$LOG_DIR"
sudo chown jack:jack "$LOG_DIR"

# Instalar servicio systemd
echo "[INFO] Instalando servicio systemd $SERVICE..."
sudo cp scripts/stellardaybook-star.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable "$SERVICE"
sudo systemctl restart "$SERVICE"

echo ""
echo "[SUCCESS] StellarDaybook activo en star."
echo "  Estado:  sudo systemctl status $SERVICE"
echo "  Logs:    journalctl -u $SERVICE -f"
echo "  Push ya: cd $REPO_DIR && .venv/bin/python -m stellar_daybook --once"
