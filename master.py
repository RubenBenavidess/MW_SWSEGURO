#!/usr/bin/env python3
"""
Master client: conecta al servant en localhost y envía un comando autenticado.
Uso típico:
    python3 master.py --host 127.0.0.1 --port 65432 --token changeme-token --action run

Por seguridad, por defecto usa localhost; modifica token antes de usar en entornos reales.
"""

import argparse
import json
import socket
import sys
import threading
import time
from typing import Tuple, Dict, Any

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = 65432
DEFAULT_TOKEN = "changeme-token"
DEFAULT_REGISTRY_FILE = "/tmp/servants_registry.json"
DEFAULT_REGISTRY_LISTEN_PORT = 65433


def send_command(host: str, port: int, token: str, action: str = 'run', count: int = 100) -> None:
    payload = {
        'token': token,
        'action': action,
        'count': count,
    }
    data = json.dumps(payload).encode('utf-8')

    try:
        with socket.create_connection((host, port), timeout=5) as sock:
            sock.sendall(data)
            try:
                resp = sock.recv(4096)
                if resp:
                    print('Response:', resp.decode('utf-8'))
            except Exception:
                # It's okay if servant doesn't reply
                pass
    except Exception as e:
        print(f"Failed to connect to {host}:{port} -> {e}")


def serve_registry(listen_host: str, listen_port: int, registry_file: str) -> None:
    """Run a simple UDP listener that accepts JSON announcements from servants
    and writes a registry file at `registry_file`.
    """
    registry: Dict[str, Dict[str, Any]] = {}

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((listen_host, listen_port))
    print(f"Registry listening on {listen_host}:{listen_port}")

    def dump_registry():
        try:
            with open(registry_file, 'w') as f:
                json.dump(registry, f, indent=2)
        except Exception as e:
            print("Failed to write registry file:", e)

    try:
        while True:
            data, addr = sock.recvfrom(4096)
            try:
                payload = json.loads(data.decode('utf-8'))
                host = payload.get('host') or addr[0]
                port = int(payload.get('port', 0) or 0)
                token = payload.get('token')
                ts = int(payload.get('ts', int(time.time())))

                key = f"{host}:{port}"
                registry[key] = {'host': host, 'port': port, 'token': token, 'last_seen': ts}
                print(f"Announce from {key} (token={token})")
                dump_registry()
            except Exception as e:
                print("Invalid announce from", addr, e)
    except KeyboardInterrupt:
        print('Registry shutting down')


def read_registry(registry_file: str) -> Dict[str, Dict[str, Any]]:
    try:
        with open(registry_file, 'r') as f:
            return json.load(f)
    except Exception:
        return {}


def cmd_list(args):
    registry = read_registry(args.registry_file)
    if not registry:
        print('No servants registered')
        return
    for k, v in registry.items():
        last = v.get('last_seen')
        ts = time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(last)) if last else 'unknown'
        print(f"{k}  token={v.get('token')}  last_seen={ts}")


def cmd_send(args):
    # If an IP is provided (host or host:port), prefer registry lookup
    host = args.host
    port = args.port

    if args.ip:
        registry = read_registry(args.registry_file)
        # ip can be 'host' or 'host:port'
        if ':' in args.ip:
            key = args.ip
        else:
            # find first entry with matching host
            key = None
            for k, v in registry.items():
                if v.get('host') == args.ip:
                    key = k
                    break
        if key and key in registry:
            host = registry[key].get('host')
            port = registry[key].get('port')
        else:
            print('Specified IP not found in registry; falling back to provided host/port')

    if not host or not port:
        print('Host and port must be specified (via registry or --host/--port)')
        return

    send_command(host, int(port), args.token, args.action, args.count)


def cmd_send_all(args):
    registry = read_registry(args.registry_file)
    if not registry:
        print('No servants registered')
        return
    for k, v in registry.items():
        host = v.get('host')
        port = v.get('port')
        print(f"Sending to {k}...")
        send_command(host, int(port), args.token, args.action, args.count)


def parse_args():
    parser = argparse.ArgumentParser(description='Master client to trigger servant')
    sub = parser.add_subparsers(dest='cmd', required=True)

    # serve command: run registry server
    pserve = sub.add_parser('serve', help='Run registry UDP server to collect servant announcements')
    pserve.add_argument('--listen-host', default=DEFAULT_HOST)
    pserve.add_argument('--listen-port', default=DEFAULT_REGISTRY_LISTEN_PORT, type=int)
    pserve.add_argument('--registry-file', default=DEFAULT_REGISTRY_FILE)

    # list command
    plist = sub.add_parser('list', help='List known servants from registry file')
    plist.add_argument('--registry-file', default=DEFAULT_REGISTRY_FILE)

    # send command
    psend = sub.add_parser('send', help='Send command to one servant')
    psend.add_argument('--ip', help='IP or host of servant (optionally host:port) to lookup in registry')
    psend.add_argument('--host', default=DEFAULT_HOST, help='Direct host to send to (if not using --ip)')
    psend.add_argument('--port', default=DEFAULT_PORT, type=int, help='Direct port to send to (if not using --ip)')
    psend.add_argument('--token', default=DEFAULT_TOKEN, help='Pre-shared token')
    psend.add_argument('--action', default='run', help='Action to send (default: run)')
    psend.add_argument('--count', default=100, type=int, help='Number of threads')
    psend.add_argument('--registry-file', default=DEFAULT_REGISTRY_FILE)

    # send-all command
    pall = sub.add_parser('send-all', help='Send command to all known servants in registry')
    pall.add_argument('--token', default=DEFAULT_TOKEN, help='Pre-shared token')
    pall.add_argument('--action', default='run', help='Action to send (default: run)')
    pall.add_argument('--count', default=100, type=int, help='Number of threads')
    pall.add_argument('--registry-file', default=DEFAULT_REGISTRY_FILE)

    return parser.parse_args()


def main():
    args = parse_args()
    if args.cmd == 'serve':
        serve_registry(args.listen_host, args.listen_port, args.registry_file)
    elif args.cmd == 'list':
        cmd_list(args)
    elif args.cmd == 'send':
        cmd_send(args)
    elif args.cmd == 'send-all':
        cmd_send_all(args)


if __name__ == '__main__':
    main()
