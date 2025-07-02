"""
Pruebas unitarias para la validación de archivos
HU01: Selección de archivo mediante interfaz gráfica
"""

import unittest
import tempfile
import os
from pathlib import Path
import sys

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from gui.main_window import MainWindow


class TestFileValidation(unittest.TestCase):
    """Pruebas para la validación de archivos"""
    
    def setUp(self):
        """Configuración inicial para las pruebas"""
        self.app = MainWindow()
        self.temp_dir = tempfile.mkdtemp()
    
    def tearDown(self):
        """Limpieza después de las pruebas"""
        # Limpiar archivos temporales
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_validate_existing_file(self):
        """Prueba validación de archivo existente"""
        # Crear archivo temporal
        temp_file = Path(self.temp_dir) / "test_file.txt"
        temp_file.write_text("Contenido de prueba")
        
        # Validar archivo
        result = self.app.validate_file(str(temp_file))
        self.assertTrue(result, "Debería validar archivo existente")
    
    def test_validate_nonexistent_file(self):
        """Prueba validación de archivo inexistente"""
        nonexistent_file = Path(self.temp_dir) / "no_existe.txt"
        
        result = self.app.validate_file(str(nonexistent_file))
        self.assertFalse(result, "No debería validar archivo inexistente")
    
    def test_validate_empty_file(self):
        """Prueba validación de archivo vacío"""
        # Crear archivo vacío
        empty_file = Path(self.temp_dir) / "empty_file.txt"
        empty_file.touch()
        
        result = self.app.validate_file(str(empty_file))
        self.assertFalse(result, "No debería validar archivo vacío")
    
    def test_format_file_size(self):
        """Prueba formateo de tamaño de archivo"""
        # Prueba diferentes tamaños
        self.assertEqual(self.app.format_file_size(0), "0 B")
        self.assertEqual(self.app.format_file_size(512), "512.00 B")
        self.assertEqual(self.app.format_file_size(1024), "1.00 KB")
        self.assertEqual(self.app.format_file_size(1048576), "1.00 MB")
        self.assertEqual(self.app.format_file_size(1073741824), "1.00 GB")


if __name__ == "__main__":
    print("🧪 Ejecutando pruebas para HU01...")
    unittest.main(verbosity=2)
