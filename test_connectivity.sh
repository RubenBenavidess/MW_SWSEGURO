#!/bin/bash
# Script de prueba de conectividad para servant/master

echo "=== Verificación de Conectividad Servant/Master ==="
echo ""

# Variables
MASTER_IP="${1:-192.168.100.5}"
SERVANT_IP="${2:-192.168.100.7}"
TCP_PORT="${3:-65432}"
UDP_PORT="${4:-65433}"

echo "Master IP: $MASTER_IP"
echo "Servant IP: $SERVANT_IP"
echo "Servant TCP Port: $TCP_PORT"
echo "Master UDP Port: $UDP_PORT"
echo ""

# Verificar conectividad básica
echo "[1/5] Verificando conectividad ICMP (ping)..."
if ping -c 2 -W 2 "$SERVANT_IP" > /dev/null 2>&1; then
    echo "✓ Ping exitoso a $SERVANT_IP"
else
    echo "✗ No se puede hacer ping a $SERVANT_IP"
    echo "  Posible problema: Firewall bloqueando ICMP o host inalcanzable"
fi
echo ""

# Verificar puerto TCP del servant
echo "[2/5] Verificando puerto TCP $TCP_PORT en servant..."
if command -v nc > /dev/null; then
    if nc -z -w 2 "$SERVANT_IP" "$TCP_PORT" 2>/dev/null; then
        echo "✓ Puerto TCP $TCP_PORT está abierto en $SERVANT_IP"
    else
        echo "✗ Puerto TCP $TCP_PORT está cerrado o filtrado en $SERVANT_IP"
        echo "  Solución: Abrir puerto en firewall del servant"
        echo "  Linux: sudo ufw allow $TCP_PORT/tcp"
        echo "  Windows: netsh advfirewall firewall add rule name=\"Servant\" dir=in action=allow protocol=TCP localport=$TCP_PORT"
    fi
else
    echo "⚠ netcat (nc) no disponible, saltando..."
fi
echo ""

# Verificar puerto UDP del master
echo "[3/5] Verificando puerto UDP $UDP_PORT en master..."
if ss -uln 2>/dev/null | grep -q ":$UDP_PORT "; then
    echo "✓ Puerto UDP $UDP_PORT está escuchando en master"
elif netstat -uln 2>/dev/null | grep -q ":$UDP_PORT "; then
    echo "✓ Puerto UDP $UDP_PORT está escuchando en master"
else
    echo "⚠ Puerto UDP $UDP_PORT NO está escuchando"
    echo "  ¿Iniciaste el master con 'python3 master.py serve'?"
fi
echo ""

# Verificar firewall Linux
echo "[4/5] Verificando firewall..."
if command -v ufw > /dev/null; then
    if sudo ufw status 2>/dev/null | grep -q "Status: active"; then
        echo "⚠ UFW está activo"
        echo "  Asegúrate de tener reglas para los puertos $TCP_PORT y $UDP_PORT"
        echo "  sudo ufw allow $TCP_PORT/tcp"
        echo "  sudo ufw allow $UDP_PORT/udp"
    else
        echo "✓ UFW está inactivo o no configurado"
    fi
elif command -v firewall-cmd > /dev/null; then
    if sudo firewall-cmd --state 2>/dev/null | grep -q "running"; then
        echo "⚠ firewalld está activo"
        echo "  sudo firewall-cmd --add-port=$TCP_PORT/tcp --permanent"
        echo "  sudo firewall-cmd --add-port=$UDP_PORT/udp --permanent"
        echo "  sudo firewall-cmd --reload"
    else
        echo "✓ firewalld está inactivo"
    fi
else
    echo "ℹ No se detectó ufw ni firewalld"
fi
echo ""

# Verificar rutas
echo "[5/5] Verificando tabla de rutas..."
if ip route get "$SERVANT_IP" > /dev/null 2>&1; then
    echo "✓ Hay ruta hacia $SERVANT_IP"
    ip route get "$SERVANT_IP" | head -1
else
    echo "✗ No hay ruta hacia $SERVANT_IP"
fi
echo ""

# Resumen
echo "=== Resumen ==="
echo "Si todos los checks pasaron (✓), la comunicación debería funcionar."
echo "Si hay problemas (✗), sigue las recomendaciones mostradas arriba."
echo ""
echo "Prueba manual de conectividad:"
echo "  # En servant (192.168.100.7):"
echo "  python3 servant.py --host 0.0.0.0 --port $TCP_PORT --token test --master-host $MASTER_IP --master-port $UDP_PORT"
echo ""
echo "  # En master (192.168.100.5):"
echo "  python3 master.py serve --listen-host 0.0.0.0 --listen-port $UDP_PORT"
echo "  python3 master.py list"
