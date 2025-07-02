"""
Módulo de compresión paralela
HU03: Compresión paralela con progreso visual
"""

import threading
import time
import zlib
from pathlib import Path


class ParallelCompressor:
    """Clase para manejar la compresión paralela de archivos"""
    
    def __init__(self, config, progress_callback=None):
        self.config = config
        self.progress_callback = progress_callback
        self.is_compressing = False
        self.compression_results = []
    
    def compress_file(self, input_file, output_file):
        """Comprime un archivo usando múltiples hilos"""
        try:
            self.is_compressing = True
            
            # Leer archivo y dividir en bloques
            blocks = self._split_file_into_blocks(input_file)
            
            # Comprimir bloques en paralelo
            compressed_blocks = self._compress_blocks_parallel(blocks)
            
            # Escribir archivo comprimido
            self._write_compressed_file(compressed_blocks, output_file)
            
            self.is_compressing = False
            return True
            
        except Exception as e:
            self.is_compressing = False
            raise e
    
    def _split_file_into_blocks(self, file_path):
        """Divide el archivo en bloques"""
        if self.progress_callback:
            self.progress_callback("Dividiendo archivo en bloques...", 10)
        
        # Convertir tamaño de bloque a bytes
        block_size_bytes = self._parse_block_size(self.config['block_size'])
        
        blocks = []
        with open(file_path, 'rb') as f:
            block_id = 0
            while True:
                data = f.read(block_size_bytes)
                if not data:
                    break
                blocks.append({
                    'id': block_id,
                    'data': data,
                    'size': len(data)
                })
                block_id += 1
        
        return blocks
    
    def _compress_blocks_parallel(self, blocks):
        """Comprime los bloques usando múltiples hilos"""
        if self.progress_callback:
            self.progress_callback("Comprimiendo bloques...", 30)
        
        compressed_blocks = [None] * len(blocks)
        threads = []
        
        # Dividir bloques entre hilos
        blocks_per_thread = len(blocks) // self.config['threads']
        
        for thread_id in range(self.config['threads']):
            start_idx = thread_id * blocks_per_thread
            if thread_id == self.config['threads'] - 1:
                end_idx = len(blocks)  # Último hilo toma los bloques restantes
            else:
                end_idx = (thread_id + 1) * blocks_per_thread
            
            thread_blocks = blocks[start_idx:end_idx]
            
            thread = threading.Thread(
                target=self._compress_thread_worker,
                args=(thread_blocks, compressed_blocks, start_idx)
            )
            threads.append(thread)
            thread.start()
        
        # Esperar a que terminen todos los hilos
        for thread in threads:
            thread.join()
        
        return compressed_blocks
    
    def _compress_thread_worker(self, blocks, result_array, start_idx):
        """Worker function para comprimir bloques en un hilo"""
        for i, block in enumerate(blocks):
            try:
                # Simular compresión (placeholder)
                if self.config['algorithm'] == 'zlib':
                    compressed_data = zlib.compress(block['data'])
                else:
                    # Placeholder para otros algoritmos
                    compressed_data = zlib.compress(block['data'])
                
                result_array[start_idx + i] = {
                    'id': block['id'],
                    'compressed_data': compressed_data,
                    'original_size': block['size'],
                    'compressed_size': len(compressed_data)
                }
                
                # Simular tiempo de procesamiento
                time.sleep(0.01)
                
            except Exception as e:
                print(f"Error comprimiendo bloque {block['id']}: {e}")
    
    def _write_compressed_file(self, compressed_blocks, output_file):
        """Escribe el archivo comprimido"""
        if self.progress_callback:
            self.progress_callback("Escribiendo archivo comprimido...", 80)
        
        with open(output_file, 'wb') as f:
            # Escribir header con metadatos
            header = {
                'blocks_count': len(compressed_blocks),
                'algorithm': self.config['algorithm'],
                'block_size': self.config['block_size']
            }
            
            # Placeholder: escribir header simple
            f.write(f"PARZIP_HEADER:{len(compressed_blocks)}\n".encode())
            
            # Escribir bloques comprimidos
            for block in compressed_blocks:
                if block:  # Verificar que el bloque no sea None
                    f.write(block['compressed_data'])
        
        if self.progress_callback:
            self.progress_callback("Compresión completada", 100)
    
    def _parse_block_size(self, size_str):
        """Convierte string de tamaño a bytes"""
        size_map = {
            'KB': 1024,
            'MB': 1024 * 1024,
            'GB': 1024 * 1024 * 1024
        }
        
        for unit, multiplier in size_map.items():
            if size_str.endswith(unit):
                number = int(size_str[:-len(unit)])
                return number * multiplier
        
        return int(size_str)  # Asumir bytes si no hay unidad
    
    def stop_compression(self):
        """Detiene la compresión en curso"""
        self.is_compressing = False
