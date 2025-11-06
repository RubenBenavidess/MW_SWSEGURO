# Servidor Maestro Flask con WebSockets

Este es el servidor maestro que gestiona las conexiones de clientes mediante WebSockets.

## Instalación

### Opcional activar entorno virtual
```bash
python -m venv venv
```

```bash
source venv/bin/activate
```

### Instalación de dependencias

```bash
pip install -r requirements.txt
```

## Ejecución

```bash
python app.py
```

El servidor flask estará disponible en `http://localhost:5000`
El servidor websockets para los bots estará disponible en `ws://localhost:5001`

## Endpoints

### REST API

- `GET /` - Estado del servidor
- `GET /clients` - Lista de clientes conectados
- `POST /broadcast` - Enviar mensaje broadcast a todos los clientes
  ```json
  {
    "message": "Tu mensaje aquí"
  }
  ```

### WebSocket Events

**Cliente -> Servidor:**
- `connect` - Conexión de cliente
- `disconnect` - Desconexión de cliente
- `ping` - Ping al servidor

**Servidor -> Cliente:**
- `client_connected` - Notificación de nuevo cliente
- `client_disconnected` - Notificación de desconexión
- `clients_update` - Actualización de lista de clientes
- `broadcast_message` - Mensaje broadcast
- `pong` - Respuesta a ping
