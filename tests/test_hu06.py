"""
Pruebas unitarias para HU06: Selección personalizada de destino
Como usuario, quiero guardar el archivo comprimido en la ruta que yo elija.
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path
from unittest.mock import patch, MagicMock

# Agregar el directorio src al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from gui.main_window import MainWindow
from gui.progress_dialog import ProgressDialog


class TestHU06OutputSelection(unittest.TestCase):
    """Pruebas para la selección personalizada del archivo de destino"""

    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_input.txt")
        self.output_file = os.path.join(self.temp_dir, "test_output.pz")
        
        # Crear archivo de prueba
        with open(self.test_file, 'w') as f:
            f.write("Contenido de prueba para HU06")

    def tearDown(self):
        """Limpieza después de cada prueba"""
        try:
            if os.path.exists(self.test_file):
                os.remove(self.test_file)
            if os.path.exists(self.output_file):
                os.remove(self.output_file)
            os.rmdir(self.temp_dir)
        except:
            pass

    @patch('tkinter.filedialog.asksaveasfilename')
    @patch('tkinter.messagebox.showinfo')
    def test_select_output_file_valid_path(self, mock_showinfo, mock_saveas):
        """HU06: Verifica que se pueda seleccionar una ruta de destino válida"""
        # Configurar mocks
        mock_saveas.return_value = self.output_file
        
        # Crear instancia de la ventana principal (sin mostrar)
        app = MainWindow()
        app.file_info = {
            'path': self.test_file,
            'name': 'test_input.txt',
            'size': 100,
            'size_formatted': '100 B'
        }
        
        # Ejecutar selección de destino
        app.select_output_file()
        
        # Verificar que se configuró la ruta de destino
        self.assertEqual(app.output_file_path.get(), self.output_file)
        
        # Verificar que se mostró mensaje de confirmación
        mock_showinfo.assert_called_once()

    def test_validate_output_path_valid_directory(self):
        """HU06: Verifica la validación de permisos en directorio válido"""
        app = MainWindow()
        
        # Probar con directorio temporal (que debe tener permisos)
        valid_path = os.path.join(self.temp_dir, "valid_output.pz")
        result = app.validate_output_path(valid_path)
        
        self.assertTrue(result)

    def test_validate_output_path_nonexistent_directory(self):
        """HU06: Verifica que se cree directorio si no existe"""
        app = MainWindow()
        
        # Crear ruta con directorio inexistente
        new_dir = os.path.join(self.temp_dir, "new_subdir")
        output_path = os.path.join(new_dir, "output.pz")
        
        result = app.validate_output_path(output_path)
        
        # Debe ser True y el directorio debe haberse creado
        self.assertTrue(result)
        self.assertTrue(os.path.exists(new_dir))

    @patch('tkinter.messagebox.askyesno')
    def test_validate_output_path_existing_file(self, mock_askyesno):
        """HU06: Verifica confirmación de sobrescritura para archivo existente"""
        # Crear archivo existente
        with open(self.output_file, 'w') as f:
            f.write("archivo existente")
        
        # Configurar mock para aceptar sobrescritura
        mock_askyesno.return_value = True
        
        app = MainWindow()
        result = app.validate_output_path(self.output_file)
        
        # Debe confirmar sobrescritura y retornar True
        self.assertTrue(result)
        mock_askyesno.assert_called_once()

    def test_suggest_output_filename(self):
        """HU06: Verifica que se sugiera automáticamente un nombre de destino"""
        app = MainWindow()
        
        # Ejecutar sugerencia
        app.suggest_output_filename(self.test_file)
        
        # Verificar que se sugirió un nombre con extensión .pz
        suggested_path = app.output_file_path.get()
        self.assertTrue(suggested_path.endswith('.pz'))
        self.assertIn('test_input_comprimido', suggested_path)

    def test_extension_enforcement(self):
        """HU06: Verifica que se fuerce la extensión .pz"""
        app = MainWindow()
        app.file_info = {
            'path': self.test_file,
            'name': 'test_input.txt',
            'size': 100,
            'size_formatted': '100 B'
        }
        
        # Simular selección de archivo sin extensión .pz
        output_without_extension = os.path.join(self.temp_dir, "output_sin_extension")
        
        with patch('tkinter.filedialog.asksaveasfilename') as mock_saveas, \
             patch('tkinter.messagebox.showinfo'):
            
            mock_saveas.return_value = output_without_extension
            
            app.select_output_file()
            
            # Verificar que se agregó la extensión .pz
            final_path = app.output_file_path.get()
            self.assertTrue(final_path.endswith('.pz'))

    def test_compression_button_state_management(self):
        """HU06: Verifica que el botón de compresión se habilite solo cuando hay archivo y destino"""
        app = MainWindow()
        
        # Inicialmente debe estar deshabilitado
        self.assertEqual(str(app.compress_button['state']), 'disabled')
        
        # Configurar archivo pero sin destino
        app.file_info = {'path': self.test_file}
        app.update_compression_button_state()
        self.assertEqual(str(app.compress_button['state']), 'disabled')
        
        # Configurar destino también
        app.output_file_path.set(self.output_file)
        app.update_compression_button_state()
        self.assertEqual(str(app.compress_button['state']), 'normal')

    def test_clear_selection_clears_destination(self):
        """HU06: Verifica que limpiar selección también limpie el destino"""
        app = MainWindow()
        
        # Configurar archivo y destino
        app.file_info = {'path': self.test_file}
        app.output_file_path.set(self.output_file)
        
        # Limpiar selección
        app.clear_selection()
        
        # Verificar que se limpió todo
        self.assertEqual(app.output_file_path.get(), "")
        self.assertEqual(app.file_info, {})


class TestHU06ProgressDialog(unittest.TestCase):
    """Pruebas para el uso del destino personalizado en el diálogo de progreso"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.output_file = os.path.join(self.temp_dir, "custom_output.pz")

    def tearDown(self):
        try:
            if os.path.exists(self.output_file):
                os.remove(self.output_file)
            os.rmdir(self.temp_dir)
        except:
            pass

    def test_progress_dialog_uses_custom_output_path(self):
        """HU06: Verifica que el diálogo de progreso use la ruta personalizada"""
        config = {
            'file_info': {
                'name': 'test.txt',
                'size_formatted': '100 B'
            },
            'threads': 4,
            'output_path': self.output_file
        }
        
        # Crear diálogo sin mostrar
        with patch('tkinter.Toplevel'):
            dialog = ProgressDialog(None, config)
            
            # Verificar que usa la ruta personalizada
            output_filename = dialog.get_output_filename()
            self.assertEqual(output_filename, self.output_file)

    def test_progress_dialog_fallback_without_custom_path(self):
        """HU06: Verifica fallback cuando no hay ruta personalizada"""
        config = {
            'file_info': {
                'name': 'test.txt',
                'path': '/path/to/test.txt',
                'size_formatted': '100 B'
            },
            'threads': 4
            # Sin output_path
        }
        
        # Crear diálogo sin mostrar
        with patch('tkinter.Toplevel'):
            dialog = ProgressDialog(None, config)
            
            # Verificar que usa el comportamiento anterior
            output_filename = dialog.get_output_filename()
            self.assertEqual(output_filename, '/path/to/test.txt.parzip')


if __name__ == '__main__':
    # Configurar headless mode para tests de GUI
    import tkinter as tk
    root = tk.Tk()
    root.withdraw()  # Ocultar ventana principal
    
    try:
        unittest.main()
    finally:
        root.destroy()
