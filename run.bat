@echo off
REM Compresor de Archivos Paralelo - Scripts de ejecución

echo 🗂️ COMPRESOR DE ARCHIVOS PARALELO
echo ================================

:menu
echo.
echo Selecciona una opción:
echo [1] Ejecutar aplicación
echo [2] Ejecutar pruebas HU01
echo [3] Ejecutar pruebas HU02
echo [4] Ejecutar todas las pruebas
echo [5] Ver demostración
echo [6] Salir
echo.
set /p choice="Opción: "

if "%choice%"=="1" goto run_app
if "%choice%"=="2" goto test_hu01
if "%choice%"=="3" goto test_hu02
if "%choice%"=="4" goto test_all
if "%choice%"=="5" goto demo
if "%choice%"=="6" goto exit

:run_app
echo.
echo 🚀 Iniciando aplicación...
python main.py
goto menu

:test_hu01
echo.
echo 🧪 Ejecutando pruebas HU01...
python tests\test_hu01.py
goto menu

:test_hu02
echo.
echo 🧪 Ejecutando pruebas HU02...
python tests\test_hu02.py
goto menu

:test_all
echo.
echo 🧪 Ejecutando todas las pruebas...
python tests\test_hu01.py
python tests\test_hu02.py
goto menu

:demo
echo.
echo 📋 Mostrando demostración...
python demo.py
goto menu

:exit
echo.
echo ¡Hasta luego! 👋
pause
