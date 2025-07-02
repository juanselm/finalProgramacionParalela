"""
Tests para HU07: Sistema centralizado de manejo de errores
"""

import unittest
import tempfile
import os
import sys
import tkinter as tk
from unittest.mock import Mock, patch, MagicMock

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from gui.error_handler import ErrorHandler, ErrorType, ErrorSeverity, handle_error, error_handler
from compression.parallel_compressor import ParallelCompressor


class TestHU07ErrorHandling(unittest.TestCase):
    """Pruebas para el sistema centralizado de manejo de errores"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # Mock de ventana para evitar problemas con GUI en tests
        self.mock_root = Mock()
        self.error_handler = ErrorHandler(self.mock_root, enable_logging=False)
        
        # Crear directorio temporal para pruebas
        self.temp_dir = tempfile.mkdtemp()
        
    def tearDown(self):
        """Limpieza después de cada test"""
        # Limpiar directorio temporal
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_error_handler_creation(self):
        """HU07: Test de creación del error handler"""
        handler = ErrorHandler(enable_logging=False)
        self.assertIsNotNone(handler)
        self.assertEqual(len(handler.error_history), 0)
        self.assertEqual(len(handler.error_callbacks), 0)
    
    def test_handle_different_error_types(self):
        """HU07: Test de manejo de diferentes tipos de errores"""
        test_error = Exception("Error de prueba")
        
        # Test para cada tipo de error
        error_types = [
            ErrorType.FILE_READ,
            ErrorType.FILE_WRITE,
            ErrorType.COMPRESSION,
            ErrorType.PERMISSION,
            ErrorType.VALIDATION
        ]
        
        for error_type in error_types:
            with self.subTest(error_type=error_type):
                error_info = self.error_handler.handle_error(
                    test_error, 
                    error_type, 
                    ErrorSeverity.ERROR,
                    f"Test context for {error_type.value}",
                    show_dialog=False
                )
                
                self.assertEqual(error_info['type'], error_type)
                self.assertEqual(error_info['exception'], test_error)
                # Verificar que el mensaje contiene palabras clave del tipo de error
                message_lower = error_info['user_message'].lower()
                if error_type == ErrorType.FILE_READ:
                    self.assertIn('leer', message_lower)
                elif error_type == ErrorType.FILE_WRITE:
                    self.assertIn('escribir', message_lower)
                elif error_type == ErrorType.COMPRESSION:
                    self.assertIn('compresión', message_lower)
                elif error_type == ErrorType.PERMISSION:
                    self.assertIn('permisos', message_lower)
                elif error_type == ErrorType.VALIDATION:
                    self.assertIn('válid', message_lower)
    
    def test_error_severity_levels(self):
        """HU07: Test de diferentes niveles de severidad"""
        test_error = Exception("Error de prueba")
        
        severity_levels = [
            ErrorSeverity.INFO,
            ErrorSeverity.WARNING,
            ErrorSeverity.ERROR,
            ErrorSeverity.CRITICAL
        ]
        
        for severity in severity_levels:
            with self.subTest(severity=severity):
                error_info = self.error_handler.handle_error(
                    test_error,
                    ErrorType.UNKNOWN,
                    severity,
                    show_dialog=False
                )
                
                self.assertEqual(error_info['severity'], severity)
    
    def test_error_history_management(self):
        """HU07: Test de gestión del historial de errores"""
        # Generar varios errores
        for i in range(3):
            test_error = Exception(f"Error {i}")
            self.error_handler.handle_error(
                test_error,
                ErrorType.COMPRESSION,
                show_dialog=False
            )
        
        # Verificar historial
        history = self.error_handler.get_error_history()
        self.assertEqual(len(history), 3)
        
        # Verificar orden cronológico
        for i, error_info in enumerate(history):
            self.assertIn(f"Error {i}", error_info['message'])
        
        # Limpiar historial
        self.error_handler.clear_history()
        self.assertEqual(len(self.error_handler.get_error_history()), 0)
    
    def test_error_callbacks(self):
        """HU07: Test de callbacks de notificación de errores"""
        callback_called = []
        
        def test_callback(error_info):
            callback_called.append(error_info)
        
        # Registrar callback
        self.error_handler.register_callback(test_callback)
        
        # Generar error
        test_error = Exception("Error con callback")
        self.error_handler.handle_error(test_error, show_dialog=False)
        
        # Verificar que se llamó el callback
        self.assertEqual(len(callback_called), 1)
        self.assertEqual(callback_called[0]['message'], "Error con callback")
        
        # Remover callback
        self.error_handler.remove_callback(test_callback)
        
        # Generar otro error
        self.error_handler.handle_error(Exception("Error sin callback"), show_dialog=False)
        
        # Verificar que no se llamó el callback
        self.assertEqual(len(callback_called), 1)
    
    @patch('tkinter.messagebox.showerror')
    def test_error_dialog_display(self, mock_messagebox):
        """HU07: Test de visualización de diálogos de error"""
        test_error = Exception("Error para diálogo")
        
        # Generar error con diálogo
        self.error_handler.handle_error(
            test_error,
            ErrorType.FILE_READ,
            ErrorSeverity.ERROR,
            "Test context",
            show_dialog=True
        )
        
        # Verificar que se llamó messagebox
        mock_messagebox.assert_called_once()
        
        # Verificar argumentos del messagebox
        args, kwargs = mock_messagebox.call_args
        self.assertIn("Lectura de archivo", args[0])  # title
        self.assertIn("leer el archivo", args[1])     # message
    
    def test_global_error_handler_functions(self):
        """HU07: Test de funciones globales de manejo de errores"""
        from gui.error_handler import get_error_handler, set_error_handler
        
        # Configurar handler personalizado
        custom_handler = ErrorHandler(enable_logging=False)
        set_error_handler(custom_handler)
        
        # Verificar que se obtiene el handler correcto
        retrieved_handler = get_error_handler()
        self.assertEqual(retrieved_handler, custom_handler)
        
        # Test de función global handle_error
        test_error = Exception("Error global")
        error_info = handle_error(
            test_error,
            ErrorType.VALIDATION,
            show_dialog=False
        )
        
        self.assertEqual(error_info['type'], ErrorType.VALIDATION)
        self.assertEqual(len(custom_handler.get_error_history()), 1)
    
    def test_error_decorator(self):
        """HU07: Test del decorador de manejo de errores"""
        
        @error_handler(
            error_type=ErrorType.COMPRESSION,
            show_dialog=False
        )
        def function_that_fails():
            raise ValueError("Error en función decorada")
        
        @error_handler(
            error_type=ErrorType.VALIDATION,
            show_dialog=False
        )
        def function_that_succeeds():
            return "success"
        
        # Test función que falla
        result = function_that_fails()
        self.assertIsNone(result)  # El decorador debe retornar None en caso de error
        
        # Test función que tiene éxito
        result = function_that_succeeds()
        self.assertEqual(result, "success")
    
    def test_compressor_error_integration(self):
        """HU07: Test de integración del error handler con el compresor"""
        # Crear compresor con error handler
        compressor = ParallelCompressor(error_handler=self.error_handler)
        
        # Verificar que el error handler está configurado
        self.assertEqual(compressor.error_handler, self.error_handler)
        
        # Test de manejo de error en método _handle_error
        test_error = Exception("Error de compresión")
        compressor._handle_error(test_error, ErrorType.COMPRESSION, "Test context")
        
        # Verificar que el error se registró
        history = self.error_handler.get_error_history()
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]['type'], ErrorType.COMPRESSION)
        self.assertEqual(history[0]['context'], "Test context")
    
    def test_file_error_scenarios(self):
        """HU07: Test de escenarios de errores de archivo"""
        compressor = ParallelCompressor(error_handler=self.error_handler)
        
        # Test archivo inexistente
        non_existent_file = os.path.join(self.temp_dir, "no_existe.txt")
        output_file = os.path.join(self.temp_dir, "output.pz")
        
        try:
            compressor.compress_file_with_threads(
                non_existent_file,
                output_file,
                num_threads=2,
                progress_callback=None
            )
        except:
            pass  # Esperamos que falle
        
        # Verificar que se registraron errores
        history = self.error_handler.get_error_history()
        self.assertGreater(len(history), 0)
    
    def test_custom_user_messages(self):
        """HU07: Test de mensajes personalizados para el usuario"""
        test_error = Exception("Error técnico complejo")
        custom_message = "Mensaje amigable para el usuario"
        
        error_info = self.error_handler.handle_error(
            test_error,
            ErrorType.COMPRESSION,
            user_message=custom_message,
            show_dialog=False
        )
        
        self.assertEqual(error_info['user_message'], custom_message)
    
    def test_error_summary_functionality(self):
        """HU07: Test de funcionalidad de resumen de errores"""
        # Generar errores de diferentes tipos
        errors = [
            (ErrorType.FILE_READ, "Error lectura 1"),
            (ErrorType.FILE_READ, "Error lectura 2"),
            (ErrorType.COMPRESSION, "Error compresión"),
            (ErrorType.FILE_WRITE, "Error escritura")
        ]
        
        for error_type, message in errors:
            self.error_handler.handle_error(
                Exception(message),
                error_type,
                show_dialog=False
            )
        
        # Verificar que hay errores en el historial
        history = self.error_handler.get_error_history()
        self.assertEqual(len(history), 4)
        
        # El método show_error_summary debería funcionar sin errores
        # (no podemos testear el messagebox fácilmente, pero sí que no lance excepciones)
        try:
            with patch('tkinter.messagebox.showinfo'):
                self.error_handler.show_error_summary()
        except Exception as e:
            self.fail(f"show_error_summary falló: {e}")


if __name__ == '__main__':
    unittest.main()
