@echo off
title Transparenta
cd /d "%~dp0"
set PY=python
where python >nul 2>&1 || set PY=py

if exist "BASE DE DATOS\transparenta.db" goto iniciar
echo Creando la base de datos por primera vez...
cd "BASE DE DATOS"
%PY% crear_bd.py
cd ..

:iniciar
echo.
echo Iniciando Transparenta. Se abrira en tu navegador en unos segundos.
echo Para cerrar el programa, cierra esta ventana o presiona Ctrl + C.
echo.
start "" cmd /c "timeout /t 3 >nul && start http://127.0.0.1:5000"
cd APLICACION
%PY% app.py
pause
