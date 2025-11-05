@echo off
REM Instalador MW_SEGURO Client - Wrapper BAT
REM Click derecho -> "Ejecutar como administrador"

echo.
echo Iniciando instalador de MW_SEGURO Client...
echo.

REM Verificar si se está ejecutando como administrador
net session >nul 2>&1
if %errorLevel% neq 0 (
    echo ERROR: Este script debe ejecutarse como Administrador
    echo.
    echo Haz click derecho sobre este archivo y selecciona:
    echo "Ejecutar como administrador"
    echo.
    pause
    exit /b 1
)

REM Ejecutar el script PowerShell
powershell.exe -ExecutionPolicy Bypass -File "%~dp0install_windows_client.ps1"

exit /b %errorLevel%
