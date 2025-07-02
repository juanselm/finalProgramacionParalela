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
        # HU08: Estado de descompresión
        self.is_decompressing = False
    
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
            success = self._write_compressed_file_from_storage(input_file, output_file, progress_callback)
            
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
    
    def _write_compressed_file_from_storage(self, input_file, output_file, progress_callback=None):
        """
        HU05/HU08: Escribe el archivo comprimido ensamblando bloques desde almacenamiento temporal
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
                # HU05/HU08: Escribir encabezado con metadatos completos
                original_filename = os.path.basename(input_file) if input_file else "unknown"
                original_size = sum(block['original_size'] for block in ordered_blocks_metadata)
                
                header_info = {
                    'format': 'PARZIP_V1',
                    'original_filename': original_filename,  # HU08: Campo requerido para descompresión
                    'original_size': original_size,  # HU08: Campo requerido para descompresión
                    'block_count': len(ordered_blocks_metadata),  # HU08: Campo requerido para descompresión
                    'total_blocks': len(ordered_blocks_metadata),  # Compatibilidad
                    'compression_algorithm': self.compression_algorithm.value if hasattr(self.compression_algorithm, 'value') else str(self.compression_algorithm),  # HU08: Campo requerido
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
    
    def decompress_file(self, input_file, output_file, progress_callback=None):
        """Descomprime un archivo usando múltiples hilos (4 hilos por defecto)"""
        return self.decompress_file_with_threads(input_file, output_file, 4, progress_callback)
    
    def decompress_file_with_threads(self, input_file: str, output_file: str, num_threads: int = None, progress_callback=None):
        """
        HU08: Descomprime un archivo .pz usando múltiples hilos
        
        Args:
            input_file: Ruta del archivo .pz a descomprimir
            output_file: Ruta donde guardar el archivo descomprimido
            num_threads: Número de hilos a usar (por defecto se calcula automáticamente)
            progress_callback: Función callback para reportar progreso
            
        Returns:
            bool: True si la descompresión fue exitosa, False en caso contrario
        """
        if self.is_decompressing:
            raise RuntimeError("Ya hay una descompresión en curso")
        
        try:
            self.is_decompressing = True
            self.cancel_requested = False
            
            if progress_callback:
                progress_callback("Iniciando descompresión...", 0, "🚀 Inicializando")
            
            # Validar archivo de entrada
            if not os.path.exists(input_file):
                raise FileNotFoundError(f"El archivo {input_file} no existe")
            
            if not input_file.lower().endswith('.pz'):
                raise ValueError("El archivo debe tener extensión .pz")
            
            # Leer información del archivo comprimido
            file_info = self._read_compressed_file_header(input_file, progress_callback)
            
            if progress_callback:
                progress_callback("Leyendo bloques comprimidos...", 10, "📖 Lectura")
            
            # Leer bloques comprimidos
            compressed_blocks = self._read_compressed_blocks(input_file, file_info, progress_callback)
            
            if progress_callback:
                progress_callback("Descomprimiendo bloques en paralelo...", 25, "🔄 Descompresión")
            
            # Descomprimir bloques en paralelo
            if num_threads is None:
                num_threads = min(4, len(compressed_blocks), os.cpu_count() or 1)
            
            decompressed_blocks = self._decompress_blocks_parallel(compressed_blocks, num_threads, progress_callback)
            
            if progress_callback:
                progress_callback("Ensamblando archivo final...", 85, "🔧 Ensamblaje")
            
            # Ensamblar archivo final
            success = self._write_decompressed_file(decompressed_blocks, output_file, file_info, progress_callback)
            
            if success and progress_callback:
                original_size = file_info.get('original_size', 0)
                compressed_size = os.path.getsize(input_file)
                progress_callback("Descompresión completada exitosamente", 100, "✅ Completado")
            
            return success
            
        except Exception as e:
            # HU07: Manejo centralizado de errores
            self._handle_error(e, ErrorType.DECOMPRESSION, "Descompresión de archivo", show_dialog=False)
            if progress_callback:
                progress_callback(f"Error en descompresión: {str(e)}", 0, "❌ Error")
            return False
        finally:
            self.is_decompressing = False
    
    def _read_compressed_file_header(self, file_path: str, progress_callback=None):
        """
        HU08: Lee el encabezado de un archivo .pz comprimido
        """
        try:
            with open(file_path, 'rb') as f:
                # Leer tamaño del encabezado (4 bytes)
                header_size_bytes = f.read(4)
                if len(header_size_bytes) < 4:
                    raise ValueError("Archivo comprimido inválido: encabezado incompleto")
                
                header_size = int.from_bytes(header_size_bytes, byteorder='little')
                
                if header_size <= 0 or header_size > 1024 * 1024:  # Máximo 1MB para el header
                    raise ValueError("Archivo comprimido inválido: tamaño de encabezado incorrecto")
                
                # Leer y deserializar encabezado
                header_json = f.read(header_size)
                if len(header_json) < header_size:
                    raise ValueError("Archivo comprimido inválido: encabezado truncado")
                
                header_info = json.loads(header_json.decode('utf-8'))
                
                # Validar estructura del encabezado
                required_fields = ['original_filename', 'original_size', 'block_count', 'compression_algorithm']
                for field in required_fields:
                    if field not in header_info:
                        raise ValueError(f"Archivo comprimido inválido: campo '{field}' faltante en encabezado")
                
                return header_info
                
        except json.JSONDecodeError as e:
            raise ValueError(f"Archivo comprimido inválido: error en JSON del encabezado - {str(e)}")
        except Exception as e:
            # HU07: Manejo centralizado de errores
            self._handle_error(e, ErrorType.FILE_READ, "Lectura de encabezado de archivo comprimido", show_dialog=False)
            raise
    
    def _read_compressed_blocks(self, file_path: str, file_info: dict, progress_callback=None):
        """
        HU08: Lee los bloques comprimidos de un archivo .pz
        """
        try:
            compressed_blocks = []
            
            with open(file_path, 'rb') as f:
                # Saltar encabezado
                header_size_bytes = f.read(4)
                header_size = int.from_bytes(header_size_bytes, byteorder='little')
                f.read(header_size)  # Saltar JSON del encabezado
                
                block_count = file_info['block_count']
                
                # Leer metadatos de bloques
                block_metadata = []
                for i in range(block_count):
                    # Leer tamaño comprimido (4 bytes)
                    compressed_size_bytes = f.read(4)
                    if len(compressed_size_bytes) < 4:
                        raise ValueError(f"Archivo comprimido inválido: metadatos de bloque {i} incompletos")
                    
                    compressed_size = int.from_bytes(compressed_size_bytes, byteorder='little')
                    
                    # Leer tamaño original (4 bytes)
                    original_size_bytes = f.read(4)
                    if len(original_size_bytes) < 4:
                        raise ValueError(f"Archivo comprimido inválido: metadatos de bloque {i} incompletos")
                    
                    original_size = int.from_bytes(original_size_bytes, byteorder='little')
                    
                    block_metadata.append({
                        'id': i,
                        'compressed_size': compressed_size,
                        'original_size': original_size
                    })
                
                # Leer datos comprimidos de cada bloque
                for i, meta in enumerate(block_metadata):
                    if self.cancel_requested:
                        break
                    
                    compressed_data = f.read(meta['compressed_size'])
                    if len(compressed_data) < meta['compressed_size']:
                        raise ValueError(f"Archivo comprimido inválido: datos de bloque {i} incompletos")
                    
                    compressed_blocks.append({
                        'id': meta['id'],
                        'compressed_data': compressed_data,
                        'compressed_size': meta['compressed_size'],
                        'original_size': meta['original_size']
                    })
                    
                    # Progreso de lectura (10% a 25%)
                    read_progress = 10 + (i / len(block_metadata)) * 15
                    if progress_callback:
                        if not progress_callback(f"Leyendo bloque {i+1}/{len(block_metadata)}", 
                                               read_progress, "📖 Lectura"):
                            self.cancel_requested = True
                            break
            
            return compressed_blocks
            
        except Exception as e:
            # HU07: Manejo centralizado de errores
            self._handle_error(e, ErrorType.FILE_READ, "Lectura de bloques comprimidos", show_dialog=False)
            raise
    
    def _decompress_blocks_parallel(self, compressed_blocks: list, num_threads: int, progress_callback=None):
        """
        HU08: Descomprime bloques en paralelo usando múltiples hilos
        """
        try:
            # Inicializar array de resultados
            decompressed_blocks = [None] * len(compressed_blocks)
            
            # Cola para reportar progreso
            progress_queue = Queue()
            
            # Dividir bloques entre hilos
            blocks_per_thread = len(compressed_blocks) // num_threads
            remainder = len(compressed_blocks) % num_threads
            
            threads = []
            start_idx = 0
            
            for thread_id in range(num_threads):
                # Calcular cantidad de bloques para este hilo
                thread_blocks = blocks_per_thread + (1 if thread_id < remainder else 0)
                end_idx = start_idx + thread_blocks
                
                if thread_blocks > 0:
                    thread_blocks_list = compressed_blocks[start_idx:end_idx]
                    
                    # Crear y ejecutar hilo
                    thread = threading.Thread(
                        target=self._decompress_thread_worker,
                        args=(thread_blocks_list, decompressed_blocks, start_idx, progress_queue, thread_id)
                    )
                    threads.append(thread)
                    thread.start()
                
                start_idx = end_idx
            
            # Monitorear progreso
            completed_blocks = 0
            total_blocks = len(compressed_blocks)
            
            while completed_blocks < total_blocks and not self.cancel_requested:
                try:
                    progress_info = progress_queue.get(timeout=0.1)
                    completed_blocks += 1
                    
                    # Progreso de descompresión (25% a 85%)
                    decompress_progress = 25 + (completed_blocks / total_blocks) * 60
                    
                    if progress_callback:
                        if not progress_callback(
                            f"Descomprimiendo bloque {completed_blocks}/{total_blocks}", 
                            decompress_progress, 
                            f"🔄 Hilo {progress_info.get('thread_id', '?')}"
                        ):
                            self.cancel_requested = True
                            break
                    
                except:
                    # Timeout - continuar monitoreando
                    pass
            
            # Esperar a que terminen todos los hilos
            for thread in threads:
                thread.join()
            
            if self.cancel_requested:
                return None
            
            return decompressed_blocks
            
        except Exception as e:
            # HU07: Manejo centralizado de errores
            self._handle_error(e, ErrorType.DECOMPRESSION, "Descompresión paralela de bloques", show_dialog=False)
            raise
    
    def _decompress_thread_worker(self, compressed_blocks: list, result_array: list, start_idx: int, progress_queue: Queue, thread_id: int):
        """
        HU08: Worker que descomprime bloques en un hilo
        """
        for i, block in enumerate(compressed_blocks):
            if self.cancel_requested:
                break
            
            try:
                # Descomprimir datos según el algoritmo usado
                compressed_data = block['compressed_data']
                
                # Por ahora asumimos zlib, pero podríamos detectar el algoritmo del header
                if len(compressed_data) == block['original_size']:
                    # Bloque no estaba comprimido (posible error durante compresión)
                    decompressed_data = compressed_data
                else:
                    # Intentar descompresión zlib
                    try:
                        decompressed_data = zlib.decompress(compressed_data)
                    except zlib.error:
                        # Si falla zlib, intentar RLE
                        decompressed_data = self._decompress_rle(compressed_data)
                
                # Verificar tamaño
                if len(decompressed_data) != block['original_size']:
                    raise ValueError(f"Tamaño descomprimido incorrecto para bloque {block['id']}")
                
                # Almacenar resultado
                result_array[start_idx + i] = {
                    'id': block['id'],
                    'data': decompressed_data,
                    'original_size': block['original_size'],
                    'thread_id': thread_id
                }
                
                # Reportar progreso
                progress_queue.put({
                    'block_id': block['id'],
                    'thread_id': thread_id,
                    'decompressed_size': len(decompressed_data)
                })
                
            except Exception as e:
                # HU07: Manejo centralizado de errores
                self._handle_error(e, ErrorType.DECOMPRESSION, f"Descompresión de bloque {block['id']}", show_dialog=False)
                print(f"Error descomprimiendo bloque {block['id']}: {e}")
                
                # En caso de error, marcar bloque como fallido
                result_array[start_idx + i] = {
                    'id': block['id'],
                    'data': None,
                    'error': str(e),
                    'thread_id': thread_id
                }
    
    def _decompress_rle(self, compressed_data: bytes) -> bytes:
        """
        HU08: Descomprime datos usando Run-Length Encoding (RLE)
        """
        try:
            decompressed = bytearray()
            i = 0
            
            while i < len(compressed_data):
                if i + 1 >= len(compressed_data):
                    break
                
                count = compressed_data[i]
                value = compressed_data[i + 1]
                
                # Añadir bytes descomprimidos
                decompressed.extend([value] * count)
                i += 2
            
            return bytes(decompressed)
            
        except Exception as e:
            raise ValueError(f"Error en descompresión RLE: {str(e)}")
    
    def _write_decompressed_file(self, decompressed_blocks: list, output_file: str, file_info: dict, progress_callback=None):
        """
        HU08: Escribe el archivo descomprimido ensamblando los bloques en orden
        """
        try:
            # Verificar que todos los bloques se descomprimieron correctamente
            for i, block in enumerate(decompressed_blocks):
                if block is None or block.get('data') is None:
                    error_msg = block.get('error', 'Desconocido') if block else 'Bloque faltante'
                    raise ValueError(f"Error en bloque {i}: {error_msg}")
            
            # Crear directorio de destino si no existe
            output_dir = os.path.dirname(output_file)
            if output_dir and not os.path.exists(output_dir):
                os.makedirs(output_dir)
            
            # Escribir archivo descomprimido
            with open(output_file, 'wb') as f:
                total_blocks = len(decompressed_blocks)
                
                for i, block in enumerate(decompressed_blocks):
                    if self.cancel_requested:
                        return False
                    
                    f.write(block['data'])
                    
                    # Progreso de escritura (85% a 98%)
                    write_progress = 85 + (i / total_blocks) * 13
                    if progress_callback:
                        if not progress_callback(f"Escribiendo bloque {i+1}/{total_blocks}", 
                                               write_progress, "💾 Escritura"):
                            self.cancel_requested = True
                            return False
            
            # Verificar tamaño final
            actual_size = os.path.getsize(output_file)
            expected_size = file_info.get('original_size', 0)
            
            if actual_size != expected_size:
                raise ValueError(f"Tamaño del archivo descomprimido incorrecto: {actual_size} vs {expected_size} esperados")
            
            if progress_callback:
                progress_callback("Archivo descomprimido exitosamente", 100, "✅ Completado")
            
            return True
            
        except Exception as e:
            # HU07: Manejo centralizado de errores
            self._handle_error(e, ErrorType.FILE_WRITE, "Escritura de archivo descomprimido", show_dialog=False)
            raise
    
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
    
    def stop_decompression(self):
        """
        HU08: Detiene la descompresión en curso
        """
        self.cancel_requested = True
        self.is_decompressing = False