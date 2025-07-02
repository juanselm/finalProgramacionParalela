"""
Configuración de parámetros de compresión
HU02: Configuración de parámetros de compresión
"""

import tkinter as tk
from tkinter import ttk


class CompressionConfigFrame(ttk.Frame):
    """Frame para configurar parámetros de compresión"""
    
    def __init__(self, parent):
        super().__init__(parent, padding="10")
        
        # Variables de configuración
        self.num_threads = tk.IntVar(value=4)
        self.block_size = tk.StringVar(value="1MB")
        self.compression_algorithm = tk.StringVar(value="zlib")
        
        self.setup_ui()
    
    def setup_ui(self):
        """Configura la interfaz de configuración"""
        # Título del frame
        title_label = ttk.Label(self, text="⚙️ Configuración de Compresión", 
                               font=("Arial", 12, "bold"))
        title_label.grid(row=0, column=0, columnspan=3, pady=(0, 15))
        
        # Número de hilos
        ttk.Label(self, text="Número de hilos:").grid(row=1, column=0, sticky=tk.W, pady=5)
        thread_spinbox = ttk.Spinbox(self, from_=1, to=16, textvariable=self.num_threads, width=10)
        thread_spinbox.grid(row=1, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        ttk.Label(self, text="(1-16)").grid(row=1, column=2, sticky=tk.W, padx=(5, 0))
        
        # Tamaño de bloque
        ttk.Label(self, text="Tamaño de bloque:").grid(row=2, column=0, sticky=tk.W, pady=5)
        block_combo = ttk.Combobox(self, textvariable=self.block_size, 
                                  values=["512KB", "1MB", "2MB", "4MB", "8MB"], 
                                  state="readonly", width=10)
        block_combo.grid(row=2, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Algoritmo de compresión
        ttk.Label(self, text="Algoritmo:").grid(row=3, column=0, sticky=tk.W, pady=5)
        algo_combo = ttk.Combobox(self, textvariable=self.compression_algorithm, 
                                 values=["zlib", "gzip", "bz2"], 
                                 state="readonly", width=10)
        algo_combo.grid(row=3, column=1, sticky=tk.W, padx=(10, 0), pady=5)
        
        # Información de configuración
        info_frame = ttk.LabelFrame(self, text="Información", padding="5")
        info_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(15, 0))
        
        self.config_info_label = ttk.Label(info_frame, text="", foreground="blue")
        self.config_info_label.pack()
        
        # Actualizar información cuando cambien los valores
        self.num_threads.trace('w', self.update_config_info)
        self.block_size.trace('w', self.update_config_info)
        self.compression_algorithm.trace('w', self.update_config_info)
        
        # Actualizar información inicial
        self.update_config_info()
    
    def update_config_info(self, *args):
        """Actualiza la información de configuración"""
        info_text = (f"Configuración: {self.num_threads.get()} hilos, "
                    f"bloques de {self.block_size.get()}, "
                    f"algoritmo {self.compression_algorithm.get()}")
        self.config_info_label.config(text=info_text)
    
    def get_config(self):
        """Retorna la configuración actual"""
        return {
            'threads': self.num_threads.get(),
            'block_size': self.block_size.get(),
            'algorithm': self.compression_algorithm.get()
        }
