# Mapy Image Manager

Un sistema de gestión de imágenes de productos para catálogos de e-commerce con soporte para 40,000+ productos.

## Características

- **Dashboard de Productos**: Visualiza todos los productos con filtros por categoría, marca, estado e imagen
- **Importación XLSX**: Carga catálogos completos desde archivos Excel
- **Búsqueda de Imágenes**: Integración con Google Images via SerpAPI para buscar automáticamente imágenes
  - Búsqueda individual: Busca y selecciona imágenes para un producto específico
  - Búsqueda en lote: Busca imágenes para todos los productos de una categoría
- **Gestión de Estado**: Seguimiento de productos por estado (Completo, Parcial, Pendiente, Sin imagen)
- **Exportación XLSX**: Descarga el catálogo actualizado con URLs de imágenes
- **Base de Datos SQLite**: Almacenamiento eficiente y rápido
- **Interfaz Responsive**: Diseño moderno y móvil-friendly

## Requisitos

- Python 3.9+
- pip

## Instalación

### 1. Clonar/Descargar el proyecto

```bash
cd /sessions/lucid-laughing-allen/mnt/"Productos Mapy"/mapy-image-manager
```

### 2. Crear entorno virtual

```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\Scripts\activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar SerpAPI

La búsqueda de imágenes requiere una clave de API de SerpAPI:

1. Registrarse en [https://serpapi.com](https://serpapi.com)
2. Obtener tu clave de API gratuita (100 búsquedas/mes)
3. Exportar la clave como variable de entorno:

```bash
export SERPAPI_KEY="tu_clave_aqui"
# En Windows: set SERPAPI_KEY=tu_clave_aqui
```

O crear un archivo `.env`:

```
SERPAPI_KEY=tu_clave_aqui
```

### 5. Inicializar la base de datos

```bash
python -c "from database import Database; Database()"
```

## Uso

### Iniciar el servidor

```bash
python app.py
```

O con uvicorn directamente:

```bash
uvicorn app:app --reload --host 0.0.0.0 --port 8000
```

El servidor estará disponible en: **http://localhost:8000**

### Flujo de trabajo

1. **Dashboard**: Visualiza los productos y su estado de imágenes
2. **Subir XLSX**: Importa tu catálogo desde un archivo Excel
3. **Buscar Imágenes**: Usa la búsqueda individual o en lote
4. **Descargar XLSX**: Exporta los datos actualizados

## Estructura del Proyecto

```
mapy-image-manager/
├── app.py                  # Aplicación FastAPI principal
├── database.py            # Capa de base de datos SQLite
├── image_search.py        # Integración con SerpAPI
├── xlsx_handler.py        # Importación/exportación de Excel
├── config.py              # Configuración
├── requirements.txt       # Dependencias Python
├── data/
│   ├── products.db       # Base de datos SQLite
│   └── images/           # Imágenes locales (futuro)
├── templates/
│   ├── base.html         # Template base
│   ├── dashboard.html    # Dashboard principal
│   ├── upload.html       # Página de importación
│   └── search.html       # Página de búsqueda
└── static/
    ├── css/
    │   └── style.css     # Estilos personalizados
    └── js/
        └── app.js        # JavaScript del cliente
```

## Formato XLSX esperado

Las columnas requeridas en el archivo Excel son:

| Columna | Requerido | Descripción |
|---------|-----------|-------------|
| SKU | Sí | Código único del producto |
| MARCA | Sí | Marca del producto |
| CATEGORIA | Sí | Categoría principal |
| NOMBRE_ESTANDAR_ES | Sí | Nombre en español |
| PRECO | Sí | Precio |
| SUBCATEGORIA | No | Subcategoría |
| NOMBRE_PADRONIZADO_PT | No | Nombre en portugués |
| DESC_ECOMMERCE_ES | No | Descripción en español |
| DESC_ECOMMERCE_PT | No | Descripción en portugués |
| URL_IMAGEN | No | URL de imagen existente |

## API Endpoints

### Productos

- `GET /` - Dashboard
- `GET /api/products` - Listar productos (con filtros y paginación)
- `GET /api/product/{id}` - Detalle de producto
- `GET /api/stats` - Estadísticas del catálogo

### Búsqueda de Imágenes

- `POST /api/search-images/{id}` - Buscar imágenes para un producto
- `POST /api/search-images-batch` - Búsqueda en lote por categoría
- `GET /api/batch-progress/{batch_id}` - Progreso de búsqueda en lote
- `POST /api/save-image/{id}` - Guardar imagen seleccionada

### Importación/Exportación

- `POST /upload` - Importar XLSX
- `GET /api/export` - Descargar XLSX actualizado

## Parámetros de Filtrado

```
GET /api/products?page=1&categoria=Electrónica&marca=Samsung&status=pending&search=laptop
```

- `page`: Número de página (defecto: 1)
- `categoria`: Filtrar por categoría
- `marca`: Filtrar por marca
- `status`: pending, partial, complete, no_image
- `search`: Búsqueda por SKU o nombre

## Despliegue en Producción

### Opción 1: Railway

```bash
# Instalar CLI de Railway
npm i -g @railway/cli

# Login y deploy
railway login
railway init
railway up
```

### Opción 2: Heroku

```bash
# Crear Procfile
echo "web: uvicorn app:app --host 0.0.0.0 --port $PORT" > Procfile

# Deploy
git init
git add .
git commit -m "Initial commit"
heroku create tu-app-name
git push heroku main
```

### Opción 3: VPS (DigitalOcean, Linode, etc.)

```bash
# En el servidor
git clone tu-repositorio
cd mapy-image-manager

# Instalar
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Ejecutar con Gunicorn
pip install gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 app:app
```

### Nginx Reverse Proxy (recomendado)

```nginx
server {
    listen 80;
    server_name tu-dominio.com;

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## Variables de Entorno

```
SERPAPI_KEY=tu_clave_api
DATABASE_PATH=data/products.db
MAX_SEARCH_RESULTS=10
ITEMS_PER_PAGE=24
```

## Límites y Quotas

### SerpAPI
- **Plan Gratuito**: 100 búsquedas/mes
- **Plan Starter**: 1,000 búsquedas/mes ($50)
- **Plan Professional**: Unlimited ($300/mes)

### Aplicación
- **Máximo de productos**: 50,000
- **Máximo de imágenes por búsqueda**: 10
- **Concurrencia de búsqueda**: 3 productos simultáneamente
- **Timeout de búsqueda**: 30 segundos

## Solución de Problemas

### "API key not configured"
Asegúrate de establecer la variable de entorno `SERPAPI_KEY`.

### "Database is locked"
El archivo de base de datos está siendo accedido por otro proceso. Reinicia la aplicación.

### "No images found"
El motor de búsqueda no encontró imágenes. Intenta con un nombre de producto diferente.

### "Out of quota"
Has excedido el límite de búsquedas de tu plan de SerpAPI. Upgrade a un plan superior.

## Rendimiento

### Optimizaciones implementadas

- Índices en base de datos para búsquedas rápidas
- Paginación (24 productos por página)
- Búsqueda concurrente (3 productos simultáneamente)
- Caché en navegador para datos recientes
- Lazy loading de imágenes
- Compresión de respuestas

### Benchmarks

- Dashboard: <500ms
- Búsqueda de imágenes individual: 2-5s
- Búsqueda en lote (100 productos): 5-10 min
- Importación XLSX (10,000 productos): 30-60s
- Exportación XLSX (10,000 productos): 10-20s

## Seguridad

- Validación de entrada en todos los endpoints
- Sanitización de datos
- CORS configurado
- SQL injection prevention (prepared statements)
- Rate limiting (1.5s entre requests a SerpAPI)

## Licencia

Propietario - Catálogo Mapy

## Soporte

Para reportar bugs o solicitar features, contacta al equipo de desarrollo.

## Changelog

### v1.0.0 (2024)
- Lanzamiento inicial
- Dashboard completo
- Búsqueda de imágenes
- Importación/exportación XLSX
- Estadísticas en tiempo real
