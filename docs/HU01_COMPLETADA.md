# HU01 - Selección de archivo mediante interfaz gráfica

## ✅ Estado: COMPLETADA

### 📋 Descripción
**Como usuario, quiero seleccionar un archivo desde una interfaz gráfica para poder comprimirlo fácilmente.**

### ✅ Criterios de aceptación cumplidos:
- ✅ La aplicación muestra un botón para "Seleccionar archivo"
- ✅ Al seleccionar el archivo, se muestra el nombre y ruta en pantalla
- ✅ El archivo seleccionado es validado como existente y accesible

### 🔧 Tareas técnicas completadas:
- ✅ Diseñar ventana principal con Tkinter
- ✅ Implementar selector de archivos (file dialog)
- ✅ Validar que el archivo exista y sea accesible
- ✅ Mostrar información del archivo seleccionado (nombre, ruta, tamaño)

### 🎯 Definición de Hecho:
- ✅ La interfaz gráfica se ejecuta correctamente
- ✅ El botón "Seleccionar archivo" abre un diálogo de archivos
- ✅ Se muestra la información del archivo seleccionado
- ✅ Se valida la existencia y accesibilidad del archivo

### 🧪 Pruebas
- ✅ Pruebas unitarias implementadas y pasando (4/4)
- ✅ Validación de archivos existentes
- ✅ Validación de archivos inexistentes
- ✅ Validación de archivos vacíos
- ✅ Formateo correcto de tamaños de archivo

### 📁 Archivos implementados:
- `main.py` - Punto de entrada principal
- `src/gui/main_window.py` - Interfaz gráfica principal con todas las funcionalidades
- `tests/test_hu01.py` - Pruebas unitarias completas

### 🚀 Funcionalidades adicionales implementadas:
- Formateo automático de tamaños de archivo (B, KB, MB, GB, TB)
- Estados visuales claros (válido/inválido/sin selección)
- Interfaz responsive y profesional
- Botón de limpiar selección
- Validación robusta de archivos
- Manejo de errores

### 📸 Interfaz implementada:
```
🗂️ Compresor de Archivos Paralelo
┌─────────────────────────────────────────────────┐
│ Selección de Archivo                            │
│ [📁 Seleccionar Archivo] [archivo_seleccionado] │
└─────────────────────────────────────────────────┘
┌─────────────────────────────────────────────────┐
│ Información del Archivo                         │
│ Nombre:    archivo.txt                          │
│ Tamaño:    1.25 MB                              │
│ Ubicación: C:\Users\...                         │
│ Estado:    ✅ Archivo válido y listo           │
└─────────────────────────────────────────────────┘
       [🗜️ Comprimir]  [🗑️ Limpiar]
```

### ➡️ Próximos pasos (HU02):
- Configuración de parámetros de compresión
- Selección de número de hilos
- Configuración de tamaño de bloque
- Selección de algoritmo de compresión
