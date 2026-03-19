# Mapy Image Manager

Sistema de gestión de imágenes de productos para catálogos e-commerce con 40,000+ productos.

## Características

- **Dashboard**: Visualiza productos con filtros por categoría, marca y estado
- **Importación XLSX**: Carga catálogos completos desde Excel
- **Búsqueda de Imágenes**: Google Custom Search API para buscar imágenes automáticamente
  - Búsqueda individual por producto
  - Búsqueda en lote por categoría
- **Gestión de Estado**: Completo, Parcial, Pendiente, Sin imagen
- **Exportación**: Descarga catálogo actualizado con URLs de imágenes
- **Base de Datos SQLite**: Almacenamiento eficiente
- **Interfaz Responsive**: Diseño moderno con TailwindCSS

## Requisitos

- Python 3.9+
- Google Custom Search API Key + CX ID (gratuito: 100 búsquedas/día)

## Instalación rápida

```bash
# 1. Clonar
git clone https://github.com/thiagofregolao-blip/mapyimage.git
cd mapyimage

# 2. Crear entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# 3. Instalar dependencias
pip install -r requirements.txt

# 4. Configurar API keys
cp .env.example .env
# Editar .env con tus keys (ver sección "Obtener API Keys")

# 5. Ejecutar
python app.py
```

Abrir en el navegador: **http://localhost:8000**

## Obtener API Keys (Google Custom Search)

### Paso 1: API Key
1. Ir a [Google Cloud Console](https://console.cloud.google.com/apis/credentials)
2. Crear un proyecto (o usar uno existente)
3. Habilitar la **"Custom Search JSON API"**
4. Ir a Credenciales → Crear credencial → API Key
5. Copiar la key

### Paso 2: Search Engine ID (CX)
1. Ir a [Programmable Search Engine](https://programmablesearchengine.google.com/)
2. Crear nuevo motor de búsqueda
3. En "Sitios a buscar" poner `*` (toda la web)
4. Activar "Búsqueda de imágenes"
5. Copiar el ID del motor (CX)

### Paso 3: Configurar
Editar archivo `.env`:
```
GOOGLE_API_KEY=AIzaSy...tu_key_aqui
GOOGLE_CX_ID=a1b2c3d4...tu_cx_aqui
```

### Límites gratuitos
- **100 búsquedas/día** gratuitas
- Después: $5 USD por cada 1,000 búsquedas
- Para 40k productos: ~$200 USD total (o ~13 meses gratis a 100/día)

## Uso

### 1. Subir catálogo
- Click en "Subir XLSX" en el menú
- Seleccionar el archivo `Catalogo_Mapy_Final_V4.xlsx`
- Esperar la importación (~30 segundos para 40k productos)

### 2. Buscar imágenes
- Ir a "Buscar Imágenes"
- Seleccionar categoría (ej: "ELECTRONICA")
- Click "Buscar" → el sistema busca imágenes automáticamente
- Revisar y seleccionar las mejores 2 imágenes por producto

### 3. Exportar
- Click en "Descargar XLSX"
- El archivo incluye las URLs de las imágenes seleccionadas

## Estructura del proyecto

```
mapyimage/
├── app.py              # API FastAPI (rutas y lógica)
├── config.py           # Configuración (API keys, paths)
├── database.py         # Capa de base de datos SQLite
├── image_search.py     # Integración Google Custom Search
├── xlsx_handler.py     # Importar/exportar Excel
├── requirements.txt    # Dependencias Python
├── .env.example        # Plantilla de configuración
├── Dockerfile          # Deploy con Docker
├── docker-compose.yml  # Docker Compose
├── run.sh / run.bat    # Scripts de inicio
├── templates/          # HTML (Jinja2)
│   ├── base.html
│   ├── dashboard.html
│   ├── upload.html
│   └── search.html
└── static/             # CSS, JS, imágenes
    ├── css/style.css
    ├── js/app.js
    └── images/placeholder.svg
```

## Deploy en la nube

### Docker
```bash
docker-compose up -d
```

### Railway
1. Conectar repo en [railway.app](https://railway.app)
2. Agregar variables de entorno (GOOGLE_API_KEY, GOOGLE_CX_ID)
3. Deploy automático

### Render
1. Conectar repo en [render.com](https://render.com)
2. Crear Web Service → Python
3. Build command: `pip install -r requirements.txt`
4. Start command: `uvicorn app:app --host 0.0.0.0 --port $PORT`

## Tecnologías

- **Backend**: Python, FastAPI, SQLite, Pandas
- **Frontend**: HTML5, TailwindCSS, JavaScript
- **API**: Google Custom Search JSON API
- **Deploy**: Docker, Railway, Render
