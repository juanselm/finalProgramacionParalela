"""
Interfaz gráfica principal del compresor de archivos paralelo
HU01: Selección de archivo mediante interfaz gráfica
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
from pathlib import Path


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Compresor de Archivos Paralelo")
        self.root.geometry("600x400")
        self.root.resizable(True, True)
        
        # Variables para almacenar información del archivo
        self.selected_file_path = tk.StringVar()
        self.file_info = {}
        
        self.setup_ui()
        
    def setup_ui(self):
        """Configura la interfaz de usuario"""
        # Frame principal
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configurar expansión de la ventana
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Título
        title_label = ttk.Label(main_frame, text="🗂️ Compresor de Archivos Paralelo", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 20))
        
        # Sección de selección de archivo
        file_frame = ttk.LabelFrame(main_frame, text="Selección de Archivo", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        file_frame.columnconfigure(1, weight=1)
        
        # Botón para seleccionar archivo
        self.select_button = ttk.Button(file_frame, text="📁 Seleccionar Archivo", 
                                       command=self.select_file)
        self.select_button.grid(row=0, column=0, padx=(0, 10), pady=5)
        
        # Campo de texto para mostrar la ruta del archivo
        self.file_path_entry = ttk.Entry(file_frame, textvariable=self.selected_file_path, 
                                        state="readonly", width=50)
        self.file_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Información del archivo
        info_frame = ttk.LabelFrame(main_frame, text="Información del Archivo", padding="10")
        info_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        info_frame.columnconfigure(1, weight=1)
        
        # Labels para mostrar información
        ttk.Label(info_frame, text="Nombre:").grid(row=0, column=0, sticky=tk.W, pady=2)
        self.name_label = ttk.Label(info_frame, text="", foreground="blue")
        self.name_label.grid(row=0, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="Tamaño:").grid(row=1, column=0, sticky=tk.W, pady=2)
        self.size_label = ttk.Label(info_frame, text="", foreground="blue")
        self.size_label.grid(row=1, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="Ubicación:").grid(row=2, column=0, sticky=tk.W, pady=2)
        self.location_label = ttk.Label(info_frame, text="", foreground="blue")
        self.location_label.grid(row=2, column=1, sticky=tk.W, pady=2)
        
        ttk.Label(info_frame, text="Estado:").grid(row=3, column=0, sticky=tk.W, pady=2)
        self.status_label = ttk.Label(info_frame, text="Ningún archivo seleccionado", 
                                     foreground="gray")
        self.status_label.grid(row=3, column=1, sticky=tk.W, pady=2)
        
        # Botones de acción
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=3, column=0, columnspan=3, pady=20)
        
        self.compress_button = ttk.Button(action_frame, text="🗜️ Comprimir", 
                                         command=self.compress_file, state="disabled")
        self.compress_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(action_frame, text="🗑️ Limpiar", 
                                      command=self.clear_selection)
        self.clear_button.pack(side=tk.LEFT)
        
    def select_file(self):
        """Abre el diálogo para seleccionar un archivo"""
        try:
            file_path = filedialog.askopenfilename(
                title="Seleccionar archivo para comprimir",
                filetypes=[
                    ("Todos los archivos", "*.*"),
                    ("Archivos de texto", "*.txt"),
                    ("Archivos de imagen", "*.jpg;*.png;*.gif"),
                    ("Archivos de documento", "*.pdf;*.doc;*.docx")
                ]
            )
            
            if file_path:
                if self.validate_file(file_path):
                    self.selected_file_path.set(file_path)
                    self.display_file_info(file_path)
                    self.compress_button.config(state="normal")
                else:
                    messagebox.showerror("Error", "El archivo seleccionado no es válido o no se puede acceder a él.")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error al seleccionar archivo: {str(e)}")
    
    def validate_file(self, file_path):
        """Valida que el archivo exista y sea accesible"""
        try:
            path = Path(file_path)
            
            # Verificar que el archivo existe
            if not path.exists():
                return False
                
            # Verificar que es un archivo (no un directorio)
            if not path.is_file():
                return False
                
            # Verificar que se puede leer
            if not os.access(file_path, os.R_OK):
                return False
                
            # Verificar que el archivo no está vacío
            if path.stat().st_size == 0:
                messagebox.showwarning("Advertencia", "El archivo seleccionado está vacío.")
                return False
                
            return True
            
        except Exception as e:
            print(f"Error validando archivo: {e}")
            return False
    
    def display_file_info(self, file_path):
        """Muestra la información del archivo seleccionado"""
        try:
            path = Path(file_path)
            file_size = path.stat().st_size
            
            # Formatear el tamaño del archivo
            size_str = self.format_file_size(file_size)
            
            # Actualizar labels
            self.name_label.config(text=path.name)
            self.size_label.config(text=size_str)
            self.location_label.config(text=str(path.parent))
            self.status_label.config(text="✅ Archivo válido y listo para comprimir", 
                                   foreground="green")
            
            # Guardar información del archivo
            self.file_info = {
                'path': file_path,
                'name': path.name,
                'size': file_size,
                'size_formatted': size_str,
                'directory': str(path.parent)
            }
            
        except Exception as e:
            self.status_label.config(text="❌ Error al leer información del archivo", 
                                   foreground="red")
            print(f"Error mostrando info del archivo: {e}")
    
    def format_file_size(self, size_bytes):
        """Formatea el tamaño del archivo en unidades legibles"""
        if size_bytes == 0:
            return "0 B"
        
        size_names = ["B", "KB", "MB", "GB", "TB"]
        i = 0
        size = float(size_bytes)
        
        while size >= 1024.0 and i < len(size_names) - 1:
            size /= 1024.0
            i += 1
            
        return f"{size:.2f} {size_names[i]}"
    
    def compress_file(self):
        """Función placeholder para comprimir archivo (se implementará en HU posteriores)"""
        if self.file_info:
            messagebox.showinfo("Compresión", 
                              f"Funcionalidad de compresión pendiente de implementar.\n"
                              f"Archivo seleccionado: {self.file_info['name']}\n"
                              f"Tamaño: {self.file_info['size_formatted']}")
    
    def clear_selection(self):
        """Limpia la selección actual"""
        self.selected_file_path.set("")
        self.name_label.config(text="")
        self.size_label.config(text="")
        self.location_label.config(text="")
        self.status_label.config(text="Ningún archivo seleccionado", foreground="gray")
        self.compress_button.config(state="disabled")
        self.file_info = {}
    
    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()


if __name__ == "__main__":
    app = MainWindow()
    app.run()
