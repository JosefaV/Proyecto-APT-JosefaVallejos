@echo off
title Transparenta - Reiniciar datos
cd /d "%~dp0"
set PY=python
where python >nul 2>&1 || set PY=py
echo Se restauraran los datos de demostracion con la fecha de hoy.
echo Las decisiones hechas durante pruebas anteriores se borraran.
pause
if exist "Base de Datos\transparenta.db" del "Base de Datos\transparenta.db"
cd "Base de Datos"
%PY% crear_bd.py
cd ..
echo.
echo Listo. Ahora abre "Iniciar Transparenta".
pause
