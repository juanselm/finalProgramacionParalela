"""
HU05: Almacenamiento temporal y ensamblaje de bloques comprimidos
Módulo para gestionar el almacenamiento temporal de bloques comprimidos 
y su posterior ensamblaje en el archivo final
"""

import os
import tempfile
import json
import threading
import zlib
import hashlib
import time
from typing import List, Dict, Any, Optional
from pathlib import Path


class TemporaryBlockStorage:
    """
    HU05: Gestiona el almacenamiento temporal de bloques comprimidos
    Cada hilo comprime un bloque y lo almacena temporalmente para luego
    ensamblar el archivo final con todos los bloques en orden.
    """
    
    def __init__(self, temp_dir: Optional[str] = None):
        """
        Inicializa el almacenamiento temporal
        
        Args:
            temp_dir: Directorio temporal personalizado. Si es None, usa el sistema.
        """
        self.temp_dir = temp_dir or tempfile.mkdtemp(prefix="parcomp_")
        self.metadata_file = os.path.join(self.temp_dir, "metadata.json")
        self.blocks_dir = os.path.join(self.temp_dir, "blocks")
        self.lock = threading.Lock()
        self.metadata = {
            "file_info": {},
            "blocks": {},
            "compression_algorithm": "zlib",
            "format_version": "1.0"
        }
        
        # Crear estructura de directorios
        os.makedirs(self.blocks_dir, exist_ok=True)
        self._save_metadata()
    
    def store_compressed_block(self, block_id: int, compressed_data: bytes, 
                             original_size: int, compression_ratio: float,
                             thread_id: int, checksum: str) -> str:
        """
        HU05: Almacena un bloque comprimido en el almacenamiento temporal
        
        Args:
            block_id: ID único del bloque
            compressed_data: Datos comprimidos del bloque
            original_size: Tamaño original del bloque
            compression_ratio: Ratio de compresión alcanzado
            thread_id: ID del hilo que procesó el bloque
            checksum: Checksum del bloque original para validación
            
        Returns:
            str: Ruta del archivo temporal donde se almacenó el bloque
        """
        block_filename = f"block_{block_id:06d}.tmp"
        block_path = os.path.join(self.blocks_dir, block_filename)
        
        # Escribir bloque comprimido a archivo temporal
        with open(block_path, 'wb') as f:
            f.write(compressed_data)
        
        # Actualizar metadata de forma thread-safe
        with self.lock:
            self.metadata["blocks"][str(block_id)] = {
                "id": block_id,
                "filename": block_filename,
                "path": block_path,
                "original_size": original_size,
                "compressed_size": len(compressed_data),
                "compression_ratio": compression_ratio,
                "thread_id": thread_id,
                "original_checksum": checksum,
                "compressed_checksum": self._calculate_checksum(compressed_data),
                "status": "completed"
            }
            self._save_metadata()
        
        return block_path
    
    def get_block_count(self) -> int:
        """Obtiene el número de bloques almacenados"""
        with self.lock:
            return len(self.metadata["blocks"])
    
    def get_stored_blocks(self) -> List[Dict[str, Any]]:
        """
        HU05: Obtiene la lista de bloques almacenados ordenados por ID
        
        Returns:
            List[Dict]: Lista de bloques ordenados para ensamblaje
        """
        with self.lock:
            blocks = list(self.metadata["blocks"].values())
            # Ordenar por ID para mantener el orden correcto
            blocks.sort(key=lambda x: x["id"])
            return blocks
    
    def validate_blocks_integrity(self) -> tuple[bool, List[str]]:
        """
        HU05: Valida la integridad de todos los bloques almacenados
        
        Returns:
            tuple: (es_válido, lista_de_errores)
        """
        errors = []
        blocks = self.get_stored_blocks()
        
        for block_info in blocks:
            block_path = block_info["path"]
            
            # Verificar que el archivo existe
            if not os.path.exists(block_path):
                errors.append(f"Bloque {block_info['id']}: archivo no encontrado")
                continue
            
            # Verificar tamaño del archivo
            actual_size = os.path.getsize(block_path)
            expected_size = block_info["compressed_size"]
            if actual_size != expected_size:
                errors.append(f"Bloque {block_info['id']}: tamaño incorrecto")
                continue
            
            # Verificar checksum del archivo comprimido
            with open(block_path, 'rb') as f:
                data = f.read()
                actual_checksum = self._calculate_checksum(data)
                expected_checksum = block_info["compressed_checksum"]
                if actual_checksum != expected_checksum:
                    errors.append(f"Bloque {block_info['id']}: checksum incorrecto")
        
        return len(errors) == 0, errors
    
    def assemble_final_file(self, output_path: str, 
                          progress_callback=None) -> bool:
        """
        HU05: Ensambla el archivo final a partir de los bloques comprimidos almacenados
        
        Args:
            output_path: Ruta donde crear el archivo final
            progress_callback: Callback para reportar progreso
            
        Returns:
            bool: True si el ensamblaje fue exitoso
        """
        try:
            # Validar integridad antes del ensamblaje
            is_valid, errors = self.validate_blocks_integrity()
            if not is_valid:
                raise ValueError(f"Errores de integridad: {errors}")
            
            blocks = self.get_stored_blocks()
            total_blocks = len(blocks)
            
            if progress_callback:
                progress_callback("Iniciando ensamblaje de archivo final...", 0, "🔧 Ensamblaje")
            
            with open(output_path, 'wb') as output_file:
                # HU05: Escribir encabezado con metadatos de orden
                header = self._create_file_header(blocks)
                output_file.write(header)
                
                # Escribir bloques comprimidos en orden
                for i, block_info in enumerate(blocks):
                    block_path = block_info["path"]
                    
                    # Leer bloque comprimido
                    with open(block_path, 'rb') as block_file:
                        compressed_data = block_file.read()
                    
                    # Escribir al archivo final
                    output_file.write(compressed_data)
                    
                    # Reportar progreso
                    if progress_callback:
                        progress = (i + 1) / total_blocks * 100
                        status = f"Ensamblando bloque {i + 1}/{total_blocks}"
                        if not progress_callback(status, progress, "🔧 Ensamblaje"):
                            return False
            
            if progress_callback:
                progress_callback("Archivo final ensamblado exitosamente", 100, "✅ Completado")
            
            return True
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error en ensamblaje: {str(e)}", 0, "❌ Error")
            return False
    
    def _create_file_header(self, blocks: List[Dict[str, Any]]) -> bytes:
        """
        HU05: Crea el encabezado del archivo con metadatos de orden
        
        Args:
            blocks: Lista de bloques ordenados
            
        Returns:
            bytes: Encabezado binario con metadatos
        """
        # Crear estructura de metadatos para el encabezado
        header_data = {
            "format": "PARCOMP_V1",
            "compression": "zlib",
            "total_blocks": len(blocks),
            "blocks_info": [
                {
                    "id": block["id"],
                    "original_size": block["original_size"],
                    "compressed_size": block["compressed_size"],
                    "compression_ratio": block["compression_ratio"],
                    "original_checksum": block["original_checksum"]
                }
                for block in blocks
            ]
        }
        
        # Serializar metadatos a JSON
        header_json = json.dumps(header_data, indent=None).encode('utf-8')
        
        # Crear encabezado con longitud prefijada
        header_length = len(header_json)
        header = b"PARCOMP1" + header_length.to_bytes(4, byteorder='little') + header_json
        
        return header
    
    def _calculate_checksum(self, data: bytes) -> str:
        """Calcula checksum SHA-256 para validación"""
        return hashlib.sha256(data).hexdigest()
    
    def _save_metadata(self):
        """Guarda metadatos en archivo JSON"""
        with open(self.metadata_file, 'w') as f:
            json.dump(self.metadata, f, indent=2)
    
    def cleanup(self):
        """
        HU05: Limpia archivos temporales después del ensamblaje
        """
        try:
            # Eliminar archivos de bloques
            for filename in os.listdir(self.blocks_dir):
                file_path = os.path.join(self.blocks_dir, filename)
                if os.path.isfile(file_path):
                    os.remove(file_path)
            
            # Eliminar directorio de bloques
            os.rmdir(self.blocks_dir)
            
            # Eliminar archivo de metadatos
            if os.path.exists(self.metadata_file):
                os.remove(self.metadata_file)
            
            # Eliminar directorio temporal principal
            os.rmdir(self.temp_dir)
            
        except Exception as e:
            print(f"Advertencia: No se pudo limpiar completamente el directorio temporal: {e}")
    
    def get_compression_statistics(self) -> Dict[str, Any]:
        """
        HU05: Obtiene estadísticas de compresión del almacenamiento temporal
        """
        with self.lock:
            blocks = list(self.metadata["blocks"].values())
            
            if not blocks:
                return {"error": "No hay bloques almacenados"}
            
            total_original = sum(block["original_size"] for block in blocks)
            total_compressed = sum(block["compressed_size"] for block in blocks)
            
            return {
                "total_blocks": len(blocks),
                "total_original_size": total_original,
                "total_compressed_size": total_compressed,
                "overall_compression_ratio": (total_compressed / total_original * 100) if total_original > 0 else 0,
                "space_saved": total_original - total_compressed,
                "space_saved_percentage": ((total_original - total_compressed) / total_original * 100) if total_original > 0 else 0
            }
    
    def set_file_info(self, input_file: str, output_file: str, total_blocks: int):
        """
        HU05: Configura la información del archivo para el almacenamiento temporal
        """
        with self.lock:
            self.metadata["file_info"] = {
                "input_file": input_file,
                "output_file": output_file,
                "total_blocks": total_blocks,
                "timestamp": time.time()
            }
            self._save_metadata()
    
    def get_file_info(self) -> Dict[str, Any]:
        """
        HU05: Obtiene la información del archivo almacenada
        """
        with self.lock:
            return self.metadata["file_info"].copy()
    
    def retrieve_block_data(self, block_id: int) -> bytes:
        """
        HU05: Recupera los datos comprimidos de un bloque específico
        """
        with self.lock:
            if str(block_id) not in self.metadata["blocks"]:
                raise KeyError(f"Bloque {block_id} no encontrado")
            
            block_info = self.metadata["blocks"][str(block_id)]
            block_path = block_info["path"]
            
            with open(block_path, 'rb') as f:
                return f.read()
    
    def get_ordered_blocks_metadata(self) -> List[Dict[str, Any]]:
        """
        HU05: Obtiene los metadatos de bloques ordenados por ID para ensamblaje final
        """
        with self.lock:
            blocks = []
            for block_id_str, block_info in self.metadata["blocks"].items():
                blocks.append(block_info.copy())
            
            # Ordenar por ID de bloque
            blocks.sort(key=lambda x: x["id"])
            return blocks


class RLECompressor:
    """
    HU05: Implementación de compresión RLE (Run-Length Encoding)
    Alternativa a zlib para casos específicos
    """
    
    @staticmethod
    def compress(data: bytes) -> bytes:
        """
        Comprime datos usando RLE
        
        Args:
            data: Datos a comprimir
            
        Returns:
            bytes: Datos comprimidos
        """
        if not data:
            return b''
        
        compressed = bytearray()
        i = 0
        while i < len(data):
            current_byte = data[i]
            count = 1
            
            # Contar bytes consecutivos iguales (máximo 255)
            while i + count < len(data) and data[i + count] == current_byte and count < 255:
                count += 1
            
            # Escribir count y byte
            compressed.append(count)
            compressed.append(current_byte)
            i += count
        
        return bytes(compressed)
    
    @staticmethod
    def decompress(data: bytes) -> bytes:
        """
        Descomprime datos RLE
        
        Args:
            data: Datos comprimidos
            
        Returns:
            bytes: Datos originales
        """
        if not data or len(data) % 2 != 0:
            return b''
        
        decompressed = bytearray()
        for i in range(0, len(data), 2):
            count = data[i]
            byte_value = data[i + 1]
            decompressed.extend([byte_value] * count)
        
        return bytes(decompressed)


class CompressionAlgorithm:
    """
    HU05: Enumeración de algoritmos de compresión disponibles
    """
    ZLIB = "zlib"
    RLE = "rle"
    
    @staticmethod
    def compress(data: bytes, algorithm: str = ZLIB, level: int = 6) -> bytes:
        """
        Comprime datos usando el algoritmo especificado
        
        Args:
            data: Datos a comprimir
            algorithm: Algoritmo a usar (zlib o rle)
            level: Nivel de compresión (solo para zlib)
            
        Returns:
            bytes: Datos comprimidos
        """
        if algorithm == CompressionAlgorithm.ZLIB:
            return zlib.compress(data, level)
        elif algorithm == CompressionAlgorithm.RLE:
            return RLECompressor.compress(data)
        else:
            raise ValueError(f"Algoritmo de compresión no soportado: {algorithm}")
    
    @staticmethod
    def decompress(data: bytes, algorithm: str = ZLIB) -> bytes:
        """
        Descomprime datos usando el algoritmo especificado
        
        Args:
            data: Datos comprimidos
            algorithm: Algoritmo usado para comprimir
            
        Returns:
            bytes: Datos originales
        """
        if algorithm == CompressionAlgorithm.ZLIB:
            return zlib.decompress(data)
        elif algorithm == CompressionAlgorithm.RLE:
            return RLECompressor.decompress(data)
        else:
            raise ValueError(f"Algoritmo de compresión no soportado: {algorithm}")
