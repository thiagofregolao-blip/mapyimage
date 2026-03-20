from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse, FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from starlette.requests import Request
from pathlib import Path
import logging
import asyncio
import os
from typing import Optional
import json

from database import Database
from image_search import get_searcher, cleanup_searcher
from xlsx_handler import XLSXHandler
from config import ITEMS_PER_PAGE, LANGUAGE

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize FastAPI
app = FastAPI(title="Mapy Image Manager", version="1.0.0")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Templates and static files
templates = Jinja2Templates(directory="templates")
app.mount("/static", StaticFiles(directory="static"), name="static")

# Database
db = Database()

# Track batch search progress
batch_progress = {}


# === STARTUP / SHUTDOWN ===
@app.on_event("startup")
async def startup_event():
    """Initialize on startup"""
    logger.info("Mapy Image Manager starting...")
    total_products = db.count_total_products()
    logger.info(f"Database initialized with {total_products} products")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on shutdown"""
    logger.info("Shutting down...")
    await cleanup_searcher()


# === DASHBOARD ROUTES ===
@app.get("/", response_class=HTMLResponse)
async def dashboard(request: Request):
    """Dashboard with product grid"""
    stats = db.get_stats()
    categories = db.get_categories()
    brands = db.get_brands()

    return templates.TemplateResponse("dashboard.html", {
        "request": request,
        "stats": stats,
        "categories": categories,
        "brands": brands,
        "language": LANGUAGE
    })


# === UPLOAD ROUTE ===
@app.post("/upload")
async def upload_xlsx(file: UploadFile = File(...)):
    """Upload and import XLSX file"""
    if not file.filename.endswith(('.xlsx', '.xls')):
        raise HTTPException(status_code=400, detail="Only XLSX/XLS files allowed")

    try:
        # Save uploaded file temporarily
        upload_dir = Path("uploads")
        upload_dir.mkdir(exist_ok=True)
        temp_path = upload_dir / file.filename

        contents = await file.read()
        with open(temp_path, "wb") as f:
            f.write(contents)

        # Import from XLSX
        products, count, errors = XLSXHandler.import_from_xlsx(str(temp_path))

        if products:
            # Upsert: new SKUs are inserted, existing SKUs have catalog data
            # updated but their images are preserved
            result = db.bulk_upsert_products(products)

            # Clean up temp file
            temp_path.unlink()

            stats = db.get_stats()

            return {
                "success": True,
                "message": (
                    f"Import complete: {result['inserted']} new, "
                    f"{result['updated']} updated (images preserved)"
                ),
                "imported": result["inserted"],
                "updated": result["updated"],
                "errors": errors,
                "stats": stats
            }
        else:
            raise HTTPException(status_code=400, detail="No valid products found in file")

    except Exception as e:
        logger.error(f"Upload error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# === API ROUTES ===
@app.get("/api/products")
async def get_products(
    page: int = 1,
    categoria: Optional[str] = None,
    marca: Optional[str] = None,
    status: Optional[str] = None,
    search: Optional[str] = None
):
    """Get products with filters and pagination"""
    if page < 1:
        page = 1

    products, total = db.get_products(
        page=page,
        per_page=ITEMS_PER_PAGE,
        categoria=categoria,
        marca=marca,
        status=status,
        search=search
    )

    total_pages = (total + ITEMS_PER_PAGE - 1) // ITEMS_PER_PAGE

    return {
        "success": True,
        "data": products,
        "pagination": {
            "current_page": page,
            "total_pages": total_pages,
            "total_items": total,
            "items_per_page": ITEMS_PER_PAGE
        }
    }


@app.get("/api/product/{product_id}")
async def get_product_detail(product_id: int):
    """Get product details"""
    product = db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return {"success": True, "data": product}


@app.get("/api/stats")
async def get_stats():
    """Get dashboard statistics"""
    stats = db.get_stats()
    return {"success": True, "data": stats}


# === IMAGE SEARCH ROUTES ===
@app.post("/api/search-images/{product_id}")
async def search_images(product_id: int):
    """Search images for a single product"""
    product = db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        searcher = await get_searcher()
        images = await searcher.search_product_images(product)

        return {
            "success": True,
            "product_id": product_id,
            "product_name": product.get("nombre_es", ""),
            "images": images
        }
    except Exception as e:
        logger.error(f"Search error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@app.post("/api/search-images-batch")
async def search_images_batch(
    background_tasks: BackgroundTasks,
    categoria: Optional[str] = None
):
    """Start batch image search for category"""
    if not categoria:
        raise HTTPException(status_code=400, detail="Category required")

    batch_id = f"batch_{categoria}_{int(asyncio.get_event_loop().time())}"
    batch_progress[batch_id] = {
        "status": "started",
        "categoria": categoria,
        "total": 0,
        "processed": 0,
        "successful": 0,
        "errors": []
    }

    # Get products in category
    products = db.get_products_by_category(categoria)
    batch_progress[batch_id]["total"] = len(products)

    if not products:
        batch_progress[batch_id]["status"] = "completed"
        return {
            "success": True,
            "batch_id": batch_id,
            "message": "No products to search"
        }

    # Run in background
    background_tasks.add_task(run_batch_search, batch_id, products)

    return {
        "success": True,
        "batch_id": batch_id,
        "message": f"Batch search started for {len(products)} products"
    }


async def run_batch_search(batch_id: str, products: list):
    """Background task for batch search"""
    try:
        searcher = await get_searcher()

        for product in products:
            try:
                images = await searcher.search_product_images(product)

                if images:
                    db.update_product_images(
                        product['id'],
                        image_url_1=images[0].get("url"),
                        image_url_2=images[1].get("url") if len(images) > 1 else None,
                        status="complete"
                    )
                    batch_progress[batch_id]["successful"] += 1
                else:
                    db.update_product_images(
                        product['id'],
                        status="no_image"
                    )

            except Exception as e:
                logger.error(f"Error processing product {product['id']}: {str(e)}")
                batch_progress[batch_id]["errors"].append(str(e))

            batch_progress[batch_id]["processed"] += 1

        batch_progress[batch_id]["status"] = "completed"

    except Exception as e:
        logger.error(f"Batch search error: {str(e)}")
        batch_progress[batch_id]["status"] = "error"
        batch_progress[batch_id]["errors"].append(str(e))


@app.get("/api/batch-progress/{batch_id}")
async def get_batch_progress(batch_id: str):
    """Get batch search progress"""
    if batch_id not in batch_progress:
        raise HTTPException(status_code=404, detail="Batch not found")

    return {
        "success": True,
        "data": batch_progress[batch_id]
    }


# === SAVE IMAGE ROUTE ===
@app.post("/api/save-image/{product_id}")
async def save_image(product_id: int, payload: dict):
    """Save selected image to product"""
    product = db.get_product(product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    try:
        image_url = payload.get("image_url")
        position = int(payload.get("position", 1))

        if not image_url:
            raise HTTPException(status_code=400, detail="image_url is required")

        if position == 1:
            db.update_product_images(product_id, image_url_1=image_url)
        elif position == 2:
            db.update_product_images(product_id, image_url_2=image_url)
        else:
            raise HTTPException(status_code=400, detail="Invalid position")

        # Update status if both images saved
        updated_product = db.get_product(product_id)
        if updated_product['image_url_1'] and updated_product['image_url_2']:
            db.update_product_images(product_id, status="complete")
        elif updated_product['image_url_1']:
            db.update_product_images(product_id, status="partial")

        return {
            "success": True,
            "message": "Image saved successfully"
        }
    except Exception as e:
        logger.error(f"Save error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# === CLEAR ALL PRODUCTS ROUTE ===
@app.delete("/api/products/clear")
async def clear_all_products():
    """Delete all products from database"""
    count = db.clear_all_products()
    return {"success": True, "message": f"Deleted {count} products"}


# === EXPORT ROUTE ===
@app.get("/api/export")
async def export_products():
    """Export all products to XLSX"""
    try:
        # Get all products
        products = []
        page = 1
        while True:
            batch, total = db.get_products(page=page, per_page=1000)
            if not batch:
                break
            products.extend(batch)
            page += 1

        # Export to XLSX
        export_path = "exports/Catalogo_Mapy_Updated.xlsx"
        success = XLSXHandler.export_to_xlsx(products, export_path)

        if success:
            return FileResponse(
                export_path,
                media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                filename="Catalogo_Mapy_Updated.xlsx"
            )
        else:
            raise HTTPException(status_code=500, detail="Export failed")

    except Exception as e:
        logger.error(f"Export error: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


# === TEMPLATE ROUTES ===
@app.get("/upload", response_class=HTMLResponse)
async def upload_page(request: Request):
    """Upload page"""
    return templates.TemplateResponse("upload.html", {
        "request": request,
        "language": LANGUAGE
    })


@app.get("/search", response_class=HTMLResponse)
async def search_page(request: Request):
    """Search page"""
    categories = db.get_categories()
    return templates.TemplateResponse("search.html", {
        "request": request,
        "categories": categories,
        "language": LANGUAGE
    })


# === ERROR HANDLERS ===
@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    """Handle HTTP exceptions"""
    return JSONResponse(
        status_code=exc.status_code,
        content={"success": False, "error": exc.detail}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception):
    """Handle general exceptions"""
    logger.error(f"Unhandled exception: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"success": False, "error": "Internal server error"}
    )


# ============================================================
# IMAGE DOWNLOADER ROUTES
# ============================================================
from image_downloader import ImageDownloader
import threading

download_state = {"status": "idle", "processed": 0, "total": 0, "complete": 0,
                  "partial": 0, "failed": 0, "api_calls": 0, "downloaded": 0,
                  "recent_logs": [], "stop_flag": False}


@app.get("/image-manager", response_class=HTMLResponse)
async def image_manager_page(request: Request):
    return templates.TemplateResponse("image_manager.html", {"request": request})


@app.post("/api/batch-download")
async def start_batch_download(request: Request):
    data = await request.json()
    category = data.get("category")
    api_key = data.get("api_key")
    cx_id = data.get("cx_id")
    imgs_per = data.get("images_per_product", 3)

    if not all([category, api_key, cx_id]):
        raise HTTPException(400, "Missing parameters")

    download_state.update({"status": "running", "processed": 0, "total": 0,
                           "complete": 0, "partial": 0, "failed": 0,
                           "api_calls": 0, "downloaded": 0, "recent_logs": [],
                           "stop_flag": False})

    async def run_download():
        downloader = ImageDownloader(api_key=api_key, cx_id=cx_id)
        await downloader.init()
        try:
            # Find xlsx
            import glob
            xlsx_files = glob.glob("uploads/*.xlsx") + glob.glob("../Catalogo_Mapy_Final_V4.xlsx")
            products = db.get_products(category=category, limit=50000)

            download_state["total"] = len(products)

            for i, prod in enumerate(products):
                if download_state["stop_flag"]:
                    break

                result = await downloader.process_product(prod, f"data/images/{category.replace('/','_')}")
                download_state["processed"] = i + 1
                download_state["api_calls"] = downloader.daily_count

                if result["status"] == "complete":
                    download_state["complete"] += 1
                    download_state["downloaded"] += len(result.get("images", []))
                    # Save URLs to DB
                    urls = [img["url"] for img in result.get("images", [])]
                    if len(urls) >= 1:
                        db.update_product_image(prod["id"], urls[0], urls[1] if len(urls) > 1 else None)
                elif result["status"] == "partial":
                    download_state["partial"] += 1
                    download_state["downloaded"] += len(result.get("images", []))
                    urls = [img["url"] for img in result.get("images", [])]
                    if urls:
                        db.update_product_image(prod["id"], urls[0], None)
                else:
                    download_state["failed"] += 1

                if downloader.daily_count >= 95:
                    download_state["recent_logs"].append("⚠️ Límite diario API alcanzado!")
                    break

        finally:
            await downloader.close()
            download_state["status"] = "done"

    asyncio.create_task(run_download())
    return {"success": True, "message": "Download started"}


@app.get("/api/download-progress")
async def get_download_progress():
    return download_state


@app.post("/api/stop-download")
async def stop_download():
    download_state["stop_flag"] = True
    return {"success": True}


@app.get("/api/export-images")
async def export_with_images():
    """Export XLSX with image URLs"""
    products = db.get_products(limit=50000)
    if not products:
        raise HTTPException(404, "No products found")

    import openpyxl
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.title = "Products"
    headers = ["SKU", "DESCRIPCION", "MARCA", "CATEGORIA", "SUBCATEGORIA",
               "NOMBRE_ES", "NOME_PT", "IMAGE_URL_1", "IMAGE_URL_2", "STATUS"]
    ws.append(headers)

    for p in products:
        ws.append([p.get("sku"), p.get("descripcion_original"), p.get("marca"),
                   p.get("categoria"), p.get("subcategoria"),
                   p.get("nombre_es"), p.get("nome_pt"),
                   p.get("image_url_1", ""), p.get("image_url_2", ""),
                   p.get("image_status", "pending")])

    filepath = "data/export_with_images.xlsx"
    wb.save(filepath)
    return FileResponse(filepath, filename="Catalogo_Mapy_Con_Imagenes.xlsx")


if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))
    uvicorn.run(app, host="0.0.0.0", port=port)
