"""
HU07: Sistema centralizado de manejo de errores
Proporciona notificación uniforme de errores en toda la aplicación
"""

import tkinter as tk
from tkinter import messagebox
import traceback
import logging
from datetime import datetime
from enum import Enum
from typing import Optional, Callable
import os


class ErrorType(Enum):
    """Tipos de errores que puede manejar la aplicación"""
    FILE_READ = "Lectura de archivo"
    FILE_WRITE = "Escritura de archivo"
    COMPRESSION = "Compresión"
    DECOMPRESSION = "Descompresión"
    PERMISSION = "Permisos"
    VALIDATION = "Validación"
    NETWORK = "Red"
    MEMORY = "Memoria"
    UNKNOWN = "Error desconocido"


class ErrorSeverity(Enum):
    """Niveles de severidad de errores"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class ErrorHandler:
    """
    HU07: Gestor centralizado de errores para la aplicación
    Proporciona manejo uniforme y notificación de errores
    """
    
    def __init__(self, parent_window: Optional[tk.Tk] = None, enable_logging: bool = True):
        """
        Inicializa el manejador de errores
        
        Args:
            parent_window: Ventana principal para centrar diálogos
            enable_logging: Si habilitar logging a archivo
        """
        self.parent_window = parent_window
        self.enable_logging = enable_logging
        self.error_history = []
        self.error_callbacks = []
        
        # Configurar logging si está habilitado
        if enable_logging:
            self._setup_logging()
    
    def _setup_logging(self):
        """Configura el sistema de logging"""
        try:
            log_dir = "logs"
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            log_file = os.path.join(log_dir, f"compression_errors_{datetime.now().strftime('%Y%m%d')}.log")
            
            logging.basicConfig(
                level=logging.INFO,
                format='%(asctime)s - %(levelname)s - %(message)s',
                handlers=[
                    logging.FileHandler(log_file),
                    logging.StreamHandler()
                ]
            )
            
            self.logger = logging.getLogger(__name__)
            
        except Exception as e:
            print(f"Warning: No se pudo configurar logging: {e}")
            self.enable_logging = False
    
    def handle_error(self, 
                    error: Exception, 
                    error_type: ErrorType = ErrorType.UNKNOWN,
                    severity: ErrorSeverity = ErrorSeverity.ERROR,
                    context: str = "",
                    show_dialog: bool = True,
                    user_message: str = None) -> dict:
        """
        HU07: Maneja un error de manera centralizada
        
        Args:
            error: La excepción que ocurrió
            error_type: Tipo de error
            severity: Severidad del error
            context: Contexto donde ocurrió el error
            show_dialog: Si mostrar diálogo al usuario
            user_message: Mensaje personalizado para el usuario
            
        Returns:
            dict: Información del error procesado
        """
        error_info = {
            'timestamp': datetime.now(),
            'type': error_type,
            'severity': severity,
            'context': context,
            'exception': error,
            'message': str(error),
            'traceback': traceback.format_exc(),
            'user_message': user_message or self._generate_user_message(error_type, error)
        }
        
        # Agregar a historial
        self.error_history.append(error_info)
        
        # Logging
        if self.enable_logging:
            self._log_error(error_info)
        
        # Notificar callbacks
        self._notify_callbacks(error_info)
        
        # Mostrar diálogo si es necesario
        if show_dialog:
            self._show_error_dialog(error_info)
        
        return error_info
    
    def _generate_user_message(self, error_type: ErrorType, error: Exception) -> str:
        """Genera un mensaje amigable para el usuario"""
        messages = {
            ErrorType.FILE_READ: "No se pudo leer el archivo seleccionado. Verifique que el archivo existe y tiene permisos de lectura.",
            ErrorType.FILE_WRITE: "No se pudo escribir el archivo de destino. Verifique los permisos de escritura en la ubicación seleccionada.",
            ErrorType.COMPRESSION: "Error durante el proceso de compresión. El archivo puede estar corrupto o ser demasiado grande.",
            ErrorType.DECOMPRESSION: "Error durante el proceso de descompresión. El archivo puede estar corrupto.",
            ErrorType.PERMISSION: "Sin permisos suficientes para realizar la operación. Ejecute como administrador o cambie la ubicación.",
            ErrorType.VALIDATION: "Los datos proporcionados no son válidos. Verifique la información ingresada.",
            ErrorType.MEMORY: "Memoria insuficiente para completar la operación. Cierre otras aplicaciones o use un archivo más pequeño.",
            ErrorType.NETWORK: "Error de conexión de red. Verifique su conexión a internet.",
            ErrorType.UNKNOWN: "Ha ocurrido un error inesperado. Por favor, inténtelo nuevamente."
        }
        
        return messages.get(error_type, f"Error: {str(error)}")
    
    def _show_error_dialog(self, error_info: dict):
        """Muestra un diálogo de error al usuario"""
        try:
            severity = error_info['severity']
            title = f"{error_info['type'].value} - {severity.value.title()}"
            message = error_info['user_message']
            
            # Agregar contexto si existe
            if error_info['context']:
                message += f"\n\nContexto: {error_info['context']}"
            
            # Mostrar diálogo según severidad
            if severity == ErrorSeverity.CRITICAL:
                messagebox.showerror(title, message, parent=self.parent_window)
            elif severity == ErrorSeverity.ERROR:
                messagebox.showerror(title, message, parent=self.parent_window)
            elif severity == ErrorSeverity.WARNING:
                messagebox.showwarning(title, message, parent=self.parent_window)
            else:  # INFO
                messagebox.showinfo(title, message, parent=self.parent_window)
        
        except Exception as e:
            # Fallback si no se puede mostrar diálogo
            print(f"Error mostrando diálogo: {e}")
            print(f"Error original: {error_info['message']}")
    
    def _log_error(self, error_info: dict):
        """Registra el error en el log"""
        try:
            log_message = (
                f"[{error_info['type'].value}] "
                f"{error_info['message']} | "
                f"Context: {error_info['context']} | "
                f"Severity: {error_info['severity'].value}"
            )
            
            if error_info['severity'] == ErrorSeverity.CRITICAL:
                self.logger.critical(log_message)
            elif error_info['severity'] == ErrorSeverity.ERROR:
                self.logger.error(log_message)
            elif error_info['severity'] == ErrorSeverity.WARNING:
                self.logger.warning(log_message)
            else:
                self.logger.info(log_message)
            
            # Log completo del traceback para errores graves
            if error_info['severity'] in [ErrorSeverity.ERROR, ErrorSeverity.CRITICAL]:
                self.logger.debug(f"Traceback: {error_info['traceback']}")
        
        except Exception as e:
            print(f"Error en logging: {e}")
    
    def _notify_callbacks(self, error_info: dict):
        """Notifica a callbacks registrados sobre el error"""
        for callback in self.error_callbacks:
            try:
                callback(error_info)
            except Exception as e:
                print(f"Error en callback: {e}")
    
    def register_callback(self, callback: Callable):
        """Registra un callback para notificaciones de error"""
        self.error_callbacks.append(callback)
    
    def remove_callback(self, callback: Callable):
        """Remueve un callback"""
        if callback in self.error_callbacks:
            self.error_callbacks.remove(callback)
    
    def get_error_history(self) -> list:
        """Obtiene el historial de errores"""
        return self.error_history.copy()
    
    def clear_history(self):
        """Limpia el historial de errores"""
        self.error_history.clear()
    
    def show_error_summary(self):
        """Muestra un resumen de errores al usuario"""
        if not self.error_history:
            messagebox.showinfo("Historial de Errores", 
                              "No se han registrado errores.",
                              parent=self.parent_window)
            return
        
        # Contar errores por tipo y severidad
        error_counts = {}
        for error_info in self.error_history:
            key = f"{error_info['type'].value} ({error_info['severity'].value})"
            error_counts[key] = error_counts.get(key, 0) + 1
        
        # Crear mensaje de resumen
        summary = "Resumen de errores:\n\n"
        for error_type, count in error_counts.items():
            summary += f"• {error_type}: {count}\n"
        
        summary += f"\nTotal de errores: {len(self.error_history)}"
        
        messagebox.showinfo("Historial de Errores", summary, parent=self.parent_window)


# Instancia global del manejador de errores
_global_error_handler = None


def get_error_handler() -> ErrorHandler:
    """Obtiene la instancia global del manejador de errores"""
    global _global_error_handler
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    return _global_error_handler


def set_error_handler(handler: ErrorHandler):
    """Establece la instancia global del manejador de errores"""
    global _global_error_handler
    _global_error_handler = handler


def handle_error(error: Exception, 
                error_type: ErrorType = ErrorType.UNKNOWN,
                severity: ErrorSeverity = ErrorSeverity.ERROR,
                context: str = "",
                show_dialog: bool = True,
                user_message: str = None) -> dict:
    """
    Función de conveniencia para manejar errores usando el handler global
    """
    return get_error_handler().handle_error(
        error, error_type, severity, context, show_dialog, user_message
    )


# Decorador para manejo automático de errores
def error_handler(error_type: ErrorType = ErrorType.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.ERROR,
                 show_dialog: bool = True,
                 user_message: str = None):
    """
    Decorador para manejo automático de errores en funciones
    """
    def decorator(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                handle_error(
                    error=e,
                    error_type=error_type,
                    severity=severity,
                    context=f"Función: {func.__name__}",
                    show_dialog=show_dialog,
                    user_message=user_message
                )
                return None
        return wrapper
    return decorator
