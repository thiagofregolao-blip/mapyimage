import pandas as pd
from pathlib import Path
from typing import List, Dict, Any, Tuple
from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
import logging

logger = logging.getLogger(__name__)

class XLSXHandler:
    """Handle XLSX file import and export"""

    @staticmethod
    def import_from_xlsx(file_path: str) -> Tuple[List[Dict[str, Any]], int, List[str]]:
        """
        Import products from XLSX file
        Returns: (products_list, count, errors_list)
        """
        errors = []

        try:
            # Read XLSX
            df = pd.read_excel(file_path, sheet_name=0)

            # Normalize column names (handle various formats)
            column_mapping = {
                'SKU': 'sku',
                'sku': 'sku',
                'DESCRIPCION': 'descripcion_original',
                'DESCRIPCION_ORIGINAL': 'descripcion_original',
                'DESCRIPCION ORIGINAL': 'descripcion_original',
                'MARCA': 'marca',
                'marca': 'marca',
                'SUBCATEGORIA': 'subcategoria',
                'subcategoria': 'subcategoria',
                'CATEGORIA': 'categoria',
                'categoria': 'categoria',
                'NOMBRE_ESTANDAR_ES': 'nombre_es',
                'NOMBRE_ES': 'nombre_es',
                'NOMBRE ESTANDAR ES': 'nombre_es',
                'NOMBRE_ESTANDAR_ESPAÑOL': 'nombre_es',
                'NOME_PADRONIZADO_PT': 'nome_pt',
                'NOME_PT': 'nome_pt',
                'NOME PADRONIZADO PT': 'nome_pt',
                'DESC_ECOMMERCE_ES': 'desc_es',
                'DESC_ES': 'desc_es',
                'DESC ECOMMERCE ES': 'desc_es',
                'DESC_ECOMMERCE_PT': 'desc_pt',
                'DESC_PT': 'desc_pt',
                'DESC ECOMMERCE PT': 'desc_pt',
                'URL_IMAGEN': 'image_url_1',
                'URL_IMAGE': 'image_url_1',
                'IMAGE_URL': 'image_url_1',
                'PRECO': 'preco',
                'PRECIO': 'preco',
                'PRICE': 'preco',
                'PRECIO_USD': 'preco',
            }

            # Rename columns
            df = df.rename(columns=column_mapping)

            # Filter to required columns
            required_columns = [
                'sku', 'descripcion_original', 'marca', 'subcategoria',
                'categoria', 'nombre_es', 'nome_pt', 'desc_es', 'desc_pt', 'preco'
            ]

            for col in required_columns:
                if col not in df.columns:
                    df[col] = None

            df = df[required_columns + [col for col in df.columns if col not in required_columns]]

            # Handle optional image_url_1 column
            if 'image_url_1' not in df.columns:
                df['image_url_1'] = None

            products = []
            for idx, row in df.iterrows():
                try:
                    sku = str(row['sku']).strip() if pd.notna(row['sku']) else None

                    if not sku:
                        errors.append(f"Row {idx + 2}: SKU is required")
                        continue

                    product = {
                        'sku': sku,
                        'descripcion_original': str(row['descripcion_original']).strip() if pd.notna(row['descripcion_original']) else None,
                        'marca': str(row['marca']).strip() if pd.notna(row['marca']) else None,
                        'subcategoria': str(row['subcategoria']).strip() if pd.notna(row['subcategoria']) else None,
                        'categoria': str(row['categoria']).strip() if pd.notna(row['categoria']) else None,
                        'nombre_es': str(row['nombre_es']).strip() if pd.notna(row['nombre_es']) else None,
                        'nome_pt': str(row['nome_pt']).strip() if pd.notna(row['nome_pt']) else None,
                        'desc_es': str(row['desc_es']).strip() if pd.notna(row['desc_es']) else None,
                        'desc_pt': str(row['desc_pt']).strip() if pd.notna(row['desc_pt']) else None,
                        'preco': float(row['preco']) if pd.notna(row['preco']) else None,
                        'image_url_1': str(row['image_url_1']).strip() if pd.notna(row['image_url_1']) and row['image_url_1'] != 'None' else None,
                        'image_status': 'complete' if pd.notna(row['image_url_1']) and str(row['image_url_1']).strip() and str(row['image_url_1']).strip() != 'None' else 'pending',
                        'search_query': ''
                    }

                    products.append(product)

                except Exception as e:
                    errors.append(f"Row {idx + 2}: {str(e)}")

            logger.info(f"Imported {len(products)} products from XLSX")
            return products, len(products), errors

        except Exception as e:
            logger.error(f"XLSX import error: {str(e)}")
            return [], 0, [f"XLSX import error: {str(e)}"]

    @staticmethod
    def export_to_xlsx(products: List[Dict[str, Any]], output_path: str = "exports/productos_updated.xlsx"):
        """Export products to XLSX with images"""
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)

        try:
            df = pd.DataFrame(products)

            # Rename columns back to original format
            column_mapping = {
                'sku': 'SKU',
                'descripcion_original': 'DESCRIPCION',
                'marca': 'MARCA',
                'subcategoria': 'SUBCATEGORIA',
                'categoria': 'CATEGORIA',
                'nombre_es': 'NOMBRE_ESTANDAR_ES',
                'nome_pt': 'NOME_PADRONIZADO_PT',
                'desc_es': 'DESC_ECOMMERCE_ES',
                'desc_pt': 'DESC_ECOMMERCE_PT',
                'preco': 'PRECO',
                'image_url_1': 'URL_IMAGEN_1',
                'image_url_2': 'URL_IMAGEN_2',
                'image_status': 'IMAGE_STATUS'
            }

            df = df.rename(columns=column_mapping)

            # Select specific columns for export
            export_columns = [
                'SKU', 'DESCRIPCION', 'MARCA', 'SUBCATEGORIA', 'CATEGORIA',
                'NOMBRE_ESTANDAR_ES', 'NOME_PADRONIZADO_PT',
                'DESC_ECOMMERCE_ES', 'DESC_ECOMMERCE_PT',
                'PRECO', 'URL_IMAGEN_1', 'URL_IMAGEN_2', 'IMAGE_STATUS'
            ]

            # Only include columns that exist
            export_columns = [col for col in export_columns if col in df.columns]
            df = df[export_columns]

            # Write to Excel
            df.to_excel(output_path, index=False, sheet_name='Productos')

            logger.info(f"Exported {len(df)} products to {output_path}")
            return True

        except Exception as e:
            logger.error(f"XLSX export error: {str(e)}")
            return False
