import sqlite3
from pathlib import Path
from config import DATABASE_PATH, SQLITE_CHECK_SAME_THREAD
from typing import Optional, List, Dict, Any

class Database:
    def __init__(self, db_path: str = DATABASE_PATH):
        self.db_path = db_path
        Path(db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def get_connection(self):
        """Get a database connection"""
        conn = sqlite3.connect(self.db_path, check_same_thread=SQLITE_CHECK_SAME_THREAD)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        """Initialize database tables"""
        conn = self.get_connection()
        cursor = conn.cursor()

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS products (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
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
                image_status TEXT DEFAULT 'pending',
                search_query TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Create indexes for performance
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_sku ON products(sku)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_categoria ON products(categoria)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_marca ON products(marca)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_status ON products(image_status)
        ''')
        cursor.execute('''
            CREATE INDEX IF NOT EXISTS idx_search ON products(nombre_es)
        ''')

        conn.commit()
        conn.close()

    def insert_product(self, product_data: Dict[str, Any]) -> int:
        """Insert a single product"""
        conn = self.get_connection()
        cursor = conn.cursor()

        try:
            cursor.execute('''
                INSERT INTO products (
                    sku, descripcion_original, marca, subcategoria, categoria,
                    nombre_es, nome_pt, desc_es, desc_pt, preco, image_status, search_query
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                product_data.get('search_query', '')
            ))
            conn.commit()
            product_id = cursor.lastrowid
            conn.close()
            return product_id
        except sqlite3.IntegrityError:
            conn.close()
            return -1  # Duplicate SKU

    def bulk_insert_products(self, products: List[Dict[str, Any]]) -> int:
        """Insert multiple products efficiently"""
        conn = self.get_connection()
        cursor = conn.cursor()
        inserted = 0

        for product in products:
            try:
                cursor.execute('''
                    INSERT INTO products (
                        sku, descripcion_original, marca, subcategoria, categoria,
                        nombre_es, nome_pt, desc_es, desc_pt, preco, image_status, search_query
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product.get('sku'),
                    product.get('descripcion_original'),
                    product.get('marca'),
                    product.get('subcategoria'),
                    product.get('categoria'),
                    product.get('nombre_es'),
                    product.get('nome_pt'),
                    product.get('desc_es'),
                    product.get('desc_pt'),
                    product.get('preco'),
                    product.get('image_status', 'pending'),
                    product.get('search_query', '')
                ))
                inserted += 1
            except sqlite3.IntegrityError:
                pass  # Skip duplicates

        conn.commit()
        conn.close()
        return inserted

    def get_product(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get a single product by ID"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM products WHERE id = ?', (product_id,))
        result = cursor.fetchone()
        conn.close()
        return dict(result) if result else None

    def get_products(
        self,
        page: int = 1,
        per_page: int = 24,
        categoria: Optional[str] = None,
        marca: Optional[str] = None,
        status: Optional[str] = None,
        search: Optional[str] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """Get paginated products with filters"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Build WHERE clause
        conditions = []
        params = []

        if categoria:
            conditions.append("categoria = ?")
            params.append(categoria)

        if marca:
            conditions.append("marca = ?")
            params.append(marca)

        if status:
            conditions.append("image_status = ?")
            params.append(status)

        if search:
            conditions.append("(nombre_es LIKE ? OR sku LIKE ?)")
            search_term = f"%{search}%"
            params.extend([search_term, search_term])

        where_clause = "WHERE " + " AND ".join(conditions) if conditions else ""

        # Count total
        count_query = f"SELECT COUNT(*) FROM products {where_clause}"
        cursor.execute(count_query, params)
        total = cursor.fetchone()[0]

        # Get paginated results
        offset = (page - 1) * per_page
        query = f"""
            SELECT * FROM products
            {where_clause}
            ORDER BY updated_at DESC
            LIMIT ? OFFSET ?
        """
        params.extend([per_page, offset])

        cursor.execute(query, params)
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return products, total

    def update_product_images(
        self,
        product_id: int,
        image_url_1: Optional[str] = None,
        image_url_2: Optional[str] = None,
        status: Optional[str] = None
    ) -> bool:
        """Update product images and status"""
        conn = self.get_connection()
        cursor = conn.cursor()

        updates = []
        params = []

        if image_url_1:
            updates.append("image_url_1 = ?")
            params.append(image_url_1)

        if image_url_2:
            updates.append("image_url_2 = ?")
            params.append(image_url_2)

        if status:
            updates.append("image_status = ?")
            params.append(status)

        if updates:
            updates.append("updated_at = CURRENT_TIMESTAMP")
            params.append(product_id)

            query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
            conn.close()
            return True

        conn.close()
        return False

    def get_stats(self) -> Dict[str, Any]:
        """Get dashboard statistics"""
        conn = self.get_connection()
        cursor = conn.cursor()

        # Total products
        cursor.execute("SELECT COUNT(*) FROM products")
        total = cursor.fetchone()[0]

        # By status
        cursor.execute("SELECT image_status, COUNT(*) FROM products GROUP BY image_status")
        status_counts = {row[0]: row[1] for row in cursor.fetchall()}

        # Unique categories and brands
        cursor.execute("SELECT COUNT(DISTINCT categoria) FROM products")
        total_categories = cursor.fetchone()[0]

        cursor.execute("SELECT COUNT(DISTINCT marca) FROM products")
        total_brands = cursor.fetchone()[0]

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
            "completion_percentage": round((status_counts.get("complete", 0) / total * 100) if total > 0 else 0, 1)
        }

    def get_categories(self) -> List[str]:
        """Get all unique categories"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT categoria FROM products WHERE categoria IS NOT NULL ORDER BY categoria")
        categories = [row[0] for row in cursor.fetchall()]
        conn.close()
        return categories

    def get_brands(self) -> List[str]:
        """Get all unique brands"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT DISTINCT marca FROM products WHERE marca IS NOT NULL ORDER BY marca")
        brands = [row[0] for row in cursor.fetchall()]
        conn.close()
        return brands

    def get_products_by_category(self, categoria: str) -> List[Dict[str, Any]]:
        """Get all products in a category (for batch search)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute(
            "SELECT * FROM products WHERE categoria = ? AND image_status = 'pending' LIMIT 100",
            (categoria,)
        )
        products = [dict(row) for row in cursor.fetchall()]
        conn.close()
        return products

    def count_total_products(self) -> int:
        """Get total count of products"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM products")
        count = cursor.fetchone()[0]
        conn.close()
        return count

    def clear_all_products(self) -> int:
        """Clear all products (for re-import)"""
        conn = self.get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM products")
        conn.commit()
        conn.close()
        return cursor.rowcount
