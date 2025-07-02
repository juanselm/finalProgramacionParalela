"""
Punto de entrada principal para el compresor de archivos paralelo
"""

import sys
import os

# Agregar el directorio src al path para imports
sys.path.append(os.path.join(os.path.dirname(__file__), 'src'))

from gui.main_window import MainWindow


def main():
    """Función principal"""
    try:
        print("🗂️ Iniciando Compresor de Archivos Paralelo...")
        print("📋 HU01: Interfaz gráfica para selección de archivos")
        
        # Crear y ejecutar la aplicación
        app = MainWindow()
        app.run()
        
    except Exception as e:
        print(f"❌ Error al iniciar la aplicación: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
