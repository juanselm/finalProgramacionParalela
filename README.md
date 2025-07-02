# 🗂️ Compresor de Archivos Paralelo

Proyecto final de la asignatura de Sistemas Operativos y laboratorio.

## 🎯 Objetivo:

Dividir un archivo grande en bloques y comprimir cada bloque en paralelo utilizando múltiples hilos. Luego combinar los bloques comprimidos en un único archivo.

---

## 📌 Fases del proyecto

### 1. **Lectura del archivo en bloques**

* Abre el archivo de entrada.
* Divide el archivo en bloques de tamaño fijo (por ejemplo, 1 MB cada uno).
* Guarda los desplazamientos en un array.

### 2. **Compresión por bloques en paralelo**

* Usa **`pthread`** o **OpenMP** para crear hilos.
* Cada hilo toma uno o varios bloques y los comprime (usando `zlib` o una compresión simple como RLE).
* Guarda el resultado en memoria o en archivos temporales.

### 3. **Escritura del archivo comprimido**

* Combina todos los bloques comprimidos en un solo archivo.
* Guarda también un encabezado con metadatos (número de bloques, tamaños, etc.).

---

## 🛠️ Herramientas

| Herramienta          | Uso                        |
| -------------------- | -------------------------- |
| `pthread`            | Control de concurrencia    |
| `zlib`               | Compresión (gzip/deflate)  |
| `Makefile`           | Automatizar compilación    |
| `fopen/fread/fwrite` | Entrada/salida de archivos |

---

## 🧪 Ejemplo de ejecución

```bash
./parzip archivo_grande.txt archivo_comprimido.pz
```

Opcionalmente:

```bash
./parzip -t 4 archivo.txt archivo.pz   # usa 4 hilos
```

---

## 🧠 Ideas para mejorar

* Agregar **descompresión** (`pardecompress`).
* Soportar múltiples algoritmos de compresión.
* Mostrar una barra de progreso.
* Comparar velocidad entre secuencial y paralelo.
