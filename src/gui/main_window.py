"""
Interfaz gráfica principal del compresor de archivos paralelo
HU01: Selección de archivo mediante interfaz gráfica
HU02: Configuración de número de hilos
"""

import tkinter as tk
from tkinter import filedialog, messagebox, ttk
import os
import multiprocessing
from pathlib import Path
from datetime import datetime
from datetime import datetime

# Importar módulos para HU03
from gui.progress_dialog import ProgressDialog
from compression.parallel_compressor import ParallelCompressor
# HU07: Importar sistema de manejo de errores
from gui.error_handler import ErrorHandler, ErrorType, ErrorSeverity, handle_error


class MainWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("Compresor de Archivos Paralelo")
        self.root.geometry("700x600")
        self.root.resizable(True, True)
        
        # Variables para almacenar información del archivo
        self.selected_file_path = tk.StringVar()
        self.output_file_path = tk.StringVar()  # HU06: Ruta de destino
        self.file_info = {}
        
        # Variables para configuración HU02
        self.max_threads = multiprocessing.cpu_count()
        self.num_threads = tk.IntVar(value=min(4, self.max_threads))
        
        # HU07: Inicializar manejador de errores centralizado
        self.error_handler = ErrorHandler(self.root, enable_logging=True)
        
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
        
        # HU07: Agregar menú de errores
        self.setup_menu()
        
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
        
        # HU06: Sección de destino del archivo comprimido
        dest_frame = ttk.LabelFrame(main_frame, text="📁 Archivo de Destino", padding="10")
        dest_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        dest_frame.columnconfigure(1, weight=1)
        
        # Botón para seleccionar destino
        self.select_dest_button = ttk.Button(dest_frame, text="💾 Elegir Destino", 
                                           command=self.select_output_file, state="disabled")
        self.select_dest_button.grid(row=0, column=0, padx=(0, 10), pady=5)
        
        # Campo de texto para mostrar la ruta de destino
        self.output_path_entry = ttk.Entry(dest_frame, textvariable=self.output_file_path, 
                                         state="readonly", width=50)
        self.output_path_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), pady=5)
        
        # Información sobre la extensión
        ttk.Label(dest_frame, text="💡 El archivo se guardará con extensión .pz automáticamente", 
                 foreground="gray", font=("Arial", 9)).grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=2)
        
        # Información del archivo
        info_frame = ttk.LabelFrame(main_frame, text="Información del Archivo", padding="10")
        info_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
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
        
        # Sección de configuración de hilos (HU02)
        config_frame = ttk.LabelFrame(main_frame, text="⚙️ Configuración de Compresión", padding="10")
        config_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        config_frame.columnconfigure(2, weight=1)
        
        # Número de hilos
        ttk.Label(config_frame, text="Número de hilos:").grid(row=0, column=0, sticky=tk.W, pady=5)
        
        # Slider para seleccionar número de hilos
        self.thread_scale = ttk.Scale(config_frame, from_=1, to=self.max_threads, 
                                     variable=self.num_threads, orient=tk.HORIZONTAL, 
                                     length=200, command=self.update_thread_display)
        self.thread_scale.grid(row=0, column=1, padx=(10, 10), pady=5, sticky=tk.W)
        
        # Etiqueta para mostrar el valor actual
        self.thread_value_label = ttk.Label(config_frame, text=f"{self.num_threads.get()}", 
                                           foreground="blue", font=("Arial", 10, "bold"))
        self.thread_value_label.grid(row=0, column=2, sticky=tk.W, pady=5)
        
        # Información sobre los núcleos disponibles
        ttk.Label(config_frame, text=f"Núcleos disponibles: {self.max_threads}", 
                 foreground="gray", font=("Arial", 9)).grid(row=1, column=0, columnspan=3, sticky=tk.W, pady=2)
        
        # Spinbox alternativo (entrada numérica)
        ttk.Label(config_frame, text="O ingresa directamente:").grid(row=2, column=0, sticky=tk.W, pady=(10, 5))
        
        self.thread_spinbox = ttk.Spinbox(config_frame, from_=1, to=self.max_threads, 
                                         textvariable=self.num_threads, width=10,
                                         validate='key', validatecommand=(self.root.register(self.validate_thread_input), '%P'))
        self.thread_spinbox.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=(10, 5))
        
        # Información de rendimiento
        self.performance_label = ttk.Label(config_frame, text="", foreground="green", font=("Arial", 9))
        self.performance_label.grid(row=3, column=0, columnspan=3, sticky=tk.W, pady=5)
        
        # Actualizar display inicial
        self.update_thread_display()
        
        # Botones de acción
        action_frame = ttk.Frame(main_frame)
        action_frame.grid(row=5, column=0, columnspan=3, pady=20)
        
        self.compress_button = ttk.Button(action_frame, text="🗜️ Comprimir", 
                                         command=self.compress_file, state="disabled")
        self.compress_button.pack(side=tk.LEFT, padx=(0, 10))
        
        self.clear_button = ttk.Button(action_frame, text="🗑️ Limpiar", 
                                      command=self.clear_selection)
        self.clear_button.pack(side=tk.LEFT)
        
        # HU07: Panel de estado de errores
        self.setup_error_status_panel(main_frame)
        
    def setup_menu(self):
        """HU07: Configura el menú principal de la aplicación"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Menú Archivo
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Archivo", menu=file_menu)
        file_menu.add_command(label="Seleccionar archivo...", command=self.select_file)
        file_menu.add_command(label="Elegir destino...", command=self.select_output_file)
        file_menu.add_separator()
        file_menu.add_command(label="Salir", command=self.root.quit)
        
        # Menú Herramientas
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Herramientas", menu=tools_menu)
        tools_menu.add_command(label="Historial de errores", command=self.show_error_history)
        tools_menu.add_command(label="Limpiar historial", command=self.clear_error_history)
        tools_menu.add_separator()
        tools_menu.add_command(label="Configuración de logging", command=self.show_logging_config)
        
        # Menú Ayuda
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Ayuda", menu=help_menu)
        help_menu.add_command(label="Acerca de", command=self.show_about)
    
    def setup_error_status_panel(self, parent):
        """HU07: Configura el panel de estado de errores"""
        # Panel de estado en la parte inferior
        status_frame = ttk.Frame(parent)
        status_frame.grid(row=6, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(10, 0))
        status_frame.columnconfigure(1, weight=1)
        
        # Icono de estado
        self.error_status_icon = ttk.Label(status_frame, text="✅", font=("Arial", 12))
        self.error_status_icon.grid(row=0, column=0, padx=(0, 5))
        
        # Mensaje de estado
        self.error_status_message = ttk.Label(status_frame, text="Sistema listo - Sin errores", 
                                            foreground="green", font=("Arial", 9))
        self.error_status_message.grid(row=0, column=1, sticky=tk.W)
        
        # Botón para ver errores
        self.view_errors_button = ttk.Button(status_frame, text="Ver Errores", 
                                           command=self.show_error_history, state="disabled")
        self.view_errors_button.grid(row=0, column=2, padx=(5, 0))
        
        # Registrar callback para actualizar estado
        self.error_handler.register_callback(self.update_error_status)
    
    def update_error_status(self, error_info: dict):
        """HU07: Actualiza el panel de estado cuando ocurre un error"""
        error_count = len(self.error_handler.get_error_history())
        severity = error_info['severity']
        
        # Actualizar icono y mensaje según severidad
        if severity.value == 'critical':
            icon = "🔴"
            color = "red"
            message = f"Error crítico - {error_count} errores registrados"
        elif severity.value == 'error':
            icon = "🟠"
            color = "orange"
            message = f"Error - {error_count} errores registrados"
        elif severity.value == 'warning':
            icon = "🟡"
            color = "orange"
            message = f"Advertencia - {error_count} errores registrados"
        else:
            icon = "🔵"
            color = "blue"
            message = f"Información - {error_count} registros"
        
        self.error_status_icon.config(text=icon)
        self.error_status_message.config(text=message, foreground=color)
        self.view_errors_button.config(state="normal")
    
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
                    
                    # HU06: Habilitar botón de selección de destino
                    self.select_dest_button.config(state="normal")
                    
                    # HU06: Sugerir nombre de destino automáticamente
                    self.suggest_output_filename(file_path)
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
        """Inicia el proceso de compresión paralela con interfaz de progreso (HU03)"""
        if not self.file_info:
            messagebox.showerror("Error", "No hay archivo seleccionado para comprimir.")
            return
        
        # HU06: Verificar que se haya seleccionado destino
        if not self.output_file_path.get():
            messagebox.showerror("Error", "Debe seleccionar la ubicación de destino para el archivo comprimido.")
            return
        
        try:
            # Obtener configuración de compresión
            config = self.get_compression_config()
            
            # HU06: Agregar ruta de destino a la configuración
            config['output_path'] = self.output_file_path.get()
            
            # Crear y mostrar diálogo de progreso
            progress_dialog = ProgressDialog(self.root, config)
            
            # Crear instancia del compresor con error handler
            compressor = ParallelCompressor(error_handler=self.error_handler)
            
            # Crear función de compresión que usa la configuración
            def compress_with_config(input_file, output_file, progress_callback):
                # Configurar número de hilos en el compresor
                return compressor.compress_file_with_threads(
                    input_file=input_file,
                    output_file=output_file,
                    num_threads=config['threads'],
                    progress_callback=progress_callback
                )
            
            # Iniciar compresión
            progress_dialog.start_compression(compress_with_config)
            
        except Exception as e:
            messagebox.showerror("Error", f"Error iniciando compresión: {str(e)}")
    
    def clear_selection(self):
        """Limpia la selección actual"""
        self.selected_file_path.set("")
        self.output_file_path.set("")  # HU06: Limpiar destino
        self.name_label.config(text="")
        self.size_label.config(text="")
        self.location_label.config(text="")
        self.status_label.config(text="Ningún archivo seleccionado", foreground="gray")
        self.compress_button.config(state="disabled")
        self.select_dest_button.config(state="disabled")  # HU06: Deshabilitar destino
        self.file_info = {}
    
    # Métodos para HU02 - Configuración de hilos
    def update_thread_display(self, *args):
        """Actualiza la visualización del número de hilos seleccionado"""
        current_threads = int(self.num_threads.get())
        self.thread_value_label.config(text=f"{current_threads}")
        
        # Actualizar información de rendimiento
        if current_threads == 1:
            performance_text = "⚠️ Modo secuencial (sin paralelización)"
            color = "orange"
        elif current_threads <= self.max_threads // 2:
            performance_text = f"✅ Configuración conservadora ({current_threads} hilos)"
            color = "green"
        elif current_threads <= self.max_threads:
            performance_text = f"🚀 Máximo rendimiento ({current_threads} hilos)"
            color = "blue"
        else:
            performance_text = "⚠️ Excede núcleos disponibles"
            color = "red"
        
        self.performance_label.config(text=performance_text, foreground=color)
    
    def validate_thread_input(self, value):
        """Valida la entrada numérica para el número de hilos"""
        try:
            if value == "":
                return True
            
            num = int(value)
            if 1 <= num <= self.max_threads:
                return True
            else:
                # Mostrar advertencia si excede el límite
                if num > self.max_threads:
                    messagebox.showwarning("Advertencia", 
                                         f"El número de hilos no puede ser mayor a {self.max_threads} "
                                         f"(núcleos disponibles en el sistema)")
                return False
        except ValueError:
            return False
    
    def get_compression_config(self):
        """Retorna la configuración actual de compresión"""
        return {
            'threads': self.num_threads.get(),
            'max_threads': self.max_threads,
            'file_info': self.file_info
        }
    
    def select_output_file(self):
        """HU06: Abre el diálogo para seleccionar la ruta de destino del archivo comprimido"""
        if not self.file_info:
            messagebox.showerror("Error", "Primero debe seleccionar un archivo para comprimir.")
            return
        
        try:
            # Generar nombre sugerido basado en el archivo original
            original_path = Path(self.file_info['path'])
            suggested_name = f"{original_path.stem}_comprimido.pz"
            initial_dir = original_path.parent
            
            # Mostrar diálogo de guardar archivo
            output_path = filedialog.asksaveasfilename(
                title="Guardar archivo comprimido como...",
                defaultextension=".pz",
                initialdir=str(initial_dir),
                initialfile=suggested_name,
                filetypes=[
                    ("Archivos comprimidos", "*.pz"),
                    ("Todos los archivos", "*.*")
                ]
            )
            
            if output_path:
                # HU06: Validar permisos de escritura
                if self.validate_output_path(output_path):
                    # Asegurar que tenga la extensión .pz
                    if not output_path.endswith('.pz'):
                        output_path = output_path + '.pz'
                    
                    self.output_file_path.set(output_path)
                    self.update_compression_button_state()
                    
                    # Mostrar confirmación
                    messagebox.showinfo("Destino Seleccionado", 
                                      f"El archivo comprimido se guardará en:\n{output_path}")
                else:
                    messagebox.showerror("Error de Permisos", 
                                       "No tiene permisos de escritura en la ubicación seleccionada.")
                    
        except Exception as e:
            messagebox.showerror("Error", f"Error al seleccionar destino: {str(e)}")
    
    def validate_output_path(self, output_path):
        """HU06: Valida que se pueda escribir en la ruta de destino"""
        try:
            output_dir = Path(output_path).parent
            
            # Verificar que el directorio existe
            if not output_dir.exists():
                # Intentar crear el directorio
                output_dir.mkdir(parents=True, exist_ok=True)
            
            # Verificar permisos de escritura
            if not os.access(output_dir, os.W_OK):
                return False
            
            # Verificar si el archivo ya existe y si se puede sobrescribir
            if Path(output_path).exists():
                if not os.access(output_path, os.W_OK):
                    return False
                
                # Confirmar sobrescritura
                result = messagebox.askyesno("Archivo Existente", 
                                           f"El archivo '{Path(output_path).name}' ya existe.\n"
                                           "¿Desea sobrescribirlo?")
                return result
            
            return True
            
        except Exception as e:
            print(f"Error validando ruta de salida: {e}")
            return False
    
    def update_compression_button_state(self):
        """HU06: Actualiza el estado del botón de compresión según las selecciones"""
        if self.file_info and self.output_file_path.get():
            self.compress_button.config(state="normal")
        else:
            self.compress_button.config(state="disabled")
    
    def suggest_output_filename(self, input_path):
        """HU06: Sugiere automáticamente un nombre de archivo de destino"""
        try:
            original_path = Path(input_path)
            suggested_name = f"{original_path.stem}_comprimido.pz"
            suggested_full_path = original_path.parent / suggested_name
            
            # Validar que se puede escribir en esa ubicación
            if self.validate_output_path(str(suggested_full_path)):
                self.output_file_path.set(str(suggested_full_path))
                self.update_compression_button_state()
            
        except Exception as e:
            print(f"Error sugiriendo nombre de archivo: {e}")
    
    def run(self):
        """Ejecuta la aplicación"""
        self.root.mainloop()
    
    def show_error_history(self):
        """HU07: Muestra el historial detallado de errores"""
        self.error_handler.show_error_summary()
    
    def clear_error_history(self):
        """HU07: Limpia el historial de errores"""
        result = messagebox.askyesno("Limpiar Historial", 
                                   "¿Está seguro de que desea limpiar el historial de errores?")
        if result:
            self.error_handler.clear_history()
            self.error_status_icon.config(text="✅")
            self.error_status_message.config(text="Sistema listo - Sin errores", foreground="green")
            self.view_errors_button.config(state="disabled")
            messagebox.showinfo("Historial Limpiado", "El historial de errores ha sido limpiado.")
    
    def show_logging_config(self):
        """HU07: Muestra configuración de logging"""
        info = f"""Configuración de Logging:

Estado: {'Habilitado' if self.error_handler.enable_logging else 'Deshabilitado'}
Directorio de logs: logs/
Archivo actual: compression_errors_{datetime.now().strftime('%Y%m%d')}.log

Los errores se registran automáticamente en el archivo de log
y se muestran en la interfaz de usuario."""
        
        messagebox.showinfo("Configuración de Logging", info)
    
    def show_about(self):
        """HU07: Muestra información sobre la aplicación"""
        about_text = """Compresor de Archivos Paralelo
        
Versión: 1.0
Características implementadas:
✅ HU01: Interfaz gráfica para selección de archivos
✅ HU02: Configuración de número de hilos
✅ HU03: Compresión paralela con progreso visual
✅ HU04: División de archivos en bloques configurables
✅ HU05: Almacenamiento temporal y ensamblaje ordenado
✅ HU06: Selección personalizada de destino
✅ HU07: Sistema centralizado de manejo de errores

Desarrollado como proyecto educativo."""
        
        messagebox.showinfo("Acerca de", about_text)
