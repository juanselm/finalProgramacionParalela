"""
Módulo de compresión paralela
HU03: Compresión paralela con progreso visual
HU04: División de archivos en bloques de tamaño fijo
HU05: Almacenamiento temporal y ensamblaje de bloques comprimidos
HU07: Manejo centralizado de errores
"""

import threading
import time
import zlib
import os
import json
from pathlib import Path
from queue import Queue
from .block_manager import FileBlockManager
from .temporary_storage import TemporaryBlockStorage, CompressionAlgorithm

# Import error handler with fallback for compatibility
try:
    from gui.error_handler import ErrorHandler, ErrorType, ErrorSeverity
except ImportError:
    # Fallback cuando se ejecuta desde tests
    import sys
    import os
    sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
    from gui.error_handler import ErrorHandler, ErrorType, ErrorSeverity


class ParallelCompressor:
    """Clase para manejar la compresión paralela de archivos"""
    
    def __init__(self, block_size: int = None, error_handler: ErrorHandler = None):
        self.is_compressing = False
        self.compression_results = []
        self.cancel_requested = False
        # HU04: Integración con FileBlockManager para gestión de bloques
        self.block_manager = FileBlockManager(block_size)
        self.compression_stats = {}
        # HU05: Almacenamiento temporal para bloques comprimidos
        self.temp_storage = None
        self.compression_algorithm = CompressionAlgorithm.ZLIB
        # HU07: Manejo centralizado de errores
        self.error_handler = error_handler
    
    def set_block_size(self, block_size: int):
        """
        Configura el tamaño de bloque para la división
        HU04: El tamaño de bloque debe ser configurable
        """
        self.block_manager = FileBlockManager(block_size)
    
    def get_block_size(self) -> int:
        """Obtiene el tamaño de bloque actual"""
        return self.block_manager.block_size
    
    def set_compression_algorithm(self, algorithm: CompressionAlgorithm):
        """
        HU05: Configura el algoritmo de compresión (zlib o RLE)
        """
        self.compression_algorithm = algorithm
    
    def get_compression_algorithm(self) -> CompressionAlgorithm:
        """
        HU05: Obtiene el algoritmo de compresión actual
        """
        return self.compression_algorithm
    
    def _handle_error(self, error: Exception, error_type: ErrorType, context: str = "", show_dialog: bool = False):
        """
        HU07: Método auxiliar para manejar errores de forma centralizada
        """
        if self.error_handler:
            return self.error_handler.handle_error(
                error=error,
                error_type=error_type,
                severity=ErrorSeverity.ERROR,
                context=context,
                show_dialog=show_dialog
            )
        else:
            # Fallback si no hay error handler
            print(f"Error en {context}: {str(error)}")
            return None
        """
        HU05: Obtiene el algoritmo de compresión actual
        """
        return self.compression_algorithm
    
    def compress_file(self, input_file, output_file, progress_callback=None):
        """Comprime un archivo usando múltiples hilos (4 hilos por defecto)"""
        return self.compress_file_with_threads(input_file, output_file, 4, progress_callback)
    
    def compress_file_with_threads(self, input_file, output_file, num_threads, progress_callback=None):
        """Comprime un archivo usando el número especificado de hilos"""
        try:
            self.is_compressing = True
            self.cancel_requested = False
            
            # HU05: Inicializar almacenamiento temporal
            self.temp_storage = TemporaryBlockStorage()
            
            # Obtener configuración desde el callback
            if progress_callback:
                progress_callback("Iniciando compresión...", 0, "🚀 Iniciando")
            
            # HU04: Usar FileBlockManager para división mejorada en bloques
            blocks = self._split_file_into_blocks_improved(input_file, progress_callback)
            if self.cancel_requested:
                return False
            
            # HU05: Configurar información del archivo en almacenamiento temporal
            self.temp_storage.set_file_info(input_file, output_file, len(blocks))
            
            # Comprimir bloques en paralelo con distribución mejorada
            compressed_blocks = self._compress_blocks_parallel_improved(blocks, num_threads, progress_callback)
            if self.cancel_requested:
                return False
            
            # HU05: Escribir archivo comprimido con ensamblaje de bloques temporales
            success = self._write_compressed_file_from_storage(output_file, progress_callback)
            
            # HU05: Limpiar almacenamiento temporal
            if self.temp_storage:
                self.temp_storage.cleanup()
                self.temp_storage = None
            
            self.is_compressing = False
            return success
            
        except Exception as e:
            # HU07: Manejo centralizado de errores
            self._handle_error(e, ErrorType.COMPRESSION, "Compresión de archivo", show_dialog=False)
            # HU05: Limpiar almacenamiento temporal en caso de error
            if self.temp_storage:
                self.temp_storage.cleanup()
                self.temp_storage = None
            self.is_compressing = False
            raise e
    
    def _split_file_into_blocks_improved(self, file_path, progress_callback=None):
        """
        HU04: División mejorada usando FileBlockManager
        Divide el archivo en bloques de tamaño fijo con validación completa
        """
        try:
            if progress_callback:
                progress_callback("Analizando archivo para división...", 2, "📊 Análisis")
            
            # Usar FileBlockManager para división robusta
            blocks = self.block_manager.split_file_into_blocks(
                file_path, 
                lambda msg, prog, phase: self._forward_progress(progress_callback, msg, 2 + prog * 0.13, phase)
            )
            
            # Guardar estadísticas de división
            self.compression_stats['block_stats'] = self.block_manager.get_statistics()
            self.compression_stats['block_analysis'] = self.block_manager.analyze_file(file_path)
            
            if progress_callback:
                progress_callback(
                    f"División completada: {len(blocks)} bloques de {self.block_manager.block_size // 1024}KB", 
                    15, 
                    "✅ División completa"
                )
            
            return blocks
            
        except Exception as e:
            # HU07: Manejo centralizado de errores
            self._handle_error(e, ErrorType.FILE_READ, "División de archivo en bloques", show_dialog=False)
            if progress_callback:
                progress_callback(f"Error en división: {str(e)}", 0, "❌ Error")
            raise e
    
    def _forward_progress(self, callback, message, progress, phase):
        """Método auxiliar para reenviar progreso con ajuste de escala"""
        if callback:
            return callback(message, progress, phase)
        return True
    
    def _compress_blocks_parallel_improved(self, blocks, num_threads, progress_callback=None):
        """
        HU04: Compresión paralela mejorada con distribución inteligente de bloques
        """
        if progress_callback:
            if not progress_callback("Iniciando compresión paralela...", 20, "🗜️ Compresión"):
                self.cancel_requested = True
                return []
        
        compressed_blocks = [None] * len(blocks)
        threads = []
        progress_queue = Queue()
        
        # HU04: Usar distribución inteligente de bloques
        distribution = self.block_manager.get_block_distribution_for_threads(num_threads)
        
        # Crear hilos con distribución optimizada
        for thread_id, block_ids in enumerate(distribution):
            if not block_ids:  # Saltar hilos sin bloques asignados
                continue
                
            thread_blocks = [blocks[block_id] for block_id in block_ids]
            
            thread = threading.Thread(
                target=self._compress_thread_worker_improved,
                args=(thread_blocks, compressed_blocks, progress_queue, thread_id)
            )
            threads.append(thread)
            thread.start()
        
        # Monitorear progreso
        completed_blocks = 0
        total_blocks = len(blocks)
        
        while completed_blocks < total_blocks and not self.cancel_requested:
            try:
                # Esperar reporte de progreso (timeout para poder cancelar)
                progress_info = progress_queue.get(timeout=0.1)
                completed_blocks += 1
                
                # Progreso de compresión (20% a 80%)
                compression_progress = 20 + (completed_blocks / total_blocks) * 60
                
                if progress_callback:
                    status = f"Comprimiendo bloque {progress_info['block_id']} (hilo {progress_info['thread_id']}) - {progress_info['compression_ratio']:.1f}% ratio"
                    if not progress_callback(status, compression_progress, "🗜️ Compresión paralela"):
                        self.cancel_requested = True
                        break
                        
            except:
                # Timeout - continuar verificando
                if self.cancel_requested:
                    break
                continue
        
        # Esperar a que terminen todos los hilos
        for thread in threads:
            thread.join()
        
        if self.cancel_requested:
            return []
        
        if progress_callback:
            progress_callback("Compresión de bloques completada", 80, "✅ Compresión terminada")
        
        return compressed_blocks
    
    def _compress_thread_worker_improved(self, blocks, result_array, progress_queue, thread_id):
        """
        HU05: Worker mejorado para comprimir bloques en un hilo
        Cada hilo comprime un bloque y lo almacena temporalmente
        """
        for block in blocks:
            if self.cancel_requested:
                break
                
            try:
                # HU05: Comprimir bloque usando el algoritmo configurado (zlib por defecto)
                original_data = block['data']
                
                if self.compression_algorithm == CompressionAlgorithm.ZLIB:
                    compressed_data = zlib.compress(original_data, level=6)
                else:
                    # RLE como alternativa (implementación simple)
                    compressed_data = self._compress_rle(original_data)
                
                # Calcular métricas de compresión
                compression_ratio = (len(compressed_data) / len(original_data)) * 100
                
                # Validar integridad de compresión
                try:
                    if self.compression_algorithm == CompressionAlgorithm.ZLIB:
                        decompressed_test = zlib.decompress(compressed_data)
                    else:
                        decompressed_test = self._decompress_rle(compressed_data)
                        
                    if decompressed_test != original_data:
                        raise ValueError("Error de integridad en compresión")
                except Exception as e:
                    # Si falla la compresión, usar datos originales
                    compressed_data = original_data
                    compression_ratio = 100.0
                
                # HU05: Almacenar bloque comprimido en almacenamiento temporal
                if self.temp_storage:
                    block_path = self.temp_storage.store_compressed_block(
                        block['id'], 
                        compressed_data,
                        block['size'],
                        compression_ratio,
                        thread_id,
                        block['checksum']
                    )
                
                # Mantener compatibilidad con result_array
                result_array[block['id']] = {
                    'id': block['id'],
                    'compressed_data': compressed_data,
                    'original_size': block['size'],
                    'compressed_size': len(compressed_data),
                    'compression_ratio': compression_ratio,
                    'start_offset': block['start_offset'],
                    'end_offset': block['end_offset'],
                    'original_checksum': block['checksum'],
                    'thread_id': thread_id
                }
                
                # Reportar progreso con métricas
                progress_queue.put({
                    'block_id': block['id'],
                    'thread_id': thread_id,
                    'compressed_size': len(compressed_data),
                    'original_size': block['size'],
                    'compression_ratio': compression_ratio
                })
                
                # Simular tiempo de procesamiento realista
                time.sleep(0.005)
                
            except Exception as e:
                # HU07: Manejo centralizado de errores
                self._handle_error(e, ErrorType.COMPRESSION, f"Compresión de bloque {block['id']}", show_dialog=False)
                print(f"Error comprimiendo bloque {block['id']}: {e}")
                if not self.cancel_requested:
                    # En caso de error, guardar bloque sin comprimir
                    result_array[block['id']] = {
                        'id': block['id'],
                        'compressed_data': block['data'],
                        'original_size': block['size'],
                        'compressed_size': block['size'],
                        'compression_ratio': 100.0,
                        'start_offset': block['start_offset'],
                        'end_offset': block['end_offset'],
                        'original_checksum': block['checksum'],
                        'thread_id': thread_id,
                        'error': str(e)
                    }
                    progress_queue.put({
                        'block_id': block['id'],
                        'thread_id': thread_id,
                        'compressed_size': block['size'],
                        'original_size': block['size'],
                        'compression_ratio': 100.0
                    })
    
    def _compress_rle(self, data: bytes) -> bytes:
        """
        HU05: Implementación simple de RLE (Run-Length Encoding)
        Como alternativa a zlib
        """
        if not data:
            return b''
        
        compressed = []
        current_byte = data[0]
        count = 1
        
        for i in range(1, len(data)):
            if data[i] == current_byte and count < 255:
                count += 1
            else:
                compressed.extend([count, current_byte])
                current_byte = data[i]
                count = 1
        
        # Agregar último run
        compressed.extend([count, current_byte])
        
        return bytes(compressed)
    
    def _decompress_rle(self, data: bytes) -> bytes:
        """
        HU05: Descompresión RLE para validación
        """
        if not data or len(data) % 2 != 0:
            return b''
        
        decompressed = []
        for i in range(0, len(data), 2):
            count = data[i]
            byte_value = data[i + 1]
            decompressed.extend([byte_value] * count)
        
        return bytes(decompressed)
    
    def _write_compressed_file_from_storage(self, output_file, progress_callback=None):
        """
        HU05: Escribe el archivo comprimido ensamblando bloques desde almacenamiento temporal
        Los bloques se ensamblan en orden y se incluyen metadatos en el encabezado
        """
        if progress_callback:
            if not progress_callback("Ensamblando archivo desde almacenamiento temporal...", 85, "🔧 Ensamblaje"):
                self.cancel_requested = True
                return False
        
        try:
            if not self.temp_storage:
                raise ValueError("No hay almacenamiento temporal inicializado")
            
            # HU05: Obtener metadata ordenada de bloques
            ordered_blocks_metadata = self.temp_storage.get_ordered_blocks_metadata()
            
            with open(output_file, 'wb') as f:
                # HU05: Escribir encabezado con metadatos de orden
                header_info = {
                    'format': 'PARZIP_V1',
                    'total_blocks': len(ordered_blocks_metadata),
                    'compression_algorithm': self.compression_algorithm,
                    'block_order': [block['id'] for block in ordered_blocks_metadata]
                }
                
                header_json = json.dumps(header_info).encode('utf-8')
                header_size = len(header_json)
                
                # Escribir tamaño del encabezado (4 bytes) y luego el encabezado
                f.write(header_size.to_bytes(4, byteorder='little'))
                f.write(header_json)
                
                # HU05: Escribir metadatos de cada bloque en orden
                for block_meta in ordered_blocks_metadata:
                    # Escribir tamaño del bloque comprimido (4 bytes)
                    f.write(block_meta['compressed_size'].to_bytes(4, byteorder='little'))
                    # Escribir tamaño original (4 bytes)
                    f.write(block_meta['original_size'].to_bytes(4, byteorder='little'))
                
                # HU05: Escribir datos comprimidos en orden
                for i, block_meta in enumerate(ordered_blocks_metadata):
                    if self.cancel_requested:
                        return False
                    
                    # Recuperar datos del bloque desde almacenamiento temporal
                    block_data = self.temp_storage.retrieve_block_data(block_meta['id'])
                    f.write(block_data)
                    
                    # Progreso de escritura (85% a 98%)
                    write_progress = 85 + (i / len(ordered_blocks_metadata)) * 13
                    if progress_callback:
                        if not progress_callback(f"Escribiendo bloque {i+1}/{len(ordered_blocks_metadata)}", 
                                               write_progress, "💾 Escritura final"):
                            self.cancel_requested = True
                            return False
            
            if progress_callback:
                progress_callback("Archivo comprimido exitosamente", 100, "✅ Completado")
            
            return True
            
        except Exception as e:
            # HU07: Manejo centralizado de errores
            self._handle_error(e, ErrorType.FILE_WRITE, "Ensamblaje de archivo final", show_dialog=False)
            print(f"Error ensamblando archivo: {e}")
            return False
    
    def _write_compressed_file(self, compressed_blocks, output_file, progress_callback=None):
        """Escribe el archivo comprimido"""
        if progress_callback:
            if not progress_callback("Escribiendo archivo comprimido...", 85, "💾 Escritura"):
                self.cancel_requested = True
                return False
        
        try:
            with open(output_file, 'wb') as f:
                # Escribir header simple
                header = f"PARZIP_V1:{len(compressed_blocks)}\n".encode()
                f.write(header)
                
                # Escribir metadatos de cada bloque
                for i, block in enumerate(compressed_blocks):
                    if self.cancel_requested:
                        return False
                        
                    if block:  # Verificar que el bloque no sea None
                        # Escribir tamaño del bloque comprimido (4 bytes)
                        f.write(len(block['compressed_data']).to_bytes(4, byteorder='little'))
                        # Escribir tamaño original (4 bytes)
                        f.write(block['original_size'].to_bytes(4, byteorder='little'))
                
                # Escribir datos comprimidos
                for i, block in enumerate(compressed_blocks):
                    if self.cancel_requested:
                        return False
                        
                    if block:
                        f.write(block['compressed_data'])
                        
                        # Progreso de escritura (85% a 98%)
                        write_progress = 85 + (i / len(compressed_blocks)) * 13
                        if progress_callback:
                            if not progress_callback(f"Escribiendo bloque {i+1}/{len(compressed_blocks)}", 
                                                   write_progress, "💾 Escritura"):
                                self.cancel_requested = True
                                return False
            
            if progress_callback:
                progress_callback("Archivo comprimido exitosamente", 100, "✅ Completado")
            
            return True
            
        except Exception as e:
            # HU07: Manejo centralizado de errores
            self._handle_error(e, ErrorType.FILE_WRITE, "Escritura de archivo comprimido", show_dialog=False)
            print(f"Error escribiendo archivo: {e}")
            return False
    
    # Métodos de compatibilidad para mantener funcionalidad existente
    def _split_file_into_blocks(self, file_path, progress_callback=None):
        """Método de compatibilidad - redirige al método mejorado"""
        return self._split_file_into_blocks_improved(file_path, progress_callback)
    
    def _compress_blocks_parallel(self, blocks, num_threads, progress_callback=None):
        """Método de compatibilidad - redirige al método mejorado"""
        return self._compress_blocks_parallel_improved(blocks, num_threads, progress_callback)
    
    def _compress_thread_worker(self, blocks, result_array, start_idx, progress_queue, thread_id):
        """Método de compatibilidad - usa worker mejorado"""
        # Simular el comportamiento anterior con el nuevo worker
        for i, block in enumerate(blocks):
            result_array[start_idx + i] = None  # Inicializar posición
        
        # Usar worker mejorado
        self._compress_thread_worker_improved(blocks, result_array, progress_queue, thread_id)
    
    def get_compression_statistics(self):
        """
        HU04: Obtiene estadísticas detalladas de la compresión
        """
        return self.compression_stats
    
    def analyze_file_for_compression(self, file_path):
        """
        HU04: Analiza un archivo para determinar la estrategia de compresión óptima
        """
        try:
            analysis = self.block_manager.analyze_file(file_path)
            return analysis
        except Exception as e:
            return {'error': str(e)}
    
    def suggest_optimal_block_size(self, file_path, num_threads):
        """
        HU04: Sugiere un tamaño de bloque óptimo para el archivo y configuración dados
        """
        try:
            file_size = os.path.getsize(file_path)
            optimal_size = FileBlockManager.calculate_optimal_block_size(file_size, num_threads)
            return {
                'suggested_block_size': optimal_size,
                'suggested_block_size_mb': optimal_size / (1024 * 1024),
                'current_block_size': self.block_manager.block_size,
                'improvement_expected': optimal_size != self.block_manager.block_size
            }
        except Exception as e:
            # HU07: Manejo centralizado de errores
            self._handle_error(e, ErrorType.VALIDATION, "Cálculo de tamaño óptimo de bloque", show_dialog=False)
            return {'error': str(e)}
    
    def stop_compression(self):
        """Detiene la compresión en curso"""
        self.cancel_requested = True
        self.is_compressing = False