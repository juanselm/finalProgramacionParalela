"""
Pruebas unitarias para la configuración de hilos
HU02: Configuración de número de hilos
"""

import unittest
import multiprocessing
import sys
import os

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from gui.main_window import MainWindow


class TestThreadConfiguration(unittest.TestCase):
    """Pruebas para la configuración de hilos (HU02)"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.app = MainWindow()
        self.max_threads = multiprocessing.cpu_count()
    
    def test_initial_thread_configuration(self):
        """Prueba la configuración inicial de hilos"""
        # El valor inicial debe ser 4 o el máximo de núcleos si es menor
        expected_initial = min(4, self.max_threads)
        self.assertEqual(self.app.num_threads.get(), expected_initial)
        self.assertEqual(self.app.max_threads, self.max_threads)
    
    def test_thread_validation_valid_range(self):
        """Prueba validación con valores válidos"""
        # Probar valores válidos
        for valid_value in ["1", "2", str(self.max_threads)]:
            result = self.app.validate_thread_input(valid_value)
            self.assertTrue(result, f"Debería validar el valor {valid_value}")
    
    def test_thread_validation_invalid_range(self):
        """Prueba validación con valores inválidos"""
        # Probar valores inválidos
        invalid_values = [str(self.max_threads + 1), str(self.max_threads + 10), "0", "-1"]
        for invalid_value in invalid_values:
            result = self.app.validate_thread_input(invalid_value)
            self.assertFalse(result, f"No debería validar el valor {invalid_value}")
    
    def test_thread_validation_non_numeric(self):
        """Prueba validación con valores no numéricos"""
        non_numeric_values = ["abc", "1.5", "two", ""]
        for value in non_numeric_values:
            if value == "":  # Valor vacío es válido
                result = self.app.validate_thread_input(value)
                self.assertTrue(result)
            else:
                result = self.app.validate_thread_input(value)
                self.assertFalse(result, f"No debería validar el valor no numérico {value}")
    
    def test_thread_display_update(self):
        """Prueba la actualización del display de hilos"""
        # Cambiar el número de hilos y verificar que se actualice
        test_values = [1, 2, self.max_threads]
        for test_value in test_values:
            if test_value <= self.max_threads:
                self.app.num_threads.set(test_value)
                self.app.update_thread_display()
                self.assertEqual(self.app.thread_value_label.cget("text"), str(test_value))
    
    def test_compression_config_retrieval(self):
        """Prueba la obtención de configuración de compresión"""
        # Configurar un valor específico
        test_threads = min(3, self.max_threads)
        self.app.num_threads.set(test_threads)
        
        config = self.app.get_compression_config()
        
        self.assertEqual(config['threads'], test_threads)
        self.assertEqual(config['max_threads'], self.max_threads)
        self.assertIsInstance(config['file_info'], dict)
    
    def test_performance_label_updates(self):
        """Prueba que las etiquetas de rendimiento se actualicen correctamente"""
        # Probar diferentes valores y verificar que generen mensajes apropiados
        test_cases = [
            (1, "secuencial"),  # Modo secuencial
            (min(2, self.max_threads), "conservadora"),  # Configuración conservadora
            (self.max_threads, "rendimiento")  # Máximo rendimiento
        ]
        
        for threads, expected_keyword in test_cases:
            if threads <= self.max_threads:
                self.app.num_threads.set(threads)
                self.app.update_thread_display()
                performance_text = self.app.performance_label.cget("text").lower()
                self.assertIn(expected_keyword, performance_text)


class TestThreadConfigurationIntegration(unittest.TestCase):
    """Pruebas de integración para HU02"""
    
    def setUp(self):
        """Configuración inicial"""
        self.app = MainWindow()
    
    def test_thread_config_with_file_selection(self):
        """Prueba que la configuración de hilos funcione con selección de archivo"""
        # Simular selección de archivo
        import tempfile
        from pathlib import Path
        
        # Crear archivo temporal
        temp_file = Path(tempfile.mktemp(suffix=".txt"))
        temp_file.write_text("Contenido de prueba para compresión")
        
        try:
            # Simular validación y configuración
            if self.app.validate_file(str(temp_file)):
                self.app.selected_file_path.set(str(temp_file))
                self.app.display_file_info(str(temp_file))
                
                # Configurar hilos
                test_threads = min(2, self.app.max_threads)
                self.app.num_threads.set(test_threads)
                
                # Obtener configuración completa
                config = self.app.get_compression_config()
                
                # Verificar que toda la configuración esté presente
                self.assertEqual(config['threads'], test_threads)
                self.assertIsNotNone(config['file_info'])
                self.assertIn('name', config['file_info'])
                
        finally:
            # Limpiar archivo temporal
            if temp_file.exists():
                temp_file.unlink()


if __name__ == "__main__":
    print("🧪 Ejecutando pruebas para HU02...")
    print(f"💻 Sistema con {multiprocessing.cpu_count()} núcleos detectados")
    unittest.main(verbosity=2)
