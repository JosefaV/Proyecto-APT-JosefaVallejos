@echo off
title Transparenta
cd /d "%~dp0"

set PY=python
where python >nul 2>&1 || set PY=py
%PY% --version >nul 2>&1
if errorlevel 1 (
  echo No se encontro Python. Instalalo desde python.org y marca "Add Python to PATH".
  pause
  exit /b 1
)

%PY% -c "import flask" >nul 2>&1
if errorlevel 1 (
  echo Instalando Flask por unica vez...
  %PY% -m pip install flask
  if errorlevel 1 (
    echo No se pudo instalar Flask. Revisa la conexion a internet.
    pause
    exit /b 1
  )
)

if not exist "Base de Datos\transparenta.db" (
  echo Creando la base de datos por primera vez...
  pushd "Base de Datos"
  %PY% crear_bd.py
  popd
)

echo.
echo Iniciando Transparenta. NO cierres esta ventana mientras uses el programa.
echo Si el navegador dice "no se puede acceder", espera unos segundos y recarga la pagina.
echo Para terminar, cierra esta ventana o presiona Ctrl + C.
echo.
start "" cmd /c "timeout /t 5 >nul && start http://127.0.0.1:5000"
cd Aplicacion
%PY% app.py
echo.
echo El programa se detuvo. Si ves un error arriba, sacale una captura.
pause
