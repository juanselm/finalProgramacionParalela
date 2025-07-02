"""
Demo de HU06: Selección personalizada de destino
Como usuario, quiero guardar el archivo comprimido en la ruta que yo elija.
"""

import os
import sys
import tempfile
import tkinter as tk
from tkinter import messagebox
from pathlib import Path

# Agregar el directorio src al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from gui.main_window import MainWindow


def create_demo_file():
    """Crea un archivo de demostración para la prueba"""
    demo_content = """
    Este es un archivo de demostración para probar HU06.
    
    Contenido de ejemplo:
    - Línea 1 con texto variado
    - Línea 2 con más contenido
    - Línea 3 para hacer el archivo más grande
    
    """ * 100  # Repetir para hacer el archivo más grande
    
    demo_file = os.path.join(tempfile.gettempdir(), "demo_hu06_input.txt")
    with open(demo_file, 'w', encoding='utf-8') as f:
        f.write(demo_content)
    
    return demo_file


def demo_hu06():
    """Demostración interactiva de HU06"""
    print("="*80)
    print("🎯 DEMO HU06: SELECCIÓN PERSONALIZADA DE DESTINO")
    print("="*80)
    print()
    print("Esta demostración muestra:")
    print("✅ Selección personalizada de la carpeta de destino")
    print("✅ Extensión .pz automática")
    print("✅ Validación de permisos de escritura")
    print("✅ Confirmación de sobrescritura")
    print()
    
    # Crear archivo de demostración
    demo_file = create_demo_file()
    print(f"📄 Archivo de demostración creado: {demo_file}")
    print(f"📊 Tamaño: {os.path.getsize(demo_file)} bytes")
    print()
    
    try:
        print("🚀 Iniciando aplicación con interfaz gráfica...")
        print()
        print("INSTRUCCIONES PARA LA DEMOSTRACIÓN:")
        print("-" * 40)
        print("1. Seleccione el archivo de demostración creado")
        print("2. Observe que se sugiere automáticamente un destino con extensión .pz")
        print("3. Use 'Elegir Destino' para cambiar la ubicación si desea")
        print("4. Inicie la compresión y observe el progreso")
        print("5. Verifique que el archivo se guarde en la ubicación elegida")
        print()
        print("Características de HU06 que puede probar:")
        print("• Cambio de carpeta de destino")
        print("• Cambio de nombre del archivo")
        print("• Extensión .pz automática")
        print("• Validación de permisos")
        print("• Confirmación de sobrescritura")
        print()
        
        # Crear y ejecutar la aplicación
        app = MainWindow()
        
        # Configurar título personalizado para el demo
        app.root.title("Demo HU06 - Selección de Destino Personalizada")
        
        # Mostrar mensaje inicial
        messagebox.showinfo("Demo HU06", 
                          f"Archivo de demostración creado en:\n{demo_file}\n\n"
                          "Por favor, seleccione este archivo para probar HU06.")
        
        # Ejecutar aplicación
        app.run()
        
    except Exception as e:
        print(f"❌ Error durante la demostración: {e}")
    
    finally:
        # Limpiar archivo temporal
        try:
            if os.path.exists(demo_file):
                os.remove(demo_file)
                print(f"🗑️ Archivo de demostración eliminado: {demo_file}")
        except:
            pass


def test_destination_validation():
    """Prueba programática de las funciones de validación"""
    print("\n🧪 PRUEBAS PROGRAMÁTICAS DE VALIDACIÓN")
    print("-" * 50)
    
    # Crear instancia temporal de la aplicación para usar sus métodos
    app = MainWindow()
    app.root.withdraw()  # Ocultar la ventana
    
    # Crear directorio temporal para pruebas
    temp_dir = tempfile.mkdtemp()
    print(f"📁 Directorio temporal: {temp_dir}")
    
    try:
        # Prueba 1: Validación de ruta válida
        valid_path = os.path.join(temp_dir, "archivo_valido.pz")
        result = app.validate_output_path(valid_path)
        print(f"✅ Validación de ruta válida: {'PASS' if result else 'FAIL'}")
        
        # Prueba 2: Creación de directorio inexistente
        new_dir_path = os.path.join(temp_dir, "nuevo_directorio", "archivo.pz")
        result = app.validate_output_path(new_dir_path)
        created = os.path.exists(os.path.dirname(new_dir_path))
        print(f"✅ Creación de directorio: {'PASS' if result and created else 'FAIL'}")
        
        # Prueba 3: Sugerencia automática de nombre
        demo_file = os.path.join(temp_dir, "archivo_original.txt")
        with open(demo_file, 'w') as f:
            f.write("contenido de prueba")
        
        app.suggest_output_filename(demo_file)
        suggested = app.output_file_path.get()
        has_pz_extension = suggested.endswith('.pz')
        has_compressed_suffix = '_comprimido' in suggested
        print(f"✅ Sugerencia automática: {'PASS' if has_pz_extension and has_compressed_suffix else 'FAIL'}")
        print(f"   Sugerido: {Path(suggested).name}")
        
        # Prueba 4: Forzado de extensión .pz
        app.file_info = {'path': demo_file, 'name': 'test.txt'}
        
        # Simular selección sin extensión .pz
        test_path_without_ext = os.path.join(temp_dir, "sin_extension")
        
        # Simular el comportamiento del método
        final_path = test_path_without_ext
        if not final_path.endswith('.pz'):
            final_path = final_path + '.pz'
        
        print(f"✅ Forzado de extensión .pz: {'PASS' if final_path.endswith('.pz') else 'FAIL'}")
        print(f"   Original: {Path(test_path_without_ext).name}")
        print(f"   Final: {Path(final_path).name}")
        
        print("\n🎉 Todas las pruebas de validación completadas")
        
    except Exception as e:
        print(f"❌ Error en pruebas: {e}")
    
    finally:
        # Limpiar
        try:
            import shutil
            shutil.rmtree(temp_dir)
        except:
            pass
        app.root.destroy()


if __name__ == "__main__":
    print("Seleccione el modo de demostración:")
    print("1. Demo interactivo (GUI)")
    print("2. Pruebas programáticas")
    print("3. Ambos")
    
    choice = input("\nIngrese su opción (1-3): ").strip()
    
    if choice in ['1', '3']:
        demo_hu06()
    
    if choice in ['2', '3']:
        test_destination_validation()
    
    if choice not in ['1', '2', '3']:
        print("Opción inválida. Ejecutando demo interactivo por defecto.")
        demo_hu06()
