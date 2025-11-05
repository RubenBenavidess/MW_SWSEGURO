#!/usr/bin/env bash
set -euo pipefail

# Instalador systemd para el script cliente
# Uso: sudo ./installer_install.sh [--user username] [--python /usr/bin/python3]

REPO_ROOT="$(cd "$(dirname "$0")" && pwd)"
SERVICE_NAME="mw_seguros_client"
UNIT_PATH="/etc/systemd/system/${SERVICE_NAME}.service"
PYTHON="python3"
RUN_AS_USER=""

print_usage() {
    echo "Uso: sudo $0 [--user username] [--python /ruta/a/python]"
    exit 1
}

while [[ $# -gt 0 ]]; do
    case "$1" in
        --user)
            shift; RUN_AS_USER="$1"; shift;;
        --python)
            shift; PYTHON="$1"; shift;;
        -h|--help)
            print_usage;;
        *)
            echo "Argumento desconocido: $1"; print_usage;;
    esac
done

echo "Instalando servicio ${SERVICE_NAME}..."

if [[ ! -f "${REPO_ROOT}/client/client.py" ]]; then
    echo "ERROR: No se encontró el archivo client/client.py en ${REPO_ROOT}" >&2
    exit 2
fi

mkdir -p "$(dirname "${UNIT_PATH}")"

echo "Escribiendo unit file en ${UNIT_PATH}"
cat > "${UNIT_PATH}" <<EOF
[Unit]
Description=MW_SEGURO Client Service
After=network.target

[Service]
Type=simple
WorkingDirectory=${REPO_ROOT}
ExecStart=${PYTHON} ${REPO_ROOT}/client/client.py
Restart=on-failure
RestartSec=5
LimitNOFILE=65536
${RUN_AS_USER:+User=${RUN_AS_USER}}

[Install]
WantedBy=multi-user.target
EOF

echo "Recargando systemd y habilitando servicio"
systemctl daemon-reload
systemctl enable --now "${SERVICE_NAME}.service"

echo "Instalación completada. Estado del servicio:"
systemctl status "${SERVICE_NAME}.service" --no-pager || true

echo "NOTA: Este servicio ejecuta el script 'client/client.py'. Asegúrate de ejecutarlo solo en entornos controlados y con autorización." 

exit 0
