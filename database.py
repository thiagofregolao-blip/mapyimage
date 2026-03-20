import psycopg2
import psycopg2.extras
from config import DATABASE_URL
from typing import Optional, List, Dict, Any


class Database:
    def __init__(self, db_url: str = DATABASE_URL):
        if not db_url:
            raise RuntimeError("DATABASE_URL environment variable is not set")
        self.db_url = db_url
        self.init_db()

    def get_connection(self):
        """Get a database connection with dict-like row access"""
        conn = psycopg2.connect(self.db_url)
        conn.autocommit = False
        return conn

    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id SERIAL PRIMARY KEY,
                sku TEXT UNIQUE NOT NULL,
                descripcion_original TEXT,
                marca TEXT,
                subcategoria TEXT,
                categoria TEXT,
                nombre_es TEXT,
                nome_pt TEXT,
                desc_es TEXT,
                desc_pt TEXT,
                preco REAL,
                image_url_1 TEXT,
                image_url_2 TEXT,
                image_status TEXT DEFAULT \'pending\',
                search_query TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        cursor.execute('CREATE INDEX IF NOT EXISTS idx_sku ON products(sku)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_categoria ON products(categoria)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_marca ON products(marca)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_status ON products(image_status)')
        cursor.execute('CREATE INDEX IF NOT EXISTS idx_search ON products(nombre_es)')

        conn.commit()
        cursor.close()
        conn.close()

    def _row_to_dict(self, cursor, row) -> Dict[str, Any]:
        """Convert a psycopg2 row to dict using column names"""
        cols = [desc[0] for desc in cursor.description]
        return dict(zip(cols, row))

    def insert_product(self, product_data: Dict[str, Any]) -> int:
        """Insert a single product"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO products (
                    sku, descripcion_original, marca, subcategoria, categoria,
                    nombre_es, nome_pt, desc_es, desc_pt, preco, image_status, search_query
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
            ''', (
                product_data.get('sku'),
                product_data.get('descripcion_original'),
                product_data.get('marca'),
                product_data.get('subcategoria'),
                product_data.get('categoria'),
                product_data.get('nombre_es'),
                product_data.get('nome_pt'),
                product_data.get('desc_es'),
                product_data.get('desc_pt'),
                product_data.get('preco'),
                product_data.get('image_status', 'pending'),
                product_data.get('search_query', ''),
            ))
            product_id = cursor.fetchone()[0]
            conn.commit()
            cursor.close()
            conn.close()
            return product_id
        except psycopg2.IntegrityError:
            conn.rollback()
            cursor.close()
            conn.close()
            return -1  # Duplicate SKU

    def bulk_upsert_products(self, products: List[Dict[str, Any]]) -> Dict[str, int]:
        """
        Upsert products: insert new ones, update catalog data for existing ones.
        Images and image_status are NEVER overwritten for existing products,
        unless the XLSX itself already carries an image URL.
        """
        conn = self.get_connection()
        cursor = conn.cursor()
        inserted = updated = 0

        for product in products:
            sku = product.get('sku')
            if not sku:
                continue

            cursor.execute(
                'SELECT id, image_url_1, image_url_2, image_status FROM products WHERE sku = %s',
                (sku,)
            )
            existing = cursor.fetchone()

            if existing:
                _id, ex_url1, ex_url2, ex_status = existing
                new_image_url_1 = product.get('image_url_1') or ex_url1
                new_image_status = ex_status
                if product.get('image_url_1') and not ex_url1:
                    new_image_status = 'complete'

                cursor.execute('''
                    UPDATE products SET
                        descripcion_original = %s,
                        marca = %s,
                        subcategoria = %s,
                        categoria = %s,
                        nombre_es = %s,
                        nome_pt = %s,
                        desc_es = %s,
                        desc_pt = %s,
                        preco = %s,
                        image_url_1 = %s,
                        image_status = %s,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE sku = %s
                ''', (
                    product.get('descripcion_original'),
                    product.get('marca'),
                    product.get('subcategoria'),
                    product.get('categoria'),
                    product.get('nombre_es'),
                    product.get('nome_pt'),
                    product.get('desc_es'),
                    product.get('desc_pt'),
                    product.get('preco'),
                    new_image_url_1,
                    new_image_status,
                    sku,
                ))
                updated += 1
            else:
                cursor.execute('''
                    INSERT INTO products (
                        sku, descripcion_original, marca, subcategoria, categoria,
                        nombre_es, nome_pt, desc_es, desc_pt, preco, image_url_1, image_status, search_query
                    ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                ''', (
                    sku,
                    product.get('descripcion_original'),
                    product.get('marca'),
                    product.get('subcategoria'),
                    product.get('categoria'),
                    product.get('nombre_es'),
                    product.get('nome_pt'),
                    product.get('desc_es'),
                    product.get('desc_pt'),
                    product.get('preco'),
                    product.get('image_url_1'),
                    product.get('image_status', 'pending'),
                    product.get('search_query', ''),
                ))
                inserted += 1

        conn.commit()
        cursor.close()
        conn.close()
        return {"inserted": inserted, "updated": updated}

    def bulk_insert_products(self, products: List[Dict[str, Any]]) -> int:
        """Kept for compatibility — delegates to bulk_upsert_products."""
        result = self.bulk_upsert_products(products)
        return result["inserted"] + result["updated"]

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a single product by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE id = %s', (product_id,))
        row = cursor.fetchone()
        result = self._row_to_dict(cursor, row) if row else None
        cursor.close()
        conn.close()
        return result

    def get_products(
        self,
        page: int = 1,
        per_page: int = 24,
        categoria: Optional[str] = None,
        marca: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None,
    ) -> tuple:
        """Get paginated products with filters"""
        conn = self.get_connection()
        cursor = conn.cursor()

        conditions = []
        params = []

        if categoria:
            conditions.append("categoria = %s")
            params.append(categoria)
        if marca:
            conditions.append("marca = %s")
            params.append(marca)
        if status:
            conditions.append("image_status = %s")
            params.append(status)
        if search:
            conditions.append("(nombre_es ILIKE %s OR sku ILIKE %s)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        cursor.execute(f"SELECT COUNT(*) FROM products {where_clause}", params)
        total = cursor.fetchone()[0]

        offset = (page - 1) * per_page
        cursor.execute(
            f"""
            SELECT * FROM products
            {where_clause}
            ORDER BY updated_at DESC
            LIMIT %s OFFSET %s
            """,
            params + [per_page, offset],
        )
        rows = cursor.fetchall()
        products = [self._row_to_dict(cursor, r) for r in rows]
        cursor.close()
        conn.close()
        return products, total

    def update_product_images(
        self,
        product_id: int,
        image_url_1: Optional[str] = None,
        image_url_2: Optional[str] = None,
        status: Optional[str] = None,
    ) -> bool:
        """Update product images and status"""
        conn = self.get_connection()
        cursor = conn.cursor()

        updates = []
        params = []

        if image_url_1:
            updates.append("image_url_1 = %s")
            params.append(image_url_1)
        if image_url_2:
            updates.append("image_url_2 = %s")
            params.append(image_url_2)
        if status:
            updates.append("image_status = %s")
            params.append(status)

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(product_id)
            cursor.execute(
                f"UPDATE products SET {', '.join(updates)} WHERE id = %s",
                params,
            )
            conn.commit()
            cursor.close()
            conn.close()
            return True

        cursor.close()
        conn.close()
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute("SELECT COUNT(*) FROM products")
        total = cursor.fetchone()[0]

        cursor.execute("SELECT image_status, COUNT(*) FROM products GROUP BY image_status")
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}

        cursor.execute("SELECT COUNT(DISTINCT categoria) FROM products")
        total_categories = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT marca) FROM products")
        total_brands = cursor.fetchone()[0]

        cursor.close()
        conn.close()

        return {
            "total_products": total,
            "with_images": status_counts.get("complete", 0) + status_counts.get("partial", 0),
            "partial": status_counts.get("partial", 0),
            "pending": status_counts.get("pending", 0),
            "no_image": status_counts.get("no_image", 0),
            "complete": status_counts.get("complete", 0),
            "total_categories": total_categories,
            "total_brands": total_brands,
            "completion_percentage": round(
                (status_counts.get("complete", 0) / total * 100) if total > 0 else 0, 1
            ),
        }

    def get_categories(self) -> List[str]:
        """Get all unique categories"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT categoria FROM products WHERE categoria IS NOT NULL ORDER BY categoria"
        )
        categories = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return categories

    def get_brands(self) -> List[str]:
        """Get all unique brands"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT DISTINCT marca FROM products WHERE marca IS NOT NULL ORDER BY marca"
        )
        brands = [row[0] for row in cursor.fetchall()]
        cursor.close()
        conn.close()
        return brands

    def get_products_by_category(self, categoria: str) -> List[Dict[str, Any]]:
        """Get all products in a category for batch search"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM products WHERE categoria = %s LIMIT 100",
            (categoria,),
        )
        rows = cursor.fetchall()
        products = [self._row_to_dict(cursor, r) for r in rows]
        cursor.close()
        conn.close()
        return products

    def count_total_products(self) -> int:
        """Get total count of products"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        cursor.close()
        conn.close()
        return count

    def clear_all_products(self) -> int:
        """Clear all products (use with caution — images will be lost)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products")
        count = cursor.rowcount
        conn.commit()
        cursor.close()
        conn.close()
        return count
