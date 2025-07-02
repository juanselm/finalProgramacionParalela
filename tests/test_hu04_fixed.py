"""
Pruebas unitarias para HU04: División de archivos en bloques de tamaño fijo
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from compression.block_manager import FileBlockManager
from compression.parallel_compressor import ParallelCompressor


class TestFileBlockManager(unittest.TestCase):
    """Pruebas para la clase FileBlockManager"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_file.txt")
        
    def tearDown(self):
        """Limpieza después de cada prueba"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        os.rmdir(self.temp_dir)
    
    def create_test_file(self, size_bytes):
        """Crea un archivo de prueba con el tamaño especificado"""
        with open(self.test_file, 'wb') as f:
            f.write(b'A' * size_bytes)
        return self.test_file
    
    def test_default_block_size(self):
        """HU04: Verifica que el tamaño de bloque por defecto sea 1MB"""
        manager = FileBlockManager()
        expected_size = 1024 * 1024  # 1MB
        self.assertEqual(manager.block_size, expected_size)
    
    def test_custom_block_size(self):
        """HU04: Verifica que se pueda configurar un tamaño de bloque personalizado"""
        custom_size = 512 * 1024  # 512KB
        manager = FileBlockManager(custom_size)
        self.assertEqual(manager.block_size, custom_size)
    
    def test_block_size_validation_minimum(self):
        """HU04: Verifica que se valide el tamaño mínimo de bloque"""
        with self.assertRaises(ValueError):
            FileBlockManager(32 * 1024)  # Menor al mínimo de 64KB
    
    def test_block_size_validation_maximum(self):
        """HU04: Verifica que se valide el tamaño máximo de bloque"""
        with self.assertRaises(ValueError):
            FileBlockManager(32 * 1024 * 1024)  # Mayor al máximo de 16MB
    
    def test_block_size_validation_invalid_type(self):
        """HU04: Verifica que se valide el tipo de dato del tamaño de bloque"""
        with self.assertRaises(ValueError):
            FileBlockManager("invalid")
        with self.assertRaises(ValueError):
            FileBlockManager(-1000)
    
    def test_file_analysis(self):
        """HU04: Verifica que el análisis de archivo proporcione información correcta"""
        # Crear archivo de 2.5MB
        file_size = int(2.5 * 1024 * 1024)
        self.create_test_file(file_size)
        
        manager = FileBlockManager(1024 * 1024)  # 1MB blocks
        analysis = manager.analyze_file(self.test_file)
        
        self.assertEqual(analysis['file_size'], file_size)
        self.assertEqual(analysis['block_size'], 1024 * 1024)
        self.assertEqual(analysis['total_blocks'], 3)  # 1MB + 1MB + 0.5MB
        self.assertEqual(analysis['last_block_size'], int(0.5 * 1024 * 1024))
    
    def test_file_analysis_exact_multiple(self):
        """HU04: Verifica análisis cuando el archivo es múltiplo exacto del tamaño de bloque"""
        # Crear archivo de exactamente 2MB
        file_size = 2 * 1024 * 1024
        self.create_test_file(file_size)
        
        manager = FileBlockManager(1024 * 1024)  # 1MB blocks
        analysis = manager.analyze_file(self.test_file)
        
        self.assertEqual(analysis['total_blocks'], 2)
        self.assertEqual(analysis['last_block_size'], 1024 * 1024)  # Último bloque completo
    
    def test_split_file_into_blocks(self):
        """HU04: Verifica que la división en bloques sea correcta"""
        # Crear archivo de 2.5MB
        file_size = int(2.5 * 1024 * 1024)
        self.create_test_file(file_size)
        
        manager = FileBlockManager(1024 * 1024)  # 1MB blocks
        blocks = manager.split_file_into_blocks(self.test_file)
        
        # Verificar número de bloques
        self.assertEqual(len(blocks), 3)
        
        # Verificar tamaños de bloques
        self.assertEqual(blocks[0]['size'], 1024 * 1024)  # Primer bloque completo
        self.assertEqual(blocks[1]['size'], 1024 * 1024)  # Segundo bloque completo
        self.assertEqual(blocks[2]['size'], int(0.5 * 1024 * 1024))  # Último bloque parcial
        
        # Verificar continuidad de datos
        total_size = sum(block['size'] for block in blocks)
        self.assertEqual(total_size, file_size)
    
    def test_block_integrity_validation(self):
        """HU04: Verifica que se valide la integridad de la división"""
        # Crear archivo pequeño
        file_size = 150000  # 150KB
        self.create_test_file(file_size)
        
        manager = FileBlockManager(65536)  # 64KB blocks
        blocks = manager.split_file_into_blocks(self.test_file)
        
        # Verificar que los offsets sean continuos
        expected_offset = 0
        for block in blocks:
            self.assertEqual(block['start_offset'], expected_offset)
            expected_offset = block['end_offset'] + 1
        
        # Verificar que el último offset coincida con el tamaño del archivo
        self.assertEqual(blocks[-1]['end_offset'], file_size - 1)
    
    def test_block_distribution_for_threads(self):
        """HU04: Verifica que la distribución de bloques entre hilos sea equitativa"""
        # Crear archivo que genere 10 bloques
        file_size = 10 * 1024 * 1024  # 10MB
        self.create_test_file(file_size)
        
        manager = FileBlockManager(1024 * 1024)  # 1MB blocks
        blocks = manager.split_file_into_blocks(self.test_file)
        
        # Distribuir entre 3 hilos
        distribution = manager.get_block_distribution_for_threads(3)
        
        # Verificar que todos los bloques estén asignados
        all_assigned_blocks = []
        for thread_blocks in distribution:
            all_assigned_blocks.extend(thread_blocks)
        
        self.assertEqual(len(all_assigned_blocks), 10)
        self.assertEqual(set(all_assigned_blocks), set(range(10)))
        
        # Verificar distribución aproximadamente equitativa
        # Con 10 bloques y 3 hilos: debería ser [4, 3, 3] o similar
        thread_counts = [len(thread_blocks) for thread_blocks in distribution]
        self.assertTrue(max(thread_counts) - min(thread_counts) <= 1)
    
    def test_no_data_loss_or_duplication(self):
        """HU04: Verifica que no se pierdan ni dupliquen datos"""
        # Crear archivo con patrón conocido
        pattern = b'ABCDEFGHIJKLMNOPQRSTUVWXYZ' * 4000  # ~104KB
        
        with open(self.test_file, 'wb') as f:
            f.write(pattern)
        
        manager = FileBlockManager(65536)  # 64KB blocks
        blocks = manager.split_file_into_blocks(self.test_file)
        
        # Reconstruir datos a partir de bloques
        reconstructed_data = b''.join(block['data'] for block in blocks)
        
        # Verificar que los datos sean idénticos
        self.assertEqual(reconstructed_data, pattern)
        self.assertEqual(len(reconstructed_data), len(pattern))
    
    def test_empty_file_handling(self):
        """HU04: Verifica el manejo de archivos vacíos"""
        # Crear archivo vacío
        with open(self.test_file, 'wb') as f:
            pass  # Archivo vacío
        
        manager = FileBlockManager()
        
        # Debe lanzar excepción para archivo vacío
        with self.assertRaises(ValueError):
            manager.analyze_file(self.test_file)
    
    def test_nonexistent_file_handling(self):
        """HU04: Verifica el manejo de archivos inexistentes"""
        manager = FileBlockManager()
        
        with self.assertRaises(FileNotFoundError):
            manager.analyze_file("nonexistent_file.txt")
    
    def test_optimal_block_size_calculation(self):
        """HU04: Verifica el cálculo de tamaño de bloque óptimo"""
        # Archivo de 100MB con 4 hilos
        file_size = 100 * 1024 * 1024
        num_threads = 4
        
        optimal_size = FileBlockManager.calculate_optimal_block_size(file_size, num_threads)
        
        # Verificar que esté dentro de límites válidos
        self.assertGreaterEqual(optimal_size, FileBlockManager.MIN_BLOCK_SIZE)
        self.assertLessEqual(optimal_size, FileBlockManager.MAX_BLOCK_SIZE)
        
        # Verificar que genere aproximadamente 2 bloques por hilo (objetivo por defecto)
        expected_blocks = num_threads * 2
        actual_blocks = file_size // optimal_size
        
        # Debe estar cerca del objetivo (±50%)
        self.assertGreater(actual_blocks, expected_blocks * 0.5)
        self.assertLess(actual_blocks, expected_blocks * 2)


class TestParallelCompressorHU04(unittest.TestCase):
    """Pruebas para la integración de HU04 en ParallelCompressor"""
    
    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_file.txt")
        
    def tearDown(self):
        """Limpieza después de cada prueba"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        os.rmdir(self.temp_dir)
    
    def create_test_file(self, size_bytes):
        """Crea un archivo de prueba con el tamaño especificado"""
        with open(self.test_file, 'wb') as f:
            f.write(b'A' * size_bytes)
        return self.test_file
    
    def test_configurable_block_size(self):
        """HU04: Verifica que ParallelCompressor permita configurar el tamaño de bloque"""
        custom_size = 512 * 1024  # 512KB
        compressor = ParallelCompressor(custom_size)
        
        self.assertEqual(compressor.get_block_size(), custom_size)
    
    def test_set_block_size_after_creation(self):
        """HU04: Verifica que se pueda cambiar el tamaño de bloque después de crear el compresor"""
        compressor = ParallelCompressor()
        original_size = compressor.get_block_size()
        
        new_size = 256 * 1024  # 256KB
        compressor.set_block_size(new_size)
        
        self.assertNotEqual(compressor.get_block_size(), original_size)
        self.assertEqual(compressor.get_block_size(), new_size)
    
    def test_file_analysis_integration(self):
        """HU04: Verifica que el análisis de archivo funcione en ParallelCompressor"""
        # Crear archivo de prueba
        file_size = 2 * 1024 * 1024  # 2MB
        self.create_test_file(file_size)
        
        compressor = ParallelCompressor()
        analysis = compressor.analyze_file_for_compression(self.test_file)
        
        self.assertIn('file_size', analysis)
        self.assertIn('total_blocks', analysis)
        self.assertIn('block_size', analysis)
        self.assertEqual(analysis['file_size'], file_size)
    
    def test_optimal_block_size_suggestion(self):
        """HU04: Verifica que se puedan obtener sugerencias de tamaño de bloque óptimo"""
        # Crear archivo de prueba
        file_size = 10 * 1024 * 1024  # 10MB
        self.create_test_file(file_size)
        
        compressor = ParallelCompressor()
        suggestion = compressor.suggest_optimal_block_size(self.test_file, 4)
        
        self.assertIn('suggested_block_size', suggestion)
        self.assertIn('current_block_size', suggestion)
        self.assertIn('improvement_expected', suggestion)
        
        # Verificar que la sugerencia sea un tamaño válido
        suggested_size = suggestion['suggested_block_size']
        self.assertGreaterEqual(suggested_size, FileBlockManager.MIN_BLOCK_SIZE)
        self.assertLessEqual(suggested_size, FileBlockManager.MAX_BLOCK_SIZE)


if __name__ == '__main__':
    unittest.main(verbosity=2)
