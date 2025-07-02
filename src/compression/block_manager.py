"""
HU04: División de archivos en bloques de tamaño fijo
Módulo especializado para partición y gestión de bloques
"""

import os
import math
from pathlib import Path
from typing import List, Dict, Any, Optional, Callable


class FileBlockManager:
    """
    Clase especializada para dividir archivos en bloques de tamaño fijo
    HU04: Como desarrollador, quiero dividir el archivo de entrada en bloques de tamaño fijo
    """
    
    # Configuración de tamaños de bloque
    DEFAULT_BLOCK_SIZE = 1024 * 1024  # 1MB por defecto
    MIN_BLOCK_SIZE = 64 * 1024        # 64KB mínimo
    MAX_BLOCK_SIZE = 16 * 1024 * 1024 # 16MB máximo
    
    def __init__(self, block_size: int = None):
        """
        Inicializa el administrador de bloques
        
        Args:
            block_size: Tamaño de bloque en bytes (por defecto 1MB)
        """
        self.block_size = self._validate_block_size(block_size or self.DEFAULT_BLOCK_SIZE)
        self.blocks_info = []
        self.total_blocks = 0
        self.total_file_size = 0
        
    def _validate_block_size(self, size: int) -> int:
        """
        Valida que el tamaño de bloque esté dentro de los límites permitidos
        
        Args:
            size: Tamaño propuesto en bytes
            
        Returns:
            Tamaño validado
            
        Raises:
            ValueError: Si el tamaño está fuera de los límites
        """
        if not isinstance(size, int) or size <= 0:
            raise ValueError("El tamaño de bloque debe ser un entero positivo")
            
        if size < self.MIN_BLOCK_SIZE:
            raise ValueError(f"El tamaño de bloque no puede ser menor a {self.MIN_BLOCK_SIZE} bytes ({self.MIN_BLOCK_SIZE // 1024}KB)")
            
        if size > self.MAX_BLOCK_SIZE:
            raise ValueError(f"El tamaño de bloque no puede ser mayor a {self.MAX_BLOCK_SIZE} bytes ({self.MAX_BLOCK_SIZE // (1024*1024)}MB)")
            
        return size
    
    def analyze_file(self, file_path: str) -> Dict[str, Any]:
        """
        Analiza un archivo y calcula información de partición
        
        Args:
            file_path: Ruta al archivo a analizar
            
        Returns:
            Diccionario con información de partición
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"El archivo no existe: {file_path}")
            
        file_stat = os.stat(file_path)
        self.total_file_size = file_stat.st_size
        
        if self.total_file_size == 0:
            raise ValueError("El archivo está vacío")
        
        # Calcular número de bloques necesarios
        self.total_blocks = math.ceil(self.total_file_size / self.block_size)
        
        # Calcular tamaño del último bloque
        last_block_size = self.total_file_size % self.block_size
        if last_block_size == 0:
            last_block_size = self.block_size
            
        analysis = {
            'file_path': file_path,
            'file_size': self.total_file_size,
            'block_size': self.block_size,
            'total_blocks': self.total_blocks,
            'last_block_size': last_block_size,
            'efficiency': (self.total_file_size / (self.total_blocks * self.block_size)) * 100,
            'estimated_memory_usage': self.total_blocks * self.block_size
        }
        
        return analysis
    
    def split_file_into_blocks(self, file_path: str, progress_callback: Optional[Callable] = None) -> List[Dict[str, Any]]:
        """
        Divide un archivo en bloques de tamaño fijo
        
        Args:
            file_path: Ruta al archivo a dividir
            progress_callback: Función de callback para reportar progreso
            
        Returns:
            Lista de bloques con sus datos y metadatos
        """
        # Analizar archivo primero
        analysis = self.analyze_file(file_path)
        
        if progress_callback:
            progress_callback(f"Iniciando división en {self.total_blocks} bloques", 0, "🔪 División")
        
        blocks = []
        bytes_read = 0
        
        try:
            with open(file_path, 'rb') as file:
                for block_id in range(self.total_blocks):
                    # Determinar tamaño del bloque actual
                    if block_id == self.total_blocks - 1:
                        # Último bloque puede ser más pequeño
                        current_block_size = analysis['last_block_size']
                    else:
                        current_block_size = self.block_size
                    
                    # Leer datos del bloque
                    data = file.read(current_block_size)
                    
                    if not data:
                        break  # Fin de archivo inesperado
                    
                    # Validar que se leyó la cantidad esperada
                    if len(data) != current_block_size:
                        if block_id != self.total_blocks - 1:
                            # Si no es el último bloque, esto es un error
                            raise IOError(f"Error de lectura en bloque {block_id}: esperado {current_block_size} bytes, leído {len(data)} bytes")
                    
                    # Crear información del bloque
                    block_info = {
                        'id': block_id,
                        'data': data,
                        'size': len(data),
                        'start_offset': bytes_read,
                        'end_offset': bytes_read + len(data) - 1,
                        'is_last_block': block_id == self.total_blocks - 1,
                        'checksum': self._calculate_checksum(data)
                    }
                    
                    blocks.append(block_info)
                    bytes_read += len(data)
                    
                    # Reportar progreso
                    if progress_callback:
                        progress = (block_id + 1) / self.total_blocks * 100
                        if not progress_callback(
                            f"Leyendo bloque {block_id + 1}/{self.total_blocks} ({len(data)} bytes)", 
                            progress, 
                            "📖 Lectura"
                        ):
                            # Callback indica cancelación
                            break
        
        except Exception as e:
            raise IOError(f"Error durante la división del archivo: {str(e)}")
        
        # Validar integridad de la división
        self._validate_block_integrity(blocks, analysis)
        
        self.blocks_info = blocks
        
        if progress_callback:
            progress_callback(f"División completada: {len(blocks)} bloques", 100, "✅ División completa")
        
        return blocks
    
    def _calculate_checksum(self, data: bytes) -> int:
        """
        Calcula un checksum simple para un bloque de datos
        
        Args:
            data: Datos del bloque
            
        Returns:
            Checksum del bloque
        """
        return hash(data) & 0xFFFFFFFF  # Usar solo 32 bits
    
    def _validate_block_integrity(self, blocks: List[Dict[str, Any]], analysis: Dict[str, Any]) -> None:
        """
        Valida que la división en bloques sea correcta
        
        Args:
            blocks: Lista de bloques creados
            analysis: Información de análisis del archivo
            
        Raises:
            ValueError: Si hay problemas de integridad
        """
        if len(blocks) != analysis['total_blocks']:
            raise ValueError(f"Número incorrecto de bloques: esperado {analysis['total_blocks']}, obtenido {len(blocks)}")
        
        total_size = sum(block['size'] for block in blocks)
        if total_size != analysis['file_size']:
            raise ValueError(f"Tamaño total incorrecto: esperado {analysis['file_size']}, obtenido {total_size}")
        
        # Validar continuidad de offsets
        expected_offset = 0
        for i, block in enumerate(blocks):
            if block['start_offset'] != expected_offset:
                raise ValueError(f"Offset incorrecto en bloque {i}: esperado {expected_offset}, obtenido {block['start_offset']}")
            expected_offset = block['end_offset'] + 1
        
        # Validar que el último bloque tiene el tamaño correcto
        if blocks and blocks[-1]['size'] != analysis['last_block_size']:
            raise ValueError(f"Tamaño incorrecto del último bloque: esperado {analysis['last_block_size']}, obtenido {blocks[-1]['size']}")
    
    def get_block_distribution_for_threads(self, num_threads: int) -> List[List[int]]:
        """
        Distribuye los bloques entre el número especificado de hilos
        
        Args:
            num_threads: Número de hilos disponibles
            
        Returns:
            Lista de listas, cada una contiene los IDs de bloques para un hilo
        """
        if num_threads <= 0:
            raise ValueError("El número de hilos debe ser positivo")
        
        if not self.blocks_info:
            raise ValueError("No hay bloques disponibles. Ejecute split_file_into_blocks primero.")
        
        # Distribuir bloques de manera equitativa
        blocks_per_thread = len(self.blocks_info) // num_threads
        remaining_blocks = len(self.blocks_info) % num_threads
        
        distribution = []
        current_block = 0
        
        for thread_id in range(num_threads):
            # Calcular cuántos bloques asignar a este hilo
            thread_blocks = blocks_per_thread
            if thread_id < remaining_blocks:
                thread_blocks += 1  # Distribuir bloques restantes en los primeros hilos
            
            # Asignar bloques al hilo
            thread_block_ids = list(range(current_block, current_block + thread_blocks))
            distribution.append(thread_block_ids)
            current_block += thread_blocks
        
        return distribution
    
    def get_block_by_id(self, block_id: int) -> Optional[Dict[str, Any]]:
        """
        Obtiene un bloque específico por su ID
        
        Args:
            block_id: ID del bloque a obtener
            
        Returns:
            Información del bloque o None si no existe
        """
        if not self.blocks_info or block_id >= len(self.blocks_info):
            return None
        
        return self.blocks_info[block_id]
    
    def get_blocks_for_thread(self, thread_id: int, distribution: List[List[int]]) -> List[Dict[str, Any]]:
        """
        Obtiene los bloques asignados a un hilo específico
        
        Args:
            thread_id: ID del hilo
            distribution: Distribución de bloques obtenida de get_block_distribution_for_threads
            
        Returns:
            Lista de bloques para el hilo
        """
        if thread_id >= len(distribution):
            return []
        
        blocks = []
        for block_id in distribution[thread_id]:
            block = self.get_block_by_id(block_id)
            if block:
                blocks.append(block)
        
        return blocks
    
    def get_statistics(self) -> Dict[str, Any]:
        """
        Obtiene estadísticas sobre la división en bloques
        
        Returns:
            Diccionario con estadísticas
        """
        if not self.blocks_info:
            return {}
        
        sizes = [block['size'] for block in self.blocks_info]
        
        return {
            'total_blocks': len(self.blocks_info),
            'total_size': sum(sizes),
            'block_size_configured': self.block_size,
            'average_block_size': sum(sizes) / len(sizes),
            'min_block_size': min(sizes),
            'max_block_size': max(sizes),
            'size_variance': max(sizes) - min(sizes),
            'memory_efficiency': (sum(sizes) / (len(sizes) * self.block_size)) * 100
        }
    
    @classmethod
    def calculate_optimal_block_size(cls, file_size: int, num_threads: int, target_blocks_per_thread: int = 2) -> int:
        """
        Calcula un tamaño de bloque óptimo basado en el tamaño del archivo y número de hilos
        
        Args:
            file_size: Tamaño del archivo en bytes
            num_threads: Número de hilos disponibles
            target_blocks_per_thread: Número objetivo de bloques por hilo
            
        Returns:
            Tamaño de bloque óptimo
        """
        if file_size <= 0 or num_threads <= 0:
            return cls.DEFAULT_BLOCK_SIZE
        
        # Calcular tamaño ideal basado en distribución uniforme
        target_blocks = num_threads * target_blocks_per_thread
        optimal_size = file_size // target_blocks
        
        # Ajustar a límites permitidos
        optimal_size = max(optimal_size, cls.MIN_BLOCK_SIZE)
        optimal_size = min(optimal_size, cls.MAX_BLOCK_SIZE)
        
        # Redondear a múltiplo de 1KB para eficiencia
        optimal_size = (optimal_size // 1024) * 1024
        
        return optimal_size or cls.DEFAULT_BLOCK_SIZE
