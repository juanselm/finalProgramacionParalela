"""
Diálogo de progreso para la compresión paralela
HU03: Progreso visual de compresión
"""

import tkinter as tk
from tkinter import ttk
import threading
import time
from pathlib import Path


class ProgressDialog:
    """Diálogo para mostrar el progreso de la compresión"""
    
    def __init__(self, parent, config):
        self.parent = parent
        self.config = config
        self.is_cancelled = False
        self.compression_thread = None
        
        # Crear ventana de progreso
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Comprimiendo archivo...")
        self.dialog.geometry("500x300")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()
        
        # Centrar el diálogo
        self.center_dialog()
        
        # Variables de progreso
        self.progress_var = tk.DoubleVar()
        self.status_var = tk.StringVar(value="Iniciando compresión...")
        self.phase_var = tk.StringVar(value="Preparación")
        self.time_var = tk.StringVar(value="Tiempo: 00:00")
        
        # Variables de tiempo
        self.start_time = None
        self.update_timer = None
        
        self.setup_ui()
        
    def center_dialog(self):
        """Centra el diálogo en la pantalla"""
        self.dialog.update_idletasks()
        x = (self.dialog.winfo_screenwidth() // 2) - (500 // 2)
        y = (self.dialog.winfo_screenheight() // 2) - (300 // 2)
        self.dialog.geometry(f"500x300+{x}+{y}")
        
    def setup_ui(self):
        """Configura la interfaz del diálogo de progreso"""
        # Frame principal
        main_frame = ttk.Frame(self.dialog, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Título
        title_label = ttk.Label(main_frame, text="🗜️ Compresión en Progreso", 
                               font=("Arial", 14, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Información del archivo
        info_frame = ttk.LabelFrame(main_frame, text="Información", padding="10")
        info_frame.pack(fill=tk.X, pady=(0, 20))
        
        file_info = self.config['file_info']
        ttk.Label(info_frame, text=f"Archivo: {file_info['name']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Tamaño: {file_info['size_formatted']}").pack(anchor=tk.W)
        ttk.Label(info_frame, text=f"Hilos: {self.config['threads']}").pack(anchor=tk.W)
        
        # HU06: Mostrar destino si está configurado
        if 'output_path' in self.config:
            output_name = Path(self.config['output_path']).name
            ttk.Label(info_frame, text=f"Destino: {output_name}").pack(anchor=tk.W)
        
        # Estado actual
        self.phase_label = ttk.Label(main_frame, textvariable=self.phase_var, 
                                    font=("Arial", 10, "bold"), foreground="blue")
        self.phase_label.pack(pady=(0, 10))
        
        # Barra de progreso
        self.progress_bar = ttk.Progressbar(main_frame, variable=self.progress_var, 
                                           maximum=100, length=400)
        self.progress_bar.pack(pady=(0, 10))
        
        # Porcentaje
        self.percent_label = ttk.Label(main_frame, text="0%", font=("Arial", 12, "bold"))
        self.percent_label.pack()
        
        # Estado detallado
        self.status_label = ttk.Label(main_frame, textvariable=self.status_var, 
                                     foreground="gray")
        self.status_label.pack(pady=(10, 0))
        
        # Tiempo transcurrido
        self.time_label = ttk.Label(main_frame, textvariable=self.time_var, 
                                   foreground="gray")
        self.time_label.pack(pady=(5, 20))
        
        # Botón cancelar
        self.cancel_button = ttk.Button(main_frame, text="❌ Cancelar", 
                                       command=self.cancel_compression)
        self.cancel_button.pack()
        
        # Protocolo de cierre
        self.dialog.protocol("WM_DELETE_WINDOW", self.cancel_compression)
        
    def start_compression(self, compress_function):
        """Inicia la compresión en un hilo separado"""
        self.start_time = time.time()
        self.update_time()
        
        # Crear y comenzar el hilo de compresión
        self.compression_thread = threading.Thread(
            target=self._compression_worker,
            args=(compress_function,),
            daemon=True
        )
        self.compression_thread.start()
        
    def _compression_worker(self, compress_function):
        """Worker que ejecuta la compresión en un hilo separado"""
        try:
            result = compress_function(
                input_file=self.config['file_info']['path'],
                output_file=self.get_output_filename(),
                progress_callback=self.update_progress
            )
            
            if not self.is_cancelled:
                self.dialog.after(0, self.compression_completed, result)
                
        except Exception as e:
            if not self.is_cancelled:
                self.dialog.after(0, self.compression_error, str(e))
    
    def get_output_filename(self):
        """HU06: Obtiene el nombre del archivo de salida desde la configuración"""
        # Si se especificó una ruta de destino en la configuración, usarla
        if 'output_path' in self.config:
            return self.config['output_path']
        
        # Fallback al comportamiento anterior
        input_path = self.config['file_info']['path']
        return input_path + ".parzip"
    
    def update_progress(self, status, percentage, phase=None):
        """Actualiza el progreso desde el hilo de compresión"""
        if self.is_cancelled:
            return False  # Señal para detener la compresión
        
        # Usar after() para actualizar la UI desde el hilo principal
        self.dialog.after(0, self._update_ui, status, percentage, phase)
        return True
    
    def _update_ui(self, status, percentage, phase):
        """Actualiza la UI en el hilo principal"""
        self.progress_var.set(percentage)
        self.status_var.set(status)
        self.percent_label.config(text=f"{percentage:.1f}%")
        
        if phase:
            self.phase_var.set(phase)
    
    def update_time(self):
        """Actualiza el tiempo transcurrido"""
        if self.start_time and not self.is_cancelled:
            elapsed = time.time() - self.start_time
            minutes = int(elapsed // 60)
            seconds = int(elapsed % 60)
            self.time_var.set(f"Tiempo: {minutes:02d}:{seconds:02d}")
            
            # Programar siguiente actualización
            self.update_timer = self.dialog.after(1000, self.update_time)
    
    def cancel_compression(self):
        """Cancela la compresión"""
        self.is_cancelled = True
        
        if self.update_timer:
            self.dialog.after_cancel(self.update_timer)
        
        self.phase_var.set("Cancelando...")
        self.status_var.set("Operación cancelada por el usuario")
        self.cancel_button.config(state="disabled")
        
        # Cerrar diálogo después de un breve retraso
        self.dialog.after(1500, self.close_dialog)
    
    def compression_completed(self, result):
        """Maneja la finalización exitosa de la compresión"""
        self.progress_var.set(100)
        self.percent_label.config(text="100%")
        self.phase_var.set("✅ Completado")
        self.status_var.set("Compresión finalizada exitosamente")
        
        if self.update_timer:
            self.dialog.after_cancel(self.update_timer)
        
        # Cambiar botón a "Cerrar"
        self.cancel_button.config(text="✅ Cerrar", command=self.close_dialog, state="normal")
        
        # Mostrar resultado
        if result:
            output_file = self.get_output_filename()
            from tkinter import messagebox
            messagebox.showinfo("Compresión Completada", 
                              f"Archivo comprimido exitosamente:\n{output_file}")
    
    def compression_error(self, error_msg):
        """Maneja errores durante la compresión"""
        self.phase_var.set("❌ Error")
        self.status_var.set(f"Error: {error_msg}")
        
        if self.update_timer:
            self.dialog.after_cancel(self.update_timer)
        
        # Cambiar botón a "Cerrar"
        self.cancel_button.config(text="❌ Cerrar", command=self.close_dialog, state="normal")
        
        # Mostrar error
        from tkinter import messagebox
        messagebox.showerror("Error de Compresión", f"Error durante la compresión:\n{error_msg}")
    
    def close_dialog(self):
        """Cierra el diálogo"""
        if self.update_timer:
            self.dialog.after_cancel(self.update_timer)
        
        self.dialog.destroy()
    
    def show(self):
        """Muestra el diálogo"""
        return self.dialog
