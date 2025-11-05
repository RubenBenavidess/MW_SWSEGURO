#!/usr/bin/env bash
set -euo pipefail

# Uninstaller para el servicio systemd creado por installer_install.sh
# Uso: sudo ./installer_uninstall.sh

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="mw_seguros_client"
UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}.service"

echo "Deteniendo y deshabilitando servicio ${SERVICE_NAME} (si existe)..."
if systemctl is-active --quiet "${SERVICE_NAME}.service"; then
    systemctl stop "${SERVICE_NAME}.service" || true
fi

if systemctl is-enabled --quiet "${SERVICE_NAME}.service"; then
    systemctl disable "${SERVICE_NAME}.service" || true
fi

if [[ -f "${UNIT_PATH}" ]]; then
    echo "Eliminando unit file ${UNIT_PATH}"
    rm -f "${UNIT_PATH}"
fi

echo "Recargando systemd"
systemctl daemon-reload
systemctl reset-failed

echo "Desinstalación completada."

exit 0
