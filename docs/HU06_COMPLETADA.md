# HU06: Selección Personalizada de Destino

## Descripción
**Como usuario, quiero guardar el archivo comprimido en la ruta que yo elija.**

## Criterios de Aceptación ✅

### ✅ Criterio 1: Botón/Campo para Elegir Carpeta de Destino
- **Implementado**: Botón "💾 Elegir Destino" en la interfaz principal
- **Ubicación**: Sección "📁 Archivo de Destino" en la ventana principal
- **Funcionalidad**: Abre diálogo de "Guardar como" para seleccionar ubicación y nombre

### ✅ Criterio 2: Extensión Personalizada (.pz)
- **Implementado**: Extensión .pz aplicada automáticamente
- **Comportamiento**: Si el usuario no especifica .pz, se agrega automáticamente
- **Validación**: El sistema asegura que todos los archivos comprimidos tengan extensión .pz

## Tareas Técnicas Implementadas ✅

### ✅ Tarea 1: Selector de Archivos para Guardar Como
**Archivo**: `src/gui/main_window.py`
**Método**: `select_output_file()`

```python
def select_output_file(self):
    """HU06: Abre el diálogo para seleccionar la ruta de destino del archivo comprimido"""
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
```

**Características**:
- Nombre sugerido automáticamente: `{nombre_original}_comprimido.pz`
- Directorio inicial: mismo que el archivo original
- Filtros de archivo para .pz
- Extensión por defecto: .pz

### ✅ Tarea 2: Validación de Permisos de Escritura
**Archivo**: `src/gui/main_window.py`
**Método**: `validate_output_path()`

```python
def validate_output_path(self, output_path):
    """HU06: Valida que se pueda escribir en la ruta de destino"""
    # Verificar que el directorio existe o se puede crear
    output_dir = Path(output_path).parent
    if not output_dir.exists():
        output_dir.mkdir(parents=True, exist_ok=True)
    
    # Verificar permisos de escritura
    if not os.access(output_dir, os.W_OK):
        return False
    
    # Confirmar sobrescritura si el archivo existe
    if Path(output_path).exists():
        result = messagebox.askyesno("Archivo Existente", 
                                   f"El archivo '{Path(output_path).name}' ya existe.\n"
                                   "¿Desea sobrescribirlo?")
        return result
    
    return True
```

**Validaciones implementadas**:
- ✅ Verificación de existencia de directorio
- ✅ Creación automática de directorios faltantes
- ✅ Verificación de permisos de escritura
- ✅ Confirmación de sobrescritura para archivos existentes
- ✅ Manejo de errores de acceso

## Funcionalidades Adicionales Implementadas

### 🔄 Sugerencia Automática de Nombre
**Método**: `suggest_output_filename()`
- Se ejecuta automáticamente al seleccionar un archivo de entrada
- Genera nombre: `{archivo_original}_comprimido.pz`
- Valida automáticamente la ubicación sugerida

### 🎛️ Gestión del Estado de la Interfaz
**Método**: `update_compression_button_state()`
- El botón "🗜️ Comprimir" solo se habilita cuando:
  - Hay un archivo de entrada seleccionado
  - Hay una ruta de destino válida configurada

### 🧹 Limpieza Integrada
**Método**: `clear_selection()` (actualizado)
- Limpia tanto la selección de entrada como la de destino
- Restablece el estado de todos los botones
- Asegura consistencia en la interfaz

## Integración con el Sistema

### 📊 Diálogo de Progreso
**Archivo**: `src/gui/progress_dialog.py`
**Cambios**:
- Método `get_output_filename()` actualizado para usar ruta personalizada
- Muestra el nombre del archivo de destino en la información del progreso
- Fallback automático al comportamiento anterior si no hay ruta personalizada

### 🔗 Configuración de Compresión
La ruta de destino se integra en la configuración que se pasa al compresor:
```python
config = {
    'threads': self.num_threads.get(),
    'max_threads': self.max_threads,
    'file_info': self.file_info,
    'output_path': self.output_file_path.get()  # HU06: Nueva configuración
}
```

## Flujo de Usuario Completo

### Paso 1: Selección de Archivo de Entrada
1. Usuario hace clic en "📁 Seleccionar Archivo"
2. Se habilita automáticamente el botón "💾 Elegir Destino"
3. Se sugiere automáticamente una ubicación de destino

### Paso 2: Selección de Destino (Opcional)
1. Usuario puede usar la sugerencia automática, o
2. Hacer clic en "💾 Elegir Destino" para personalizar:
   - Cambiar carpeta de destino
   - Cambiar nombre del archivo
   - Extensión .pz se asegura automáticamente

### Paso 3: Validación Automática
1. Sistema valida permisos de escritura
2. Confirma sobrescritura si es necesario
3. Habilita botón "🗜️ Comprimir" solo cuando todo es válido

### Paso 4: Compresión
1. Usuario inicia compresión
2. Diálogo de progreso muestra archivo de destino
3. Archivo se guarda en la ubicación especificada con extensión .pz

## Casos de Uso Cubiertos

### ✅ Caso 1: Usuario Acepta Sugerencia Automática
- Selecciona archivo → Acepta sugerencia → Comprime
- Archivo se guarda como `{nombre}_comprimido.pz` en la misma carpeta

### ✅ Caso 2: Usuario Cambia Ubicación
- Selecciona archivo → Cambia destino → Elige nueva carpeta → Comprime
- Archivo se guarda en la ubicación personalizada

### ✅ Caso 3: Usuario Cambia Nombre
- Selecciona archivo → Cambia destino → Modifica nombre → Comprime
- Archivo se guarda con el nombre personalizado + .pz

### ✅ Caso 4: Archivo de Destino Existe
- Sistema detecta archivo existente → Solicita confirmación → Procede según respuesta

### ✅ Caso 5: Sin Permisos de Escritura
- Sistema detecta falta de permisos → Muestra error → Usuario debe elegir otra ubicación

## Pruebas Implementadas

### Archivo de Pruebas: `tests/test_hu06.py`

#### Pruebas de Funcionalidad:
- ✅ `test_select_output_file_valid_path`: Selección de ruta válida
- ✅ `test_validate_output_path_valid_directory`: Validación de directorio válido
- ✅ `test_validate_output_path_nonexistent_directory`: Creación de directorios
- ✅ `test_validate_output_path_existing_file`: Confirmación de sobrescritura
- ✅ `test_suggest_output_filename`: Sugerencia automática
- ✅ `test_extension_enforcement`: Forzado de extensión .pz
- ✅ `test_compression_button_state_management`: Gestión de estado de botones
- ✅ `test_clear_selection_clears_destination`: Limpieza completa

#### Pruebas de Integración:
- ✅ `test_progress_dialog_uses_custom_output_path`: Uso de ruta personalizada
- ✅ `test_progress_dialog_fallback_without_custom_path`: Fallback automático

## Demo Interactivo

### Archivo de Demo: `demo_hu06.py`
- **Demo Interactivo**: Lanza la aplicación con instrucciones
- **Pruebas Programáticas**: Valida funcionalidades automáticamente
- **Archivo de Prueba**: Crea contenido de ejemplo para testing

## Archivos Modificados

### Archivos Principales:
1. **`src/gui/main_window.py`**: Interfaz principal con nueva sección de destino
2. **`src/gui/progress_dialog.py`**: Soporte para ruta personalizada
3. **`main.py`**: Actualizado para mostrar HU06 ✅

### Archivos de Prueba:
4. **`tests/test_hu06.py`**: Suite completa de pruebas
5. **`demo_hu06.py`**: Demostración interactiva
6. **`test_file_hu06.txt`**: Archivo de ejemplo para pruebas

## Estado de Implementación

### ✅ COMPLETADO - HU06 Totalmente Funcional

**Criterios de Aceptación**: ✅ Cumplidos al 100%
**Tareas Técnicas**: ✅ Implementadas completamente
**Integración**: ✅ Integrado con HU01-HU05
**Pruebas**: ✅ Suite completa de pruebas
**Documentación**: ✅ Completa

### Funcionalidades Bonus Implementadas:
- 🎯 Sugerencia automática inteligente
- 🔐 Validación robusta de permisos
- 🎛️ Gestión avanzada del estado de la UI
- 🔄 Integración perfecta con el flujo existente
- 📊 Información de destino en progreso
- 🧹 Limpieza completa al resetear

**HU06 está lista para producción** 🚀
