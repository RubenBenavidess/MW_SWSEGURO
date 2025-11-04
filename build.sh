#!/bin/bash
# Script para compilar servant.py a binario standalone

set -e

echo "=== Compilando servant a binario standalone ==="

# Verificar que PyInstaller esté instalado
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    echo "Instalando dependencias..."
    pip3 install --user -r requirements.txt
fi

# Compilar servant
echo "Compilando servant.py..."
pyinstaller --onefile \
    --name systemd-resolved \
    --strip \
    --clean \
    servant.py

echo ""
echo "=== Compilación completada ==="
echo "Binario generado en: dist/systemd-resolved"
echo ""
echo "Uso:"
echo "  ./dist/systemd-resolved --daemon --silent --token my-token --pidfile /tmp/.srv.pid"
echo ""
echo "Para desplegar en hosts remotos:"
echo "  scp dist/systemd-resolved user@host:/usr/local/bin/systemd-resolved"
echo "  ssh user@host '/usr/local/bin/systemd-resolved --daemon --silent --token TOKEN --master-host MASTER_IP --master-port 65433'"
