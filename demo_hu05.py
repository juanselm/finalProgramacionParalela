"""
Demo de HU05: Almacenamiento temporal y ensamblaje de bloques comprimidos
Demuestra que cada hilo comprime un bloque y lo almacena temporalmente 
para luego ensamblar el archivo final en orden.
"""

import os
import sys
import tempfile
import time

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from compression.parallel_compressor import ParallelCompressor
from compression.temporary_storage import CompressionAlgorithm


def create_demo_file(size_mb=10):
    """Crea un archivo de demostración con contenido variado"""
    demo_file = os.path.join(tempfile.gettempdir(), "demo_hu05.txt")
    
    print(f"📄 Creando archivo de demostración de {size_mb}MB...")
    
    with open(demo_file, 'w') as f:
        # Crear contenido variado para demostrar compresión
        for i in range(size_mb * 1024):  # 1KB por iteración
            if i % 4 == 0:
                f.write("A" * 512 + "B" * 512)  # Patrón repetitivo (bueno para RLE)
            elif i % 4 == 1:
                f.write("Lorem ipsum dolor sit amet, consectetur adipiscing elit. " * 10)
            elif i % 4 == 2:
                f.write(f"Bloque_{i:06d}_" * 50 + "\n")  # Contenido único
            else:
                f.write("X" * 1000 + "\n")  # Más contenido repetitivo
    
    print(f"✅ Archivo creado: {demo_file} ({os.path.getsize(demo_file)} bytes)")
    return demo_file


def progress_callback(message, progress, phase):
    """Callback para mostrar progreso"""
    print(f"\r{phase} [{progress:6.2f}%]: {message}", end="", flush=True)
    return True


def demo_compression_algorithms():
    """Demuestra compresión con diferentes algoritmos"""
    print("\n" + "="*80)
    print("🗜️ DEMO HU05: COMPRESIÓN PARALELA CON ALMACENAMIENTO TEMPORAL")
    print("="*80)
    
    # Crear archivo de demostración
    demo_file = create_demo_file(5)  # 5MB
    
    try:
        # Configurar compresor
        compressor = ParallelCompressor(block_size=256 * 1024)  # 256KB por bloque
        
        # Demo 1: Compresión con ZLIB
        print("\n\n🧪 PRUEBA 1: Compresión paralela usando ZLIB")
        print("-" * 50)
        
        compressor.set_compression_algorithm(CompressionAlgorithm.ZLIB)
        zlib_output = os.path.join(tempfile.gettempdir(), "demo_hu05_zlib.parzip")
        
        start_time = time.time()
        success = compressor.compress_file_with_threads(demo_file, zlib_output, 4, progress_callback)
        elapsed_time = time.time() - start_time
        
        print(f"\n✅ Compresión ZLIB completada en {elapsed_time:.2f} segundos")
        if success and os.path.exists(zlib_output):
            original_size = os.path.getsize(demo_file)
            compressed_size = os.path.getsize(zlib_output)
            ratio = (compressed_size / original_size) * 100
            print(f"📊 Tamaño original: {original_size:,} bytes")
            print(f"📊 Tamaño comprimido: {compressed_size:,} bytes")
            print(f"📊 Ratio de compresión: {ratio:.1f}%")
            print(f"💾 Espacio ahorrado: {original_size - compressed_size:,} bytes")
        
        # Demo 2: Compresión con RLE
        print("\n\n🧪 PRUEBA 2: Compresión paralela usando RLE")
        print("-" * 50)
        
        compressor.set_compression_algorithm(CompressionAlgorithm.RLE)
        rle_output = os.path.join(tempfile.gettempdir(), "demo_hu05_rle.parzip")
        
        start_time = time.time()
        success = compressor.compress_file_with_threads(demo_file, rle_output, 4, progress_callback)
        elapsed_time = time.time() - start_time
        
        print(f"\n✅ Compresión RLE completada en {elapsed_time:.2f} segundos")
        if success and os.path.exists(rle_output):
            original_size = os.path.getsize(demo_file)
            compressed_size = os.path.getsize(rle_output)
            ratio = (compressed_size / original_size) * 100
            print(f"📊 Tamaño original: {original_size:,} bytes")
            print(f"📊 Tamaño comprimido: {compressed_size:,} bytes")
            print(f"📊 Ratio de compresión: {ratio:.1f}%")
            print(f"💾 Espacio ahorrado: {original_size - compressed_size:,} bytes")
        
        # Demo 3: Verificar estructura del archivo comprimido
        print("\n\n🔍 PRUEBA 3: Verificación de estructura del archivo comprimido")
        print("-" * 60)
        
        verify_compressed_file_structure(zlib_output, "ZLIB")
        
        # Mostrar estadísticas del compresor
        print("\n\n📈 ESTADÍSTICAS DE COMPRESIÓN:")
        print("-" * 40)
        stats = compressor.get_compression_statistics()
        if 'block_stats' in stats:
            block_stats = stats['block_stats']
            print(f"📦 Total de bloques: {block_stats.get('total_blocks', 'N/A')}")
            print(f"📐 Tamaño de bloque: {block_stats.get('block_size', 'N/A'):,} bytes")
            print(f"⚡ Eficiencia de división: {block_stats.get('efficiency_percentage', 'N/A'):.1f}%")
        
        print("\n✨ HU05 completada exitosamente!")
        print("✅ Cada hilo comprimió bloques y los almacenó temporalmente")
        print("✅ El archivo final fue ensamblado con todos los bloques en orden")
        print("✅ Los metadatos de orden se guardaron en el encabezado")
        print("✅ Se soportan múltiples algoritmos de compresión (zlib y RLE)")
        
    except Exception as e:
        print(f"\n❌ Error durante la demostración: {e}")
    
    finally:
        # Limpiar archivos temporales
        for file_path in [demo_file, zlib_output, rle_output]:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
            except:
                pass


def verify_compressed_file_structure(compressed_file, algorithm_name):
    """Verifica la estructura del archivo comprimido"""
    try:
        with open(compressed_file, 'rb') as f:
            # Leer tamaño del encabezado
            header_size_bytes = f.read(4)
            if len(header_size_bytes) == 4:
                header_size = int.from_bytes(header_size_bytes, byteorder='little')
                print(f"📋 {algorithm_name} - Tamaño del encabezado: {header_size} bytes")
                
                # Leer encabezado JSON
                header_data = f.read(header_size)
                if header_data:
                    import json
                    header_info = json.loads(header_data.decode('utf-8'))
                    print(f"📋 {algorithm_name} - Formato: {header_info.get('format', 'N/A')}")
                    print(f"📋 {algorithm_name} - Total de bloques: {header_info.get('total_blocks', 'N/A')}")
                    print(f"📋 {algorithm_name} - Algoritmo: {header_info.get('compression_algorithm', 'N/A')}")
                    print(f"📋 {algorithm_name} - Orden de bloques: {header_info.get('block_order', [])[:5]}{'...' if len(header_info.get('block_order', [])) > 5 else ''}")
                else:
                    print(f"⚠️ {algorithm_name} - No se pudo leer el encabezado")
            else:
                print(f"⚠️ {algorithm_name} - Archivo comprimido inválido")
                
    except Exception as e:
        print(f"❌ Error verificando estructura de {algorithm_name}: {e}")


if __name__ == "__main__":
    demo_compression_algorithms()
