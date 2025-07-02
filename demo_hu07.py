"""
Demo para HU07: Sistema centralizado de manejo de errores
Demuestra las capacidades de manejo de errores de la aplicación
"""

import sys
import os
import tempfile
import threading
import time

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gui.error_handler import ErrorHandler, ErrorType, ErrorSeverity, handle_error
from compression.parallel_compressor import ParallelCompressor


def demo_error_types():
    """Demuestra diferentes tipos de errores y su manejo"""
    print("🔥 === DEMO HU07: MANEJO CENTRALIZADO DE ERRORES ===")
    print()
    
    # Crear error handler sin GUI para demo
    error_handler = ErrorHandler(parent_window=None, enable_logging=True)
    
    print("1️⃣ Probando diferentes tipos de errores:")
    print("-" * 50)
    
    # Simular errores de diferentes tipos
    error_scenarios = [
        (FileNotFoundError("Archivo no encontrado"), ErrorType.FILE_READ, "Lectura de archivo inexistente"),
        (PermissionError("Sin permisos de escritura"), ErrorType.FILE_WRITE, "Escritura sin permisos"),
        (ValueError("Datos corruptos"), ErrorType.COMPRESSION, "Compresión de datos inválidos"),
        (MemoryError("Memoria insuficiente"), ErrorType.MEMORY, "Procesamiento de archivo grande"),
        (Exception("Error desconocido"), ErrorType.UNKNOWN, "Operación inesperada")
    ]
    
    for i, (error, error_type, context) in enumerate(error_scenarios, 1):
        print(f"   {i}. {error_type.value}: {context}")
        error_info = error_handler.handle_error(
            error=error,
            error_type=error_type,
            severity=ErrorSeverity.ERROR,
            context=context,
            show_dialog=False  # No mostrar diálogos en demo
        )
        print(f"      → Mensaje usuario: {error_info['user_message'][:60]}...")
        print()
    
    return error_handler


def demo_error_severity():
    """Demuestra diferentes niveles de severidad"""
    print("2️⃣ Probando diferentes niveles de severidad:")
    print("-" * 50)
    
    error_handler = ErrorHandler(parent_window=None, enable_logging=False)
    
    severity_scenarios = [
        (ErrorSeverity.INFO, "Información general"),
        (ErrorSeverity.WARNING, "Advertencia menor"),
        (ErrorSeverity.ERROR, "Error estándar"),
        (ErrorSeverity.CRITICAL, "Error crítico del sistema")
    ]
    
    for severity, description in severity_scenarios:
        test_error = Exception(f"Error de prueba: {description}")
        error_info = error_handler.handle_error(
            error=test_error,
            error_type=ErrorType.VALIDATION,
            severity=severity,
            context=description,
            show_dialog=False
        )
        print(f"   {severity.value.upper()}: {description}")
        print(f"      → Timestamp: {error_info['timestamp'].strftime('%H:%M:%S')}")
        print()


def demo_compressor_integration():
    """Demuestra la integración del error handler con el compresor"""
    print("3️⃣ Probando integración con compresor paralelo:")
    print("-" * 50)
    
    # Crear error handler
    error_handler = ErrorHandler(parent_window=None, enable_logging=False)
    
    # Crear compresor con error handler
    compressor = ParallelCompressor(error_handler=error_handler)
    
    print("   ✅ Compresor creado con error handler integrado")
    
    # Crear directorio temporal
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Intentar comprimir archivo inexistente
        non_existent_file = os.path.join(temp_dir, "archivo_inexistente.txt")
        output_file = os.path.join(temp_dir, "output.pz")
        
        print(f"   🔍 Intentando comprimir archivo inexistente: {os.path.basename(non_existent_file)}")
        
        try:
            compressor.compress_file_with_threads(
                non_existent_file,
                output_file,
                num_threads=2,
                progress_callback=None
            )
        except Exception as e:
            print(f"   ❌ Error capturado: {type(e).__name__}")
        
        # Mostrar errores registrados
        history = error_handler.get_error_history()
        if history:
            print(f"   📊 Errores registrados: {len(history)}")
            for i, error_info in enumerate(history[-2:], 1):  # Mostrar últimos 2
                print(f"      {i}. {error_info['type'].value}: {error_info['context']}")
        
    finally:
        # Limpiar directorio temporal
        import shutil
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
    
    print()


def demo_error_callbacks():
    """Demuestra el sistema de callbacks para notificaciones"""
    print("4️⃣ Probando sistema de callbacks:")
    print("-" * 50)
    
    error_handler = ErrorHandler(parent_window=None, enable_logging=False)
    
    # Contador de notificaciones
    notifications = []
    
    def error_callback(error_info):
        notifications.append({
            'type': error_info['type'].value,
            'severity': error_info['severity'].value,
            'time': error_info['timestamp'].strftime('%H:%M:%S')
        })
        print(f"   🔔 Notificación: {error_info['type'].value} [{error_info['severity'].value}]")
    
    # Registrar callback
    error_handler.register_callback(error_callback)
    
    print("   ✅ Callback registrado")
    
    # Generar algunos errores
    test_errors = [
        (ValueError("Error 1"), ErrorType.VALIDATION),
        (IOError("Error 2"), ErrorType.FILE_READ),
        (RuntimeError("Error 3"), ErrorType.COMPRESSION)
    ]
    
    for error, error_type in test_errors:
        error_handler.handle_error(error, error_type, show_dialog=False)
        time.sleep(0.1)  # Pequeña pausa para mostrar orden
    
    print(f"   📊 Total de notificaciones recibidas: {len(notifications)}")
    print()


def demo_error_history():
    """Demuestra la gestión del historial de errores"""
    print("5️⃣ Probando gestión de historial:")
    print("-" * 50)
    
    error_handler = ErrorHandler(parent_window=None, enable_logging=False)
    
    # Generar historial de errores
    for i in range(5):
        error = Exception(f"Error histórico {i+1}")
        error_handler.handle_error(
            error,
            ErrorType.COMPRESSION,
            severity=ErrorSeverity.ERROR,
            context=f"Operación {i+1}",
            show_dialog=False
        )
    
    history = error_handler.get_error_history()
    print(f"   📚 Errores en historial: {len(history)}")
    
    # Mostrar resumen por tipo
    error_types = {}
    for error_info in history:
        error_type = error_info['type'].value
        error_types[error_type] = error_types.get(error_type, 0) + 1
    
    print("   📈 Resumen por tipo:")
    for error_type, count in error_types.items():
        print(f"      • {error_type}: {count}")
    
    # Limpiar historial
    error_handler.clear_history()
    print(f"   🧹 Historial limpiado. Errores restantes: {len(error_handler.get_error_history())}")
    print()


def demo_logging_functionality():
    """Demuestra la funcionalidad de logging"""
    print("6️⃣ Probando funcionalidad de logging:")
    print("-" * 50)
    
    # Crear error handler con logging habilitado
    error_handler = ErrorHandler(parent_window=None, enable_logging=True)
    
    print("   ✅ Error handler con logging habilitado")
    
    # Generar errores que serán loggeados
    log_errors = [
        (ValueError("Error crítico de validación"), ErrorType.VALIDATION, ErrorSeverity.CRITICAL),
        (IOError("Error de lectura"), ErrorType.FILE_READ, ErrorSeverity.ERROR),
        (RuntimeWarning("Advertencia de rendimiento"), ErrorType.COMPRESSION, ErrorSeverity.WARNING)
    ]
    
    for error, error_type, severity in log_errors:
        error_handler.handle_error(
            error,
            error_type,
            severity,
            context="Demo de logging",
            show_dialog=False
        )
        print(f"   📝 Logged: {severity.value.upper()} - {error_type.value}")
    
    # Verificar si existe directorio de logs
    log_dir = "logs"
    if os.path.exists(log_dir):
        log_files = [f for f in os.listdir(log_dir) if f.endswith('.log')]
        if log_files:
            print(f"   📁 Archivos de log creados: {len(log_files)}")
            latest_log = max(log_files)
            print(f"   📄 Último archivo de log: {latest_log}")
        else:
            print("   ⚠️ No se encontraron archivos de log")
    else:
        print("   ⚠️ Directorio de logs no encontrado")
    
    print()


def main():
    """Función principal del demo"""
    print("🚀 Iniciando Demo HU07 - Sistema Centralizado de Manejo de Errores")
    print("=" * 70)
    print()
    
    try:
        # Ejecutar todas las demostraciones
        error_handler = demo_error_types()
        demo_error_severity()
        demo_compressor_integration()
        demo_error_callbacks()
        demo_error_history()
        demo_logging_functionality()
        
        print("🎉 RESUMEN FINAL:")
        print("-" * 50)
        print("✅ Manejo de diferentes tipos de errores")
        print("✅ Soporte para múltiples niveles de severidad")
        print("✅ Integración con compresor paralelo")
        print("✅ Sistema de callbacks para notificaciones")
        print("✅ Gestión completa de historial de errores")
        print("✅ Funcionalidad de logging a archivos")
        print()
        print("🏆 HU07 COMPLETADA: Sistema centralizado de manejo de errores implementado exitosamente")
        
    except Exception as e:
        print(f"❌ Error en demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
