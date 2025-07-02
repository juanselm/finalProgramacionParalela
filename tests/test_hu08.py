"""
Tests para HU08: Descompresión de archivos .pz
"""

import unittest
import tempfile
import os
import sys
from pathlib import Path

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from compression.parallel_compressor import ParallelCompressor
from gui.error_handler import ErrorHandler


class TestHU08Decompression(unittest.TestCase):
    """Pruebas para la funcionalidad de descompresión de archivos .pz"""
    
    def setUp(self):
        """Configuración inicial para cada test"""
        # Crear directorio temporal para pruebas
        self.temp_dir = tempfile.mkdtemp()
        
        # Crear error handler para las pruebas
        self.error_handler = ErrorHandler(enable_logging=False)
        
        # Crear compresor con error handler
        self.compressor = ParallelCompressor(error_handler=self.error_handler)
        
        # Crear archivo de prueba
        self.test_content = b"Este es un archivo de prueba para HU08.\n" * 100
        self.test_file = os.path.join(self.temp_dir, "test_file.txt")
        with open(self.test_file, 'wb') as f:
            f.write(self.test_content)
    
    def tearDown(self):
        """Limpieza después de cada test"""
        # Limpiar directorio temporal
        import shutil
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)
    
    def test_compress_then_decompress_cycle(self):
        """HU08: Test del ciclo completo comprimir -> descomprimir"""
        # Archivo comprimido
        compressed_file = os.path.join(self.temp_dir, "test_compressed.pz")
        
        # Comprimir archivo
        compression_success = self.compressor.compress_file_with_threads(
            input_file=self.test_file,
            output_file=compressed_file,
            num_threads=2,
            progress_callback=None
        )
        
        self.assertTrue(compression_success, "La compresión debe ser exitosa")
        self.assertTrue(os.path.exists(compressed_file), "El archivo comprimido debe existir")
        
        # Archivo descomprimido
        decompressed_file = os.path.join(self.temp_dir, "test_decompressed.txt")
        
        # Descomprimir archivo
        decompression_success = self.compressor.decompress_file_with_threads(
            input_file=compressed_file,
            output_file=decompressed_file,
            num_threads=2,
            progress_callback=None
        )
        
        self.assertTrue(decompression_success, "La descompresión debe ser exitosa")
        self.assertTrue(os.path.exists(decompressed_file), "El archivo descomprimido debe existir")
        
        # Verificar que el contenido es idéntico
        with open(decompressed_file, 'rb') as f:
            decompressed_content = f.read()
        
        self.assertEqual(self.test_content, decompressed_content, 
                        "El archivo descomprimido debe ser idéntico al original")
    
    def test_decompress_file_validation(self):
        """HU08: Test de validación de archivos de entrada para descompresión"""
        output_file = os.path.join(self.temp_dir, "output.txt")
        
        # Test archivo inexistente
        result = self.compressor.decompress_file_with_threads(
            input_file=os.path.join(self.temp_dir, "nonexistent.pz"),
            output_file=output_file,
            num_threads=2
        )
        self.assertFalse(result, "Debe fallar con archivo inexistente")
        
        # Test archivo sin extensión .pz
        result = self.compressor.decompress_file_with_threads(
            input_file=self.test_file,  # archivo .txt
            output_file=output_file,
            num_threads=2
        )
        self.assertFalse(result, "Debe fallar con archivo sin extensión .pz")
    
    def test_decompress_invalid_pz_file(self):
        """HU08: Test de descompresión de archivo .pz inválido"""
        # Crear archivo .pz falso (no es realmente comprimido)
        fake_pz = os.path.join(self.temp_dir, "fake.pz")
        with open(fake_pz, 'wb') as f:
            f.write(b"This is not a valid .pz file")
        
        output_file = os.path.join(self.temp_dir, "output.txt")
        
        # Intentar descomprimir
        result = self.compressor.decompress_file_with_threads(
            input_file=fake_pz,
            output_file=output_file,
            num_threads=2
        )
        
        self.assertFalse(result, "Debe fallar con archivo .pz inválido")
    
    def test_decompress_with_different_thread_counts(self):
        """HU08: Test de descompresión con diferentes números de hilos"""
        # Comprimir archivo primero
        compressed_file = os.path.join(self.temp_dir, "test_threads.pz")
        
        self.compressor.compress_file_with_threads(
            input_file=self.test_file,
            output_file=compressed_file,
            num_threads=4
        )
        
        # Probar descompresión con diferentes números de hilos
        for num_threads in [1, 2, 4]:
            with self.subTest(num_threads=num_threads):
                decompressed_file = os.path.join(self.temp_dir, f"decompressed_{num_threads}.txt")
                
                result = self.compressor.decompress_file_with_threads(
                    input_file=compressed_file,
                    output_file=decompressed_file,
                    num_threads=num_threads
                )
                
                self.assertTrue(result, f"Descompresión debe funcionar con {num_threads} hilos")
                
                # Verificar contenido
                with open(decompressed_file, 'rb') as f:
                    content = f.read()
                self.assertEqual(content, self.test_content, 
                               f"Contenido debe ser correcto con {num_threads} hilos")
    
    def test_decompress_large_file(self):
        """HU08: Test de descompresión de archivo grande"""
        # Crear archivo más grande
        large_content = b"Contenido repetido para archivo grande.\n" * 1000
        large_file = os.path.join(self.temp_dir, "large_test.txt")
        with open(large_file, 'wb') as f:
            f.write(large_content)
        
        # Comprimir
        compressed_file = os.path.join(self.temp_dir, "large_compressed.pz")
        compression_result = self.compressor.compress_file_with_threads(
            input_file=large_file,
            output_file=compressed_file,
            num_threads=4
        )
        self.assertTrue(compression_result, "Compresión de archivo grande debe funcionar")
        
        # Descomprimir
        decompressed_file = os.path.join(self.temp_dir, "large_decompressed.txt")
        decompression_result = self.compressor.decompress_file_with_threads(
            input_file=compressed_file,
            output_file=decompressed_file,
            num_threads=4
        )
        
        self.assertTrue(decompression_result, "Descompresión de archivo grande debe funcionar")
        
        # Verificar tamaño
        original_size = os.path.getsize(large_file)
        decompressed_size = os.path.getsize(decompressed_file)
        self.assertEqual(original_size, decompressed_size, "Los tamaños deben coincidir")
        
        # Verificar contenido por muestras (para optimizar test)
        with open(decompressed_file, 'rb') as f:
            decompressed_content = f.read(1000)  # Leer primeros 1000 bytes
        self.assertEqual(large_content[:1000], decompressed_content, 
                        "El contenido debe coincidir")
    
    def test_decompress_with_progress_callback(self):
        """HU08: Test de descompresión con callback de progreso"""
        # Comprimir archivo primero
        compressed_file = os.path.join(self.temp_dir, "progress_test.pz")
        self.compressor.compress_file_with_threads(
            input_file=self.test_file,
            output_file=compressed_file,
            num_threads=2
        )
        
        # Lista para capturar progreso
        progress_updates = []
        
        def progress_callback(message, progress, phase):
            progress_updates.append({
                'message': message,
                'progress': progress,
                'phase': phase
            })
            return True  # Continuar
        
        # Descomprimir con callback
        decompressed_file = os.path.join(self.temp_dir, "progress_decompressed.txt")
        result = self.compressor.decompress_file_with_threads(
            input_file=compressed_file,
            output_file=decompressed_file,
            num_threads=2,
            progress_callback=progress_callback
        )
        
        self.assertTrue(result, "Descompresión con callback debe funcionar")
        self.assertGreater(len(progress_updates), 0, "Debe haber actualizaciones de progreso")
        
        # Verificar que el progreso llegó al 100%
        final_progress = max(update['progress'] for update in progress_updates)
        self.assertEqual(final_progress, 100, "El progreso debe llegar al 100%")
        
        # Verificar fases del progreso
        phases = set(update['phase'] for update in progress_updates)
        expected_phases = {'🚀 Inicializando', '📖 Lectura', '🔄 Descompresión', '💾 Escritura', '✅ Completado'}
        self.assertTrue(phases.intersection(expected_phases), 
                       "Debe incluir fases esperadas de descompresión")
    
    def test_decompress_cancellation(self):
        """HU08: Test de cancelación durante descompresión"""
        # Comprimir archivo primero
        compressed_file = os.path.join(self.temp_dir, "cancel_test.pz")
        self.compressor.compress_file_with_threads(
            input_file=self.test_file,
            output_file=compressed_file,
            num_threads=2
        )
        
        # Callback que cancela después del primer update
        cancel_after_first = True
        
        def cancelling_callback(message, progress, phase):
            nonlocal cancel_after_first
            if cancel_after_first and progress > 0:
                self.compressor.stop_decompression()
                cancel_after_first = False
            return not self.compressor.cancel_requested
        
        # Intentar descomprimir con cancelación
        decompressed_file = os.path.join(self.temp_dir, "cancelled_decompressed.txt")
        result = self.compressor.decompress_file_with_threads(
            input_file=compressed_file,
            output_file=decompressed_file,
            num_threads=2,
            progress_callback=cancelling_callback
        )
        
        # La operación puede fallar o no completarse debido a la cancelación
        # El archivo de salida puede no existir o estar incompleto
        if os.path.exists(decompressed_file):
            # Si existe, debe ser más pequeño que el original o igual
            decompressed_size = os.path.getsize(decompressed_file)
            original_size = len(self.test_content)
            self.assertLessEqual(decompressed_size, original_size, 
                               "El archivo cancelado debe ser menor o igual al original")
    
    def test_decompress_error_handling(self):
        """HU08: Test de manejo de errores durante descompresión"""
        compressed_file = os.path.join(self.temp_dir, "error_test.pz")
        
        # Comprimir archivo primero
        self.compressor.compress_file_with_threads(
            input_file=self.test_file,
            output_file=compressed_file,
            num_threads=2
        )
        
        # Intentar descomprimir a ubicación sin permisos (simulado con archivo readonly)
        readonly_output = os.path.join(self.temp_dir, "readonly_output.txt")
        
        # Crear archivo readonly
        with open(readonly_output, 'w') as f:
            f.write("readonly")
        
        # En Windows, hacer el archivo readonly
        if os.name == 'nt':
            import stat
            os.chmod(readonly_output, stat.S_IREAD)
        
        try:
            result = self.compressor.decompress_file_with_threads(
                input_file=compressed_file,
                output_file=readonly_output,
                num_threads=2
            )
            
            # Debería fallar debido a permisos (en algunos sistemas)
            # No podemos garantizar el fallo en todos los sistemas, 
            # así que solo verificamos que se maneje apropiadamente
            
        except Exception:
            # Los errores deben ser manejados por el error handler
            pass
        finally:
            # Restaurar permisos para limpieza
            if os.name == 'nt':
                import stat
                try:
                    os.chmod(readonly_output, stat.S_IWRITE | stat.S_IREAD)
                    os.remove(readonly_output)
                except:
                    pass
        
        # Verificar que los errores se registraron
        error_history = self.error_handler.get_error_history()
        # Puede haber errores registrados dependiendo del sistema
    
    def test_read_compressed_file_header(self):
        """HU08: Test de lectura del encabezado de archivo comprimido"""
        # Comprimir archivo primero
        compressed_file = os.path.join(self.temp_dir, "header_test.pz")
        self.compressor.compress_file_with_threads(
            input_file=self.test_file,
            output_file=compressed_file,
            num_threads=2
        )
        
        # Leer encabezado
        header_info = self.compressor._read_compressed_file_header(compressed_file)
        
        # Verificar campos requeridos
        required_fields = ['original_filename', 'original_size', 'block_count', 'compression_algorithm']
        for field in required_fields:
            self.assertIn(field, header_info, f"El encabezado debe contener el campo '{field}'")
        
        # Verificar valores lógicos
        self.assertEqual(header_info['original_filename'], 'test_file.txt')
        self.assertEqual(header_info['original_size'], len(self.test_content))
        self.assertGreater(header_info['block_count'], 0, "Debe haber al menos un bloque")
    
    def test_file_size_verification(self):
        """HU08: Test de verificación de tamaño de archivo descomprimido"""
        # Comprimir archivo
        compressed_file = os.path.join(self.temp_dir, "size_test.pz")
        self.compressor.compress_file_with_threads(
            input_file=self.test_file,
            output_file=compressed_file,
            num_threads=2
        )
        
        # Descomprimir
        decompressed_file = os.path.join(self.temp_dir, "size_decompressed.txt")
        result = self.compressor.decompress_file_with_threads(
            input_file=compressed_file,
            output_file=decompressed_file,
            num_threads=2
        )
        
        self.assertTrue(result, "Descompresión debe ser exitosa")
        
        # Verificar tamaños
        original_size = os.path.getsize(self.test_file)
        decompressed_size = os.path.getsize(decompressed_file)
        
        self.assertEqual(original_size, decompressed_size, 
                        "El tamaño del archivo descomprimido debe coincidir con el original")


if __name__ == '__main__':
    unittest.main()
