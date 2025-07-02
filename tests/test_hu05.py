"""
Pruebas unitarias para HU05: Almacenamiento temporal y ensamblaje de bloques comprimidos
Como desarrollador, quiero que cada hilo comprima un bloque y lo almacene temporalmente 
para luego ensamblar el archivo final.
"""

import unittest
import tempfile
import os
import sys
import json
import zlib
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'src')))

from compression.parallel_compressor import ParallelCompressor
from compression.temporary_storage import TemporaryBlockStorage, CompressionAlgorithm


class TestHU05TemporaryStorage(unittest.TestCase):
    """Pruebas para el almacenamiento temporal de bloques comprimidos"""

    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.temp_dir = tempfile.mkdtemp()
        self.storage = TemporaryBlockStorage(self.temp_dir)

    def tearDown(self):
        """Limpieza después de cada prueba"""
        self.storage.cleanup()

    def test_store_and_retrieve_compressed_block(self):
        """HU05: Verifica que los bloques comprimidos se almacenan y recuperan correctamente"""
        block_id = 0
        test_data = b"Este es un bloque de prueba para comprimir"
        compressed_data = zlib.compress(test_data)
        
        # Almacenar bloque
        block_path = self.storage.store_compressed_block(
            block_id, compressed_data, len(test_data), 75.0, 1, "checksum123"
        )
        
        # Verificar que se almacenó
        self.assertTrue(os.path.exists(block_path))
        
        # Recuperar datos del bloque
        retrieved_data = self.storage.retrieve_block_data(block_id)
        self.assertEqual(retrieved_data, compressed_data)

    def test_ordered_blocks_metadata(self):
        """HU05: Verifica que los metadatos de bloques se mantienen en orden"""
        # Almacenar bloques en orden no secuencial
        blocks_data = [
            (2, b"bloque2", 50.0),
            (0, b"bloque0", 60.0),
            (1, b"bloque1", 55.0)
        ]
        
        for block_id, data, ratio in blocks_data:
            self.storage.store_compressed_block(
                block_id, data, len(data), ratio, 1, f"checksum{block_id}"
            )
        
        # Obtener metadatos ordenados
        ordered_metadata = self.storage.get_ordered_blocks_metadata()
        
        # Verificar que están en orden correcto (0, 1, 2)
        self.assertEqual(len(ordered_metadata), 3)
        self.assertEqual(ordered_metadata[0]['id'], 0)
        self.assertEqual(ordered_metadata[1]['id'], 1)
        self.assertEqual(ordered_metadata[2]['id'], 2)

    def test_file_info_storage(self):
        """HU05: Verifica que la información del archivo se almacena correctamente"""
        input_file = "test_input.txt"
        output_file = "test_output.parzip"
        total_blocks = 5
        
        self.storage.set_file_info(input_file, output_file, total_blocks)
        file_info = self.storage.get_file_info()
        
        self.assertEqual(file_info['input_file'], input_file)
        self.assertEqual(file_info['output_file'], output_file)
        self.assertEqual(file_info['total_blocks'], total_blocks)


class TestHU05ParallelCompression(unittest.TestCase):
    """Pruebas para la compresión paralela con almacenamiento temporal"""

    def setUp(self):
        """Configuración inicial para cada prueba"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, "test_file.txt")
        self.compressed_file = os.path.join(self.temp_dir, "compressed.parzip")
        self.compressor = ParallelCompressor(block_size=65536)  # 64KB mínimo

    def tearDown(self):
        """Limpieza después de cada prueba"""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.compressed_file):
            os.remove(self.compressed_file)
        try:
            os.rmdir(self.temp_dir)
        except:
            pass

    def create_test_file(self, size_bytes):
        """Crea un archivo de prueba con el tamaño especificado"""
        with open(self.test_file, 'wb') as f:
            # Crear contenido variado para mejor compresión
            pattern = b"ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789" * (size_bytes // 36 + 1)
            f.write(pattern[:size_bytes])
        return self.test_file

    def test_compression_with_zlib(self):
        """HU05: Verifica compresión paralela usando zlib"""
        # Crear archivo de prueba de 200KB para generar múltiples bloques
        test_file = self.create_test_file(200 * 1024)
        
        # Configurar algoritmo zlib
        self.compressor.set_compression_algorithm(CompressionAlgorithm.ZLIB)
        
        # Comprimir archivo
        success = self.compressor.compress_file(test_file, self.compressed_file)
        
        # Verificar que se completó exitosamente
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.compressed_file))
        
        # Verificar que el archivo comprimido contiene encabezado con metadatos
        with open(self.compressed_file, 'rb') as f:
            # Leer tamaño del encabezado
            header_size = int.from_bytes(f.read(4), byteorder='little')
            self.assertGreater(header_size, 0)
            
            # Leer y parsear encabezado JSON
            header_data = f.read(header_size)
            header_info = json.loads(header_data.decode('utf-8'))
            
            # Verificar estructura del encabezado
            self.assertEqual(header_info['format'], 'PARZIP_V1')
            self.assertGreater(header_info['total_blocks'], 0)
            self.assertEqual(header_info['compression_algorithm'], 'zlib')
            self.assertIsInstance(header_info['block_order'], list)

    def test_compression_with_rle(self):
        """HU05: Verifica compresión paralela usando RLE"""
        # Crear archivo con patrón repetitivo para RLE (200KB)
        with open(self.test_file, 'wb') as f:
            f.write(b'A' * 80000 + b'B' * 80000 + b'C' * 80000)
        
        # Configurar algoritmo RLE
        self.compressor.set_compression_algorithm(CompressionAlgorithm.RLE)
        
        # Comprimir archivo
        success = self.compressor.compress_file(self.test_file, self.compressed_file)
        
        # Verificar que se completó exitosamente
        self.assertTrue(success)
        self.assertTrue(os.path.exists(self.compressed_file))

    def test_block_order_preservation(self):
        """HU05: Verifica que los bloques se ensamblan en el orden correcto"""
        # Crear archivo con patrón identificable (300KB)
        test_content = b""
        for i in range(10):
            # Cada bloque tendrá un patrón único (30KB por bloque aprox)
            block_content = f"BLOQUE_{i:02d}_".encode() * 3000
            test_content += block_content
        
        with open(self.test_file, 'wb') as f:
            f.write(test_content)
        
        # Comprimir archivo
        success = self.compressor.compress_file(self.test_file, self.compressed_file)
        self.assertTrue(success)
        
        # Verificar que el archivo comprimido mantiene el orden
        with open(self.compressed_file, 'rb') as f:
            # Leer encabezado
            header_size = int.from_bytes(f.read(4), byteorder='little')
            header_data = f.read(header_size)
            header_info = json.loads(header_data.decode('utf-8'))
            
            # Verificar que el orden de bloques es secuencial
            block_order = header_info['block_order']
            expected_order = list(range(len(block_order)))
            self.assertEqual(block_order, expected_order)

    def test_temporary_storage_cleanup(self):
        """HU05: Verifica que el almacenamiento temporal se limpia después de la compresión"""
        test_file = self.create_test_file(128 * 1024)  # 128KB
        
        # Comprimir archivo
        success = self.compressor.compress_file(test_file, self.compressed_file)
        self.assertTrue(success)
        
        # Verificar que el almacenamiento temporal está limpio
        self.assertIsNone(self.compressor.temp_storage)

    def test_error_handling_with_cleanup(self):
        """HU05: Verifica que el almacenamiento temporal se limpia en caso de error"""
        # Intentar comprimir archivo inexistente
        non_existent_file = os.path.join(self.temp_dir, "no_existe.txt")
        
        with self.assertRaises(Exception):
            self.compressor.compress_file(non_existent_file, self.compressed_file)
        
        # Verificar que el almacenamiento temporal se limpió
        self.assertIsNone(self.compressor.temp_storage)


class TestHU05CompressionAlgorithms(unittest.TestCase):
    """Pruebas para los algoritmos de compresión implementados"""

    def setUp(self):
        self.compressor = ParallelCompressor()

    def test_rle_compression_decompression(self):
        """HU05: Verifica que RLE funciona correctamente"""
        test_data = b"AAABBBCCCDDDEEEFFFGGGHHHIIIJJJKKKLLLMMMNNNOOOPPPQQQRRRSSSTTTUUUVVVWWWXXXYYYZZZ"
        
        # Comprimir con RLE
        compressed = self.compressor._compress_rle(test_data)
        
        # Descomprimir
        decompressed = self.compressor._decompress_rle(compressed)
        
        # Verificar que son iguales
        self.assertEqual(decompressed, test_data)
        
        # Verificar que hay compresión (debe ser menor)
        self.assertLess(len(compressed), len(test_data))

    def test_rle_edge_cases(self):
        """HU05: Verifica casos edge de RLE"""
        # Datos vacíos
        self.assertEqual(self.compressor._compress_rle(b""), b"")
        self.assertEqual(self.compressor._decompress_rle(b""), b"")
        
        # Un solo byte
        self.assertEqual(self.compressor._decompress_rle(self.compressor._compress_rle(b"A")), b"A")
        
        # Bytes alternados (peor caso para RLE)
        alternating = b"ABABABABABABABAB"
        compressed = self.compressor._compress_rle(alternating)
        decompressed = self.compressor._decompress_rle(compressed)
        self.assertEqual(decompressed, alternating)


if __name__ == '__main__':
    unittest.main()
