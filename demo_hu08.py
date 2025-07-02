"""
Demo para HU08: Descompresión de archivos .pz
Demuestra las capacidades de descompresión de la aplicación
"""

import sys
import os
import tempfile
import shutil

# Agregar el directorio src al path
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from compression.parallel_compressor import ParallelCompressor
from gui.error_handler import ErrorHandler, ErrorType, ErrorSeverity


def create_test_files(temp_dir):
    """Crea archivos de prueba para el demo"""
    files = {}
    
    # Archivo de texto simple
    text_content = """Este es un archivo de prueba para HU08.
La funcionalidad de descompresión debe recuperar este contenido exactamente.
Línea 3 de contenido.
Línea 4 con más texto.
Final del archivo de prueba."""
    
    text_file = os.path.join(temp_dir, "demo_text.txt")
    with open(text_file, 'w', encoding='utf-8') as f:
        f.write(text_content)
    files['text'] = text_file
    
    # Archivo binario (simulado)
    binary_content = bytes(range(256)) * 10  # Datos binarios variados
    binary_file = os.path.join(temp_dir, "demo_binary.dat")
    with open(binary_file, 'wb') as f:
        f.write(binary_content)
    files['binary'] = binary_file
    
    # Archivo más grande
    large_content = "Contenido repetido para archivo grande.\n" * 500
    large_file = os.path.join(temp_dir, "demo_large.txt")
    with open(large_file, 'w', encoding='utf-8') as f:
        f.write(large_content)
    files['large'] = large_file
    
    return files


def demo_basic_decompression():
    """Demuestra descompresión básica"""
    print("1️⃣ Demostración de descompresión básica:")
    print("-" * 50)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        # Crear error handler y compresor
        error_handler = ErrorHandler(enable_logging=False)
        compressor = ParallelCompressor(error_handler=error_handler)
        
        # Crear archivo de prueba
        test_files = create_test_files(temp_dir)
        test_file = test_files['text']
        
        print(f"   📄 Archivo original: {os.path.basename(test_file)}")
        original_size = os.path.getsize(test_file)
        print(f"   📏 Tamaño original: {original_size} bytes")
        
        # Comprimir archivo
        compressed_file = os.path.join(temp_dir, "demo_compressed.pz")
        print(f"   🗜️ Comprimiendo a: {os.path.basename(compressed_file)}")
        
        compression_success = compressor.compress_file_with_threads(
            input_file=test_file,
            output_file=compressed_file,
            num_threads=2,
            progress_callback=None
        )
        
        if compression_success:
            compressed_size = os.path.getsize(compressed_file)
            ratio = (compressed_size / original_size) * 100
            print(f"   ✅ Compresión exitosa")
            print(f"   📏 Tamaño comprimido: {compressed_size} bytes ({ratio:.1f}% del original)")
        else:
            print(f"   ❌ Error en compresión")
            return
        
        # Descomprimir archivo
        decompressed_file = os.path.join(temp_dir, "demo_decompressed.txt")
        print(f"   📦 Descomprimiendo a: {os.path.basename(decompressed_file)}")
        
        decompression_success = compressor.decompress_file_with_threads(
            input_file=compressed_file,
            output_file=decompressed_file,
            num_threads=2,
            progress_callback=None
        )
        
        if decompression_success:
            decompressed_size = os.path.getsize(decompressed_file)
            print(f"   ✅ Descompresión exitosa")
            print(f"   📏 Tamaño descomprimido: {decompressed_size} bytes")
            
            # Verificar integridad
            with open(test_file, 'rb') as f:
                original_content = f.read()
            with open(decompressed_file, 'rb') as f:
                decompressed_content = f.read()
            
            if original_content == decompressed_content:
                print(f"   🎯 VERIFICACIÓN: Archivo recuperado es IDÉNTICO al original")
            else:
                print(f"   ❌ ERROR: Archivo recuperado NO coincide con el original")
        else:
            print(f"   ❌ Error en descompresión")
    
    finally:
        shutil.rmtree(temp_dir)
    
    print()


def demo_different_file_types():
    """Demuestra descompresión de diferentes tipos de archivo"""
    print("2️⃣ Descompresión de diferentes tipos de archivo:")
    print("-" * 50)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        error_handler = ErrorHandler(enable_logging=False)
        compressor = ParallelCompressor(error_handler=error_handler)
        
        test_files = create_test_files(temp_dir)
        
        for file_type, file_path in test_files.items():
            print(f"   📁 Procesando archivo {file_type}: {os.path.basename(file_path)}")
            
            # Comprimir
            compressed_file = os.path.join(temp_dir, f"{file_type}_compressed.pz")
            compression_success = compressor.compress_file_with_threads(
                input_file=file_path,
                output_file=compressed_file,
                num_threads=2
            )
            
            if not compression_success:
                print(f"      ❌ Error comprimiendo {file_type}")
                continue
            
            # Descomprimir
            decompressed_file = os.path.join(temp_dir, f"{file_type}_decompressed")
            decompression_success = compressor.decompress_file_with_threads(
                input_file=compressed_file,
                output_file=decompressed_file,
                num_threads=2
            )
            
            if decompression_success:
                # Verificar integridad
                with open(file_path, 'rb') as f:
                    original = f.read()
                with open(decompressed_file, 'rb') as f:
                    decompressed = f.read()
                
                if original == decompressed:
                    print(f"      ✅ {file_type.upper()}: Recuperación EXITOSA e IDÉNTICA")
                else:
                    print(f"      ❌ {file_type.upper()}: Error en recuperación")
            else:
                print(f"      ❌ {file_type.upper()}: Error en descompresión")
    
    finally:
        shutil.rmtree(temp_dir)
    
    print()


def demo_multithreaded_decompression():
    """Demuestra descompresión con diferentes números de hilos"""
    print("3️⃣ Descompresión con múltiples hilos:")
    print("-" * 50)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        error_handler = ErrorHandler(enable_logging=False)
        compressor = ParallelCompressor(error_handler=error_handler)
        
        # Crear archivo más grande para mejor demo de paralelismo
        test_files = create_test_files(temp_dir)
        large_file = test_files['large']
        
        # Comprimir una vez
        compressed_file = os.path.join(temp_dir, "multithreaded_test.pz")
        compressor.compress_file_with_threads(
            input_file=large_file,
            output_file=compressed_file,
            num_threads=4
        )
        
        print(f"   📄 Archivo comprimido: {os.path.basename(compressed_file)}")
        compressed_size = os.path.getsize(compressed_file)
        print(f"   📏 Tamaño: {compressed_size} bytes")
        
        # Probar con diferentes números de hilos
        thread_counts = [1, 2, 4]
        
        for num_threads in thread_counts:
            print(f"   🔄 Descomprimiendo con {num_threads} hilo(s):")
            
            decompressed_file = os.path.join(temp_dir, f"decompressed_{num_threads}t.txt")
            
            import time
            start_time = time.time()
            
            success = compressor.decompress_file_with_threads(
                input_file=compressed_file,
                output_file=decompressed_file,
                num_threads=num_threads
            )
            
            end_time = time.time()
            duration = end_time - start_time
            
            if success:
                print(f"      ✅ Exitosa en {duration:.2f} segundos")
                
                # Verificar integridad
                with open(large_file, 'rb') as f:
                    original = f.read()
                with open(decompressed_file, 'rb') as f:
                    decompressed = f.read()
                
                if original == decompressed:
                    print(f"      🎯 Integridad: VERIFICADA")
                else:
                    print(f"      ❌ Integridad: FALLO")
            else:
                print(f"      ❌ Falló en {duration:.2f} segundos")
    
    finally:
        shutil.rmtree(temp_dir)
    
    print()


def demo_error_handling():
    """Demuestra manejo de errores en descompresión"""
    print("4️⃣ Manejo de errores en descompresión:")
    print("-" * 50)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        error_handler = ErrorHandler(enable_logging=False)
        compressor = ParallelCompressor(error_handler=error_handler)
        
        # Test 1: Archivo inexistente
        print("   🔍 Test: Archivo .pz inexistente")
        result = compressor.decompress_file_with_threads(
            input_file=os.path.join(temp_dir, "nonexistent.pz"),
            output_file=os.path.join(temp_dir, "output.txt"),
            num_threads=2
        )
        print(f"      Resultado: {'❌ Error manejado correctamente' if not result else '⚠️ Inesperado'}")
        
        # Test 2: Archivo sin extensión .pz
        print("   🔍 Test: Archivo sin extensión .pz")
        normal_file = os.path.join(temp_dir, "normal.txt")
        with open(normal_file, 'w') as f:
            f.write("Not a compressed file")
        
        result = compressor.decompress_file_with_threads(
            input_file=normal_file,
            output_file=os.path.join(temp_dir, "output.txt"),
            num_threads=2
        )
        print(f"      Resultado: {'❌ Error manejado correctamente' if not result else '⚠️ Inesperado'}")
        
        # Test 3: Archivo .pz inválido
        print("   🔍 Test: Archivo .pz con formato inválido")
        fake_pz = os.path.join(temp_dir, "fake.pz")
        with open(fake_pz, 'wb') as f:
            f.write(b"This is not a real compressed file")
        
        result = compressor.decompress_file_with_threads(
            input_file=fake_pz,
            output_file=os.path.join(temp_dir, "output.txt"),
            num_threads=2
        )
        print(f"      Resultado: {'❌ Error manejado correctamente' if not result else '⚠️ Inesperado'}")
        
        # Mostrar errores registrados
        errors = error_handler.get_error_history()
        print(f"   📊 Errores registrados en el sistema: {len(errors)}")
        
        if errors:
            print("   📋 Tipos de errores capturados:")
            error_types = set(error['type'].value for error in errors)
            for error_type in error_types:
                print(f"      • {error_type}")
    
    finally:
        shutil.rmtree(temp_dir)
    
    print()


def demo_progress_tracking():
    """Demuestra seguimiento de progreso durante descompresión"""
    print("5️⃣ Seguimiento de progreso durante descompresión:")
    print("-" * 50)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        error_handler = ErrorHandler(enable_logging=False)
        compressor = ParallelCompressor(error_handler=error_handler)
        
        # Crear y comprimir archivo
        test_files = create_test_files(temp_dir)
        large_file = test_files['large']
        compressed_file = os.path.join(temp_dir, "progress_test.pz")
        
        compressor.compress_file_with_threads(
            input_file=large_file,
            output_file=compressed_file,
            num_threads=2
        )
        
        # Descomprimir con seguimiento de progreso
        print("   🔄 Iniciando descompresión con seguimiento de progreso:")
        
        progress_updates = []
        
        def progress_callback(message, progress, phase):
            progress_updates.append({
                'message': message,
                'progress': progress,
                'phase': phase
            })
            
            # Mostrar cada 20% de progreso o cambio de fase
            if len(progress_updates) == 1 or progress % 20 == 0 or progress == 100:
                print(f"      [{progress:3d}%] {phase}: {message}")
            
            return True  # Continuar
        
        decompressed_file = os.path.join(temp_dir, "progress_decompressed.txt")
        result = compressor.decompress_file_with_threads(
            input_file=compressed_file,
            output_file=decompressed_file,
            num_threads=2,
            progress_callback=progress_callback
        )
        
        if result:
            print(f"   ✅ Descompresión completada exitosamente")
            print(f"   📊 Total de actualizaciones de progreso: {len(progress_updates)}")
            
            # Mostrar fases detectadas
            phases = set(update['phase'] for update in progress_updates)
            print(f"   🔄 Fases del proceso:")
            for phase in sorted(phases):
                print(f"      • {phase}")
        else:
            print(f"   ❌ Error en descompresión con progreso")
    
    finally:
        shutil.rmtree(temp_dir)
    
    print()


def demo_header_information():
    """Demuestra lectura de información del encabezado de archivos .pz"""
    print("6️⃣ Lectura de información del encabezado:")
    print("-" * 50)
    
    temp_dir = tempfile.mkdtemp()
    
    try:
        error_handler = ErrorHandler(enable_logging=False)
        compressor = ParallelCompressor(error_handler=error_handler)
        
        # Crear diferentes archivos de prueba
        test_files = create_test_files(temp_dir)
        
        for file_type, file_path in test_files.items():
            print(f"   📄 Archivo: {os.path.basename(file_path)} ({file_type})")
            
            # Comprimir
            compressed_file = os.path.join(temp_dir, f"{file_type}_header.pz")
            compressor.compress_file_with_threads(
                input_file=file_path,
                output_file=compressed_file,
                num_threads=2
            )
            
            # Leer información del encabezado
            try:
                header_info = compressor._read_compressed_file_header(compressed_file)
                
                print(f"      🏷️ Nombre original: {header_info.get('original_filename', 'N/A')}")
                print(f"      📏 Tamaño original: {header_info.get('original_size', 0)} bytes")
                print(f"      🧱 Número de bloques: {header_info.get('block_count', 0)}")
                print(f"      🗜️ Algoritmo: {header_info.get('compression_algorithm', 'N/A')}")
                
                if 'compression_time' in header_info:
                    print(f"      ⏱️ Tiempo de compresión: {header_info['compression_time']:.2f}s")
                
                print()
                
            except Exception as e:
                print(f"      ❌ Error leyendo encabezado: {str(e)}")
                print()
    
    finally:
        shutil.rmtree(temp_dir)


def main():
    """Función principal del demo"""
    print("🚀 Iniciando Demo HU08 - Descompresión de Archivos .pz")
    print("=" * 70)
    print()
    
    try:
        # Ejecutar todas las demostraciones
        demo_basic_decompression()
        demo_different_file_types()
        demo_multithreaded_decompression()
        demo_error_handling()
        demo_progress_tracking()
        demo_header_information()
        
        print("🎉 RESUMEN FINAL:")
        print("-" * 50)
        print("✅ Descompresión básica de archivos .pz")
        print("✅ Soporte para múltiples tipos de archivo")
        print("✅ Descompresión paralela con múltiples hilos")
        print("✅ Manejo robusto de errores")
        print("✅ Seguimiento detallado de progreso")
        print("✅ Lectura de información de encabezados")
        print("✅ Verificación de integridad (archivo idéntico al original)")
        print()
        print("🏆 HU08 COMPLETADA: Descompresión de archivos .pz implementada exitosamente")
        print("🎯 CRITERIO CLAVE: El archivo recuperado es IDÉNTICO al original")
        
    except Exception as e:
        print(f"❌ Error en demo: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
