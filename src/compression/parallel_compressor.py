"""
Módulo de compresión paralela
HU03: Compresión paralela con progreso visual
"""

import threading
import time
import zlib
import os
from pathlib import Path
from queue import Queue


class ParallelCompressor:
    """Clase para manejar la compresión paralela de archivos"""
    
    def __init__(self):
        self.is_compressing = False
        self.compression_results = []
        self.cancel_requested = False
    
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
            
            # Leer archivo y dividir en bloques
            blocks = self._split_file_into_blocks(input_file, progress_callback)
            if self.cancel_requested:
                return False
            
            # Comprimir bloques en paralelo
            compressed_blocks = self._compress_blocks_parallel(blocks, num_threads, progress_callback)
            if self.cancel_requested:
                return False
            
            # Escribir archivo comprimido
            success = self._write_compressed_file(compressed_blocks, output_file, progress_callback)
            
            self.is_compressing = False
            return success
            
        except Exception as e:
            self.is_compressing = False
            raise e
    
    def _split_file_into_blocks(self, file_path, progress_callback=None):
        """Divide el archivo en bloques"""
        if progress_callback:
            if not progress_callback("Analizando archivo...", 5, "📊 Análisis"):
                self.cancel_requested = True
                return []
        
        # Tamaño de bloque: 1MB
        block_size_bytes = 1024 * 1024
        
        blocks = []
        file_size = os.path.getsize(file_path)
        
        with open(file_path, 'rb') as f:
            block_id = 0
            bytes_read = 0
            
            while True:
                if self.cancel_requested:
                    return []
                
                data = f.read(block_size_bytes)
                if not data:
                    break
                    
                blocks.append({
                    'id': block_id,
                    'data': data,
                    'size': len(data)
                })
                
                bytes_read += len(data)
                block_id += 1
                
                # Actualizar progreso de lectura (5% a 15%)
                read_progress = 5 + (bytes_read / file_size) * 10
                if progress_callback:
                    if not progress_callback(f"Leyendo bloque {block_id}...", read_progress, "📖 Lectura"):
                        self.cancel_requested = True
                        return []
        
        if progress_callback:
            progress_callback(f"Archivo dividido en {len(blocks)} bloques", 15, "✅ División completa")
        
        return blocks
    
    def _compress_blocks_parallel(self, blocks, num_threads, progress_callback=None):
        """Comprime los bloques usando múltiples hilos"""
        if progress_callback:
            if not progress_callback("Iniciando compresión paralela...", 20, "🗜️ Compresión"):
                self.cancel_requested = True
                return []
        
        compressed_blocks = [None] * len(blocks)
        threads = []
        progress_queue = Queue()
        
        # Dividir bloques entre hilos
        blocks_per_thread = max(1, len(blocks) // num_threads)
        
        for thread_id in range(num_threads):
            start_idx = thread_id * blocks_per_thread
            if thread_id == num_threads - 1:
                end_idx = len(blocks)  # Último hilo toma los bloques restantes
            else:
                end_idx = (thread_id + 1) * blocks_per_thread
            
            if start_idx < len(blocks):
                thread_blocks = blocks[start_idx:end_idx]
                
                thread = threading.Thread(
                    target=self._compress_thread_worker,
                    args=(thread_blocks, compressed_blocks, start_idx, progress_queue, thread_id)
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
                    status = f"Comprimiendo bloque {progress_info['block_id']} (hilo {progress_info['thread_id']})"
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
    
    def _compress_thread_worker(self, blocks, result_array, start_idx, progress_queue, thread_id):
        """Worker function para comprimir bloques en un hilo"""
        for i, block in enumerate(blocks):
            if self.cancel_requested:
                break
                
            try:
                # Comprimir bloque usando zlib
                compressed_data = zlib.compress(block['data'], level=6)
                
                result_array[start_idx + i] = {
                    'id': block['id'],
                    'compressed_data': compressed_data,
                    'original_size': block['size'],
                    'compressed_size': len(compressed_data)
                }
                
                # Reportar progreso
                progress_queue.put({
                    'block_id': block['id'],
                    'thread_id': thread_id,
                    'compressed_size': len(compressed_data),
                    'original_size': block['size']
                })
                
                # Simular tiempo de procesamiento realista
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Error comprimiendo bloque {block['id']}: {e}")
                if not self.cancel_requested:
                    # En caso de error, guardar bloque sin comprimir
                    result_array[start_idx + i] = {
                        'id': block['id'],
                        'compressed_data': block['data'],
                        'original_size': block['size'],
                        'compressed_size': block['size']
                    }
                    progress_queue.put({
                        'block_id': block['id'],
                        'thread_id': thread_id,
                        'compressed_size': block['size'],
                        'original_size': block['size']
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
    
    def stop_compression(self):
        """Detiene la compresión en curso"""
        self.cancel_requested = True
        self.is_compressing = False
