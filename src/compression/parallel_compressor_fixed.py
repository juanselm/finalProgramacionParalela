"""
Módulo de compresión paralela
HU03: Compresión paralela con progreso visual
HU04: División de archivos en bloques de tamaño fijo
"""

import threading
import time
import zlib
import os
from pathlib import Path
from queue import Queue
from .block_manager import FileBlockManager


class ParallelCompressor:
    """Clase para manejar la compresión paralela de archivos"""
    
    def __init__(self, block_size: int = None):
        self.is_compressing = False
        self.compression_results = []
        self.cancel_requested = False
        # HU04: Integración con FileBlockManager para gestión de bloques
        self.block_manager = FileBlockManager(block_size)
        self.compression_stats = {}
    
    def set_block_size(self, block_size: int):
        """
        Configura el tamaño de bloque para la división
        HU04: El tamaño de bloque debe ser configurable
        """
        self.block_manager = FileBlockManager(block_size)
    
    def get_block_size(self) -> int:
        """Obtiene el tamaño de bloque actual"""
        return self.block_manager.block_size
    
    def compress_file(self, input_file, output_file, progress_callback=None):
        """Comprime un archivo usando múltiples hilos (4 hilos por defecto)"""
        return self.compress_file_with_threads(input_file, output_file, 4, progress_callback)
    
    def compress_file_with_threads(self, input_file, output_file, num_threads, progress_callback=None):
        """Comprime un archivo usando el número especificado de hilos"""
        try:
            self.is_compressing = True
            self.cancel_requested = False
            
            # Obtener configuración desde el callback
            if progress_callback:
                progress_callback("Iniciando compresión...", 0, "🚀 Iniciando")
            
            # HU04: Usar FileBlockManager para división mejorada en bloques
            blocks = self._split_file_into_blocks_improved(input_file, progress_callback)
            if self.cancel_requested:
                return False
            
            # Comprimir bloques en paralelo con distribución mejorada
            compressed_blocks = self._compress_blocks_parallel_improved(blocks, num_threads, progress_callback)
            if self.cancel_requested:
                return False
            
            # Escribir archivo comprimido
            success = self._write_compressed_file(compressed_blocks, output_file, progress_callback)
            
            self.is_compressing = False
            return success
            
        except Exception as e:
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
        HU04: Worker mejorado para comprimir bloques en un hilo
        Incluye validación de integridad y métricas detalladas
        """
        for block in blocks:
            if self.cancel_requested:
                break
                
            try:
                # Comprimir bloque usando zlib
                original_data = block['data']
                compressed_data = zlib.compress(original_data, level=6)
                
                # Calcular métricas de compresión
                compression_ratio = (len(compressed_data) / len(original_data)) * 100
                
                # Validar integridad de compresión
                try:
                    decompressed_test = zlib.decompress(compressed_data)
                    if decompressed_test != original_data:
                        raise ValueError("Error de integridad en compresión")
                except Exception as e:
                    # Si falla la compresión, usar datos originales
                    compressed_data = original_data
                    compression_ratio = 100.0
                
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
            return {'error': str(e)}
    
    def stop_compression(self):
        """Detiene la compresión en curso"""
        self.cancel_requested = True
        self.is_compressing = False
