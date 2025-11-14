import io
import csv
from typing import Dict, Any, List
from sqlalchemy import text
from sqlalchemy.engine import Connection
from api.schemas.froms import ClienteFormData, ProductoFormData, OrdenFormData

class BulkUploadService:
    def __init__(self, conn: Connection):
        self.conn = conn

    def _parse_file(self, file_content: bytes, filename: str) -> List[Dict[str, str]]:
        """
        Parse the uploaded file content based on the file extension.
        """
        try:
            if filename.endswith('.csv'):
                text_content = file_content.decode('utf-8')
                reader = csv.DictReader(io.StringIO(text_content))
                
                if not reader.fieldnames:
                    raise ValueError("CSV file is empty")
                
                return [row for row in reader]
            
            raise ValueError("Unsupported file type")
        
        except Exception as e:
            raise ValueError(f"Error processing file: {str(e)}")

    def bulk_upload_clientes(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        try:
            rows = self._parse_file(file_content, filename)
            inserted = 0
            reactivated = 0
            skipped = 0
            errors = []
            
            for row_num, row in enumerate(rows, start=2):
                try:
                    row = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
                    
                    check_q = text("""
                        SELECT ClienteId, Activo FROM Ventas_Transactional.dbo.Cliente 
                        WHERE Email = :email;
                    """)
                    existing = self.conn.execute(check_q, {"email": row.get('Email')}).mappings().first()
                    
                    if existing:
                        if existing["Activo"]:
                            skipped += 1
                            continue
                        upd = text("""
                            UPDATE Ventas_Transactional.dbo.Cliente
                            SET Activo = 1, Nombre = :nombre, Genero = :genero, Pais = :pais
                            WHERE ClienteId = :id;
                        """)
                        self.conn.execute(upd, {
                            "nombre": row.get('Nombre'),
                            "genero": row.get('Genero'),
                            "pais": row.get('Pais'),
                            "id": existing["ClienteId"]
                        })
                        reactivated += 1
                    else:
                        q = text("""
                            INSERT INTO Ventas_Transactional.dbo.Cliente 
                            (Nombre, Email, Genero, Pais)
                            VALUES (:nombre, :email, :genero, :pais);
                        """)
                        self.conn.execute(q, {
                            "nombre": row.get('Nombre'),
                            "email": row.get('Email'),
                            "genero": row.get('Genero'),
                            "pais": row.get('Pais')
                        })
                        inserted += 1
                except Exception as e:
                    errors.append({"row": row_num, "error": str(e)})
            
            return {
                "success": True,
                "inserted": inserted,
                "reactivated": reactivated,
                "skipped": skipped,
                "errors": errors or None
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    def bulk_upload_productos(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        try:
            rows = self._parse_file(file_content, filename)
            inserted = 0
            reactivated = 0
            skipped = 0
            errors = []
            
            for row_num, row in enumerate(rows, start=2):
                try:
                    row = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
                    
                    check_q = text("""
                        SELECT ProductoId, Activo FROM Ventas_Transactional.dbo.Producto 
                        WHERE SKU = :sku;
                    """)
                    existing = self.conn.execute(check_q, {"sku": row.get('SKU')}).mappings().first()
                    
                    if existing:
                        if existing["Activo"]:
                            skipped += 1
                            continue
                        upd = text("""
                            UPDATE Ventas_Transactional.dbo.Producto
                            SET Activo = 1, Nombre = :nombre, Categoria = :categoria
                            WHERE ProductoId = :id;
                        """)
                        self.conn.execute(upd, {
                            "nombre": row.get('Nombre'),
                            "categoria": row.get('Categoria'),
                            "id": existing["ProductoId"]
                        })
                        reactivated += 1
                    else:
                        q = text("""
                            INSERT INTO Ventas_Transactional.dbo.Producto 
                            (SKU, Nombre, Categoria)
                            VALUES (:sku, :nombre, :categoria);
                        """)
                        self.conn.execute(q, {
                            "sku": row.get('SKU'),
                            "nombre": row.get('Nombre'),
                            "categoria": row.get('Categoria')
                        })
                        inserted += 1
                except Exception as e:
                    errors.append({"row": row_num, "error": str(e)})
            
            return {
                "success": True,
                "inserted": inserted,
                "reactivated": reactivated,
                "skipped": skipped,
                "errors": errors or None
            }
        except Exception as e:
            return {"success": False, "message": str(e)}

    def bulk_upload_ordenes(self, file_content: bytes, filename: str) -> Dict[str, Any]:
        try:
            rows = self._parse_file(file_content, filename)
            inserted = 0
            errors = []
            
            for row_num, row in enumerate(rows, start=2):
                try:
                    row = {k: (v.strip() if isinstance(v, str) else v) for k, v in row.items()}
                    
                    q = text("""
                        INSERT INTO Ventas_Transactional.dbo.Orden 
                        (ClienteId, Fecha, Canal, Moneda, Total)
                        VALUES (:cliente_id, :fecha, :canal, :moneda, :total);
                    """)
                    self.conn.execute(q, {
                        "cliente_id": int(row.get('ClienteId')),
                        "fecha": row.get('Fecha'),
                        "canal": row.get('Canal'),
                        "moneda": row.get('Moneda'),
                        "total": float(row.get('Total'))
                    })
                    inserted += 1
                except Exception as e:
                    errors.append({"row": row_num, "error": str(e)})
            
            return {
                "success": True,
                "inserted": inserted,
                "errors": errors or None
            }
        except Exception as e:
            return {"success": False, "message": str(e)}