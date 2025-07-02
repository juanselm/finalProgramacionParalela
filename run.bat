@echo off
chcp 65001 >nul
REM Compresor de Archivos Paralelo - Scripts de ejecución

echo 🗂️ COMPRESOR DE ARCHIVOS PARALELO
echo ================================

:menu
echo.
echo Selecciona una opción:
echo [1] Ejecutar aplicación
echo [2] Ejecutar todas las pruebas (pytest)
echo [3] Ejecutar pruebas por HU
echo [4] Ver demos disponibles
echo [5] Limpiar archivos temporales
echo [6] Salir
echo.
set /p choice="Opción: "

if "%choice%"=="1" goto run_app
if "%choice%"=="2" goto test_all
if "%choice%"=="3" goto test_menu
if "%choice%"=="4" goto demo_menu
if "%choice%"=="5" goto cleanup
if "%choice%"=="6" goto exit

:run_app
echo.
echo 🚀 Iniciando aplicación...
python main.py
goto menu

:test_all
echo.
echo 🧪 Ejecutando todas las pruebas con pytest...
python -m pytest tests/ -v
echo.
pause
goto menu

:test_menu
echo.
echo Pruebas disponibles:
echo [1] HU01 - Interfaz gráfica
echo [2] HU02 - Configuración de hilos
echo [3] HU04 - Gestión de bloques
echo [4] HU05 - Almacenamiento temporal
echo [5] HU06 - Selección de archivos
echo [6] HU07 - Manejo de errores
echo [7] HU08 - Descompresión
echo [8] Volver al menú principal
echo.
set /p test_choice="Selecciona prueba: "

if "%test_choice%"=="1" python -m pytest tests/test_hu01.py -v
if "%test_choice%"=="2" python -m pytest tests/test_hu02.py -v
if "%test_choice%"=="3" python -m pytest tests/test_hu04.py -v
if "%test_choice%"=="4" python -m pytest tests/test_hu05.py -v
if "%test_choice%"=="5" python -m pytest tests/test_hu06.py -v
if "%test_choice%"=="6" python -m pytest tests/test_hu07.py -v
if "%test_choice%"=="7" python -m pytest tests/test_hu08.py -v
if "%test_choice%"=="8" goto menu

if not "%test_choice%"=="8" (
    echo.
    pause
)
goto menu

:demo_menu
echo.
echo Demos disponibles:
echo [1] Demo HU05 - Compresión paralela
echo [2] Demo HU06 - Selección de archivos
echo [3] Demo HU07 - Manejo de errores
echo [4] Demo HU08 - Descompresión
echo [5] Volver al menú principal
echo.
set /p demo_choice="Selecciona demo: "

if "%demo_choice%"=="1" python demo_hu05.py
if "%demo_choice%"=="2" python demo_hu06.py
if "%demo_choice%"=="3" python demo_hu07.py
if "%demo_choice%"=="4" python demo_hu08.py
if "%demo_choice%"=="5" goto menu

if not "%demo_choice%"=="5" (
    echo.
    pause
)
goto menu

:cleanup
echo.
echo 🧹 Limpiando archivos temporales...
if exist "*.pz" del /q "*.pz"
if exist "test_file*.txt" del /q "test_file*.txt"
if exist "__pycache__" rmdir /s /q "__pycache__"
if exist "src\__pycache__" rmdir /s /q "src\__pycache__"
if exist "src\compression\__pycache__" rmdir /s /q "src\compression\__pycache__"
if exist "src\gui\__pycache__" rmdir /s /q "src\gui\__pycache__"
if exist "tests\__pycache__" rmdir /s /q "tests\__pycache__"
if exist ".pytest_cache" rmdir /s /q ".pytest_cache"
if exist "logs" rmdir /s /q "logs"
echo ✅ Limpieza completada
echo.
pause
goto menu

:exit
echo.
echo ¡Hasta luego! 👋
pause
