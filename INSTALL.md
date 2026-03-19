# Guía de Instalación - Mapy Image Manager

Sigue estos pasos para instalar y ejecutar Mapy Image Manager en tu sistema.

## Instalación Rápida (5 minutos)

### 1. Descargar Python

- Descargar desde [python.org](https://www.python.org/downloads/) - Versión 3.9 o superior
- Durante la instalación, asegúrate de marcar "Add Python to PATH"

### 2. Clonar el repositorio

```bash
cd "Productos Mapy"
```

### 3. Instalar dependencias

**En Windows:**
```bash
run.bat
```

**En Linux/Mac:**
```bash
chmod +x run.sh
./run.sh
```

### 4. Configurar SerpAPI (para búsqueda de imágenes)

1. Visita [https://serpapi.com](https://serpapi.com)
2. Crea una cuenta gratuita
3. Copia tu clave API
4. Abre `.env` y pega tu clave:
   ```
   SERPAPI_KEY=tu_clave_aqui
   ```

### 5. Ejecutar la aplicación

Accede a: **http://localhost:8000**

## Instalación Detallada

### Requisitos Previos

- Python 3.9 o superior
- pip (incluido con Python)
- Espacio en disco: ~500MB
- Conexión a internet (para búsqueda de imágenes)

### Paso a Paso

#### Paso 1: Descargar el Proyecto

```bash
cd /ruta/a/Productos\ Mapy
```

#### Paso 2: Crear Entorno Virtual

Un entorno virtual aísla las dependencias del proyecto.

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

#### Paso 3: Instalar Dependencias

```bash
pip install -r requirements.txt
```

Esto instalará:
- FastAPI (framework web)
- Uvicorn (servidor)
- pandas y openpyxl (Excel)
- httpx (HTTP client)
- google-search-results (SerpAPI)

#### Paso 4: Configuración SerpAPI

Sin SerpAPI, solo puedes usar la importación manual de imágenes.

**Opción A: Variable de entorno (recomendado)**

Windows (en PowerShell):
```powershell
$env:SERPAPI_KEY="tu_clave_aqui"
```

Windows (en cmd):
```cmd
set SERPAPI_KEY=tu_clave_aqui
```

Linux/Mac:
```bash
export SERPAPI_KEY="tu_clave_aqui"
```

**Opción B: Archivo .env**

Copia `.env.example` a `.env`:
```bash
cp .env.example .env
```

Edita `.env` y añade tu clave:
```
SERPAPI_KEY=tu_clave_aqui
```

#### Paso 5: Inicializar Base de Datos

```bash
python -c "from database import Database; Database()"
```

Esto creará `data/products.db`.

#### Paso 6: Ejecutar la Aplicación

```bash
python app.py
```

O con uvicorn:
```bash
uvicorn app:app --reload --port 8000
```

Deberías ver:
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Abre tu navegador en: **http://localhost:8000**

## Instalación con Docker

Si tienes Docker instalado, es la forma más fácil:

### 1. Crear archivo .env

```bash
cp .env.example .env
# Edita .env con tu SERPAPI_KEY
```

### 2. Ejecutar Docker

```bash
docker-compose up
```

La aplicación estará en: **http://localhost:8000**

Para detener: `Ctrl+C`

## Solución de Problemas de Instalación

### Error: "Python no encontrado"

Python no está en el PATH. Desinstalalo y reinstalalo, asegurándote de marcar "Add Python to PATH".

### Error: "pip no encontrado"

Intenta:
```bash
python -m pip install -r requirements.txt
```

### Error: "Permission denied" (Linux/Mac)

```bash
chmod +x run.sh
./run.sh
```

### Error: "No module named 'fastapi'"

Las dependencias no se instalaron correctamente:
```bash
pip install -r requirements.txt --force-reinstall
```

### Error: "Port 8000 already in use"

Otro programa usa el puerto 8000. Opción A: Usa otro puerto:
```bash
uvicorn app:app --port 8001
```

Opción B: Mata el proceso usando el puerto (Linux/Mac):
```bash
lsof -ti:8000 | xargs kill -9
```

### Error: "Database is locked"

Cierra todos los procesos de la aplicación:
```bash
pkill -f "uvicorn app:app"
```

## Verificación de Instalación

Ejecuta estos comandos para verificar que todo está correcto:

```bash
# Verificar Python
python --version  # Debe ser 3.9+

# Verificar pip
pip --version

# Verificar dependencias
pip show fastapi
pip show pandas

# Verificar base de datos
python -c "from database import Database; print('Database OK')"

# Verificar que el servidor inicia
python app.py  # Presiona Ctrl+C después de 5 segundos
```

## Primeros Pasos

1. **Accede al dashboard**: http://localhost:8000
2. **Importa productos**:
   - Ve a "Subir XLSX"
   - Selecciona tu archivo Excel (Catalogo_Mapy_Final_V4.xlsx)
   - Espera a que se complete
3. **Busca imágenes**:
   - Ve a "Buscar Imágenes"
   - Elige una categoría y haz clic en "Iniciar Búsqueda en Lote"
   - O busca un producto individual
4. **Descarga actualizado**:
   - Ve a "Descargar XLSX" para obtener el catálogo con imágenes

## Actualización

Para actualizar a una versión más nueva:

```bash
# Descargar cambios
git pull origin main

# Instalar nuevas dependencias (si las hay)
pip install -r requirements.txt

# Reiniciar la aplicación
```

## Desinstalación

```bash
# Desactivar entorno virtual
deactivate

# Eliminar entorno (opcional)
rm -rf venv  # Linux/Mac
rmdir /s venv  # Windows
```

## Soporte

- **Documentación**: Ver README.md
- **Problemas**: Revisa el archivo de logs en la consola
- **SerpAPI Issues**: https://serpapi.com/docs

## Variables de Entorno Completas

```
# SerpAPI
SERPAPI_KEY=tu_clave_api

# Base de datos
DATABASE_PATH=data/products.db

# Búsqueda de imágenes
MAX_SEARCH_RESULTS=10
SEARCH_TIMEOUT=30
REQUEST_DELAY=1.5

# Interfaz
ITEMS_PER_PAGE=24
LANGUAGE=es

# Servidor
HOST=0.0.0.0
PORT=8000
DEBUG=False
```

## Siguiente: Primer Uso

Una vez instalado, sigue los "Primeros Pasos" arriba para:
1. Importar tu catálogo
2. Configurar la búsqueda de imágenes
3. Ejecutar búsquedas
4. Exportar los datos actualizados

¡Listo para empezar!
