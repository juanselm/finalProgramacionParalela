# HU02 - Configuración de número de hilos

## ✅ Estado: COMPLETADA

### 📋 Descripción
**Como usuario, quiero elegir el número de hilos que se usarán para la compresión para poder ajustar el rendimiento.**

### ✅ Criterios de aceptación cumplidos:
- ✅ La interfaz ofrece una entrada (slider y spinbox) para elegir entre 1 y N hilos
- ✅ El número de hilos no puede ser mayor al número de núcleos disponibles
- ✅ Se muestra información visual sobre el rendimiento esperado

### 🔧 Tareas técnicas completadas:
- ✅ Control en GUI para seleccionar cantidad de hilos (slider + spinbox)
- ✅ Validación que el número no sea mayor al número de núcleos disponibles
- ✅ Detección automática de núcleos del sistema usando `multiprocessing.cpu_count()`
- ✅ Retroalimentación visual del rendimiento esperado
- ✅ Integración con la configuración de compresión

### 🎯 Funcionalidades implementadas:

#### 1. **Slider de hilos**
- Rango: 1 hasta `multiprocessing.cpu_count()`
- Actualización en tiempo real del valor
- Sincronización con entrada numérica

#### 2. **Entrada numérica (Spinbox)**
- Validación en tiempo real
- Previene valores fuera del rango válido
- Advertencias automáticas para valores inválidos

#### 3. **Retroalimentación visual inteligente**
- 🟠 **1 hilo**: "⚠️ Modo secuencial (sin paralelización)"
- 🟢 **2 a N/2 hilos**: "✅ Configuración conservadora"
- 🔵 **N/2+ a N hilos**: "🚀 Máximo rendimiento"
- 🔴 **>N hilos**: "⚠️ Excede núcleos disponibles"

#### 4. **Información del sistema**
- Detección automática de núcleos disponibles
- Mostrar información del sistema en la interfaz
- Configuración inicial inteligente (4 hilos o máximo disponible)

### 🧪 Pruebas: 8/8 PASANDO
- ✅ `test_initial_thread_configuration` - Configuración inicial correcta
- ✅ `test_thread_validation_valid_range` - Validación de valores válidos
- ✅ `test_thread_validation_invalid_range` - Rechazo de valores inválidos
- ✅ `test_thread_validation_non_numeric` - Manejo de entrada no numérica
- ✅ `test_thread_display_update` - Actualización de display
- ✅ `test_compression_config_retrieval` - Obtención de configuración
- ✅ `test_performance_label_updates` - Etiquetas de rendimiento
- ✅ `test_thread_config_with_file_selection` - Integración con selección

### 📁 Archivos modificados/creados:
- `src/gui/main_window.py` - Interfaz actualizada con configuración de hilos
- `tests/test_hu02.py` - Suite de pruebas completa para HU02
- `main.py` - Actualizado para reflejar HU02 completada

### 🚀 Funcionalidades adicionales implementadas:
- **Detección automática de hardware**: Usa `multiprocessing.cpu_count()` para detectar núcleos
- **Validación robusta**: Previene configuraciones inválidas
- **Retroalimentación intuitiva**: Códigos de color y mensajes claros
- **Doble control**: Slider para facilidad + spinbox para precisión
- **Configuración inteligente**: Valor inicial óptimo (4 hilos o máximo disponible)
- **Integración perfecta**: Se combina con la selección de archivos de HU01

### 📸 Interfaz de configuración implementada:
```
⚙️ Configuración de Compresión
┌─────────────────────────────────────────────────────┐
│ Número de hilos: [====●====] 4                     │
│ Núcleos disponibles: 12                             │
│ O ingresa directamente: [4▼]                        │
│ ✅ Configuración conservadora (4 hilos)             │
└─────────────────────────────────────────────────────┘
```

### 🎮 Uso de la funcionalidad:
1. **Slider**: Arrastra para ajustar número de hilos visualmente
2. **Spinbox**: Ingresa número exacto o usa flechas
3. **Validación automática**: Valores fuera de rango son rechazados
4. **Retroalimentación**: Color y texto indican rendimiento esperado

### 🔗 Integración con HU01:
- La configuración de hilos se incluye en el diálogo de compresión
- Se muestra junto con información del archivo seleccionado
- Validación combinada: archivo + configuración de hilos

### ➡️ Preparación para HU03:
- Configuración de hilos lista para usar en compresión paralela
- Método `get_compression_config()` retorna toda la configuración
- Interfaz preparada para mostrar progreso de compresión

### 🏆 Criterios de aceptación - VERIFICACIÓN:

#### ✅ "La interfaz debe ofrecer una entrada para elegir entre 1 y N hilos"
- **CUMPLIDO**: Slider (1 a N) + Spinbox (1 a N)
- **Evidencia**: Controles visuales en la interfaz
- **Prueba**: `test_thread_validation_valid_range`

#### ✅ "Validar que el número no sea mayor al número de núcleos disponibles"
- **CUMPLIDO**: Validación en tiempo real + advertencias
- **Evidencia**: Advertencia automática cuando se excede límite
- **Prueba**: `test_thread_validation_invalid_range`

### 🎯 Estado: **HU02 COMPLETAMENTE FUNCIONAL** ✅

La Historia de Usuario 02 está **100% implementada y probada**. Los usuarios pueden ahora:
- Seleccionar número de hilos con controles intuitivos
- Recibir retroalimentación sobre el rendimiento esperado
- Estar protegidos contra configuraciones inválidas
- Ver información clara sobre su sistema (núcleos disponibles)
