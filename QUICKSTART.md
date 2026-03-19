# Mapy Image Manager - Quick Start Guide

¡Bienvenido a Mapy Image Manager! Este documento te guiará en los primeros pasos.

## Opción 1: Windows (La más rápida)

### 1. Abre PowerShell o cmd en la carpeta del proyecto

```bash
cd "Productos Mapy\mapy-image-manager"
```

### 2. Ejecuta el archivo de inicio

```bash
run.bat
```

Esto hará todo automáticamente:
- ✓ Crear entorno virtual
- ✓ Instalar dependencias
- ✓ Inicializar base de datos
- ✓ Iniciar servidor

### 3. Abre tu navegador

```
http://localhost:8000
```

## Opción 2: Linux / Mac

### 1. Abre Terminal en la carpeta del proyecto

```bash
cd "Productos Mapy/mapy-image-manager"
```

### 2. Ejecuta el script de inicio

```bash
chmod +x run.sh
./run.sh
```

### 3. Abre tu navegador

```
http://localhost:8000
```

## Opción 3: Docker (Sin instalar Python)

### 1. Instala Docker Desktop desde docker.com

### 2. En la carpeta del proyecto, ejecuta

```bash
docker-compose up
```

### 3. Abre tu navegador

```
http://localhost:8000
```

## Configuración Inicial (Importante para búsqueda de imágenes)

### 1. Obtén una clave gratuita de SerpAPI

1. Visita [https://serpapi.com](https://serpapi.com)
2. Haz clic en "Sign up"
3. Crea una cuenta (gratis)
4. Ve a "API key" en tu dashboard
5. Copia tu clave (empieza con `'...`)

### 2. Configura la clave

**Opción A: Crear archivo .env (más fácil)**

En la carpeta del proyecto, crea un archivo llamado `.env` con este contenido:

```
SERPAPI_KEY=pega_tu_clave_aqui
```

Ejemplo:
```
SERPAPI_KEY='abc123def456ghi789'
```

**Opción B: Variable de entorno**

Windows (PowerShell):
```powershell
$env:SERPAPI_KEY="tu_clave_aqui"
```

Linux/Mac:
```bash
export SERPAPI_KEY="tu_clave_aqui"
```

### 3. Reinicia la aplicación

```bash
Ctrl+C  # Detén el servidor actual
python app.py  # O vuelve a ejecutar run.bat
```

## Primer Uso - Importar Catálogo

### 1. Accede al dashboard

Abre: http://localhost:8000

### 2. Sube tu archivo Excel

- Haz clic en "Subir XLSX" en el menú lateral
- Selecciona tu archivo (ej: `Catalogo_Mapy_Final_V4.xlsx`)
- Espera a que termine la importación
- ¡Listo! Tu catálogo está en el sistema

### 3. Busca imágenes automáticamente

**Opción A: Búsqueda en lote (recomendado)**

- Ve a "Buscar Imágenes"
- Selecciona una categoría
- Haz clic en "Iniciar Búsqueda en Lote"
- El sistema buscará automáticamente imágenes para todos los productos
- Toma ~5-10 minutos por cada 100 productos

**Opción B: Búsqueda individual**

- Busca un producto específico
- El sistema mostrará 6 opciones de imagen
- Selecciona las 2 mejores imágenes
- Haz clic en "Guardar Imágenes"

### 4. Descarga el catálogo actualizado

- Haz clic en "Descargar XLSX"
- Tu archivo se descargará con todas las URLs de imágenes

## Estructura del Proyecto

```
mapy-image-manager/
├── app.py              # Aplicación principal
├── database.py         # Base de datos
├── image_search.py     # Búsqueda de imágenes
├── config.py           # Configuración
├── templates/          # Páginas HTML
├── static/             # CSS, JS, imágenes
├── data/               # Base de datos (se crea automáticamente)
└── README.md           # Documentación completa
```

## Problemas Comunes

### "API key not configured"

Significa que no configuraste SERPAPI_KEY. Ver sección "Configuración Inicial" arriba.

### "Port 8000 already in use"

Otro programa usa el puerto. Intenta:

```bash
# Windows
netstat -ano | findstr :8000
taskkill /PID <PID> /F

# Linux/Mac
lsof -ti:8000 | xargs kill -9
```

O usa otro puerto:

```bash
uvicorn app:app --port 8001
```

### "No images found"

- Asegúrate de que SerpAPI esté configurado correctamente
- Intenta con un nombre de producto diferente
- Verifica tu cuota de SerpAPI (100 búsquedas/mes gratis)

### "Database is locked"

Cierra todos los procesos y reinicia:

```bash
python app.py
```

## Cuotas y Límites

### SerpAPI (Búsqueda de imágenes)

| Plan | Búsquedas/mes | Precio |
|------|---|---|
| **Gratuito** | 100 | $0 |
| Starter | 1,000 | $50 |
| Professional | Unlimited | $300 |

### Aplicación

- Máx 50,000 productos
- 24 productos por página
- 10 imágenes por búsqueda
- 30 segundos timeout
- 3 búsquedas simultáneas

## Teclados de Atajo

| Atajo | Función |
|-------|---------|
| Ctrl+K | Enfocar buscador |
| Esc | Cerrar modales |
| Enter | Enviar formulario |

## URLs Útiles

- **Dashboard**: http://localhost:8000
- **API productos**: http://localhost:8000/api/products
- **API estadísticas**: http://localhost:8000/api/stats
- **SerpAPI**: https://serpapi.com
- **Documentación**: README.md

## Siguiente: Deployment

Cuando quieras poner la aplicación en un servidor:

Ver README.md para:
- Deployment en Railway
- Deployment en Heroku
- Deployment en un VPS

## ¿Necesitas Ayuda?

1. Lee el README.md para documentación completa
2. Revisa INSTALL.md para troubleshooting detallado
3. Verifica los logs en la consola al ejecutar

## Límites Importantes

⚠️ **SerpAPI Gratuito**: 100 búsquedas/mes
- Para un catálogo de 40,972 productos necesitarías ~410 meses
- **Recomendación**: Busca por categorías (grupos de 50-100 productos)

## Tips para Optimizar

1. Busca por categoría (más rápido que individual)
2. Usa búsquedas en lote durante la noche
3. Filtra productos sin imágenes antes de buscar
4. Guarda imágenes que funcionen bien como referencia

## Verificación Final

Cuando veas esto, ¡está todo listo!

```
INFO:     Application startup complete
INFO:     Uvicorn running on http://0.0.0.0:8000
```

Accede a: **http://localhost:8000** ✓

---

**¡Listo para empezar! Disfruta usando Mapy Image Manager.**
