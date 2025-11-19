from typing import Dict, Any, Optional, List
from sqlalchemy import text
from sqlalchemy.engine import Connection
import io
import csv

class DWService:
    def __init__(self, conn: Connection):
        self.conn = conn

    def get_dimclientes(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        offset = (page - 1) * limit
        q = text("""
        SELECT ClienteID, ClienteKeyNatural, Nombre, Email, Genero, Pais, 
               FechaRegistro, SourceSystem, EsRegistroActual
        FROM dbo.DimCliente
        WHERE Activo = 1
        ORDER BY ClienteID
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;
        """)
        total_q = text("SELECT COUNT(1) AS total FROM dbo.DimCliente WHERE Activo = 1;")
        res = self.conn.execute(q, {"offset": offset, "limit": limit})
        rows = [dict(r) for r in res.mappings().all()]
        total = self.conn.execute(total_q).scalar_one()
        return {"data": rows, "total": total}

    def get_dimcliente_by_id(self, cliente_id: int) -> Optional[Dict[str, Any]]:
        q = text("""
        SELECT ClienteID, ClienteKeyNatural, Nombre, Email, Genero, Pais, 
               FechaRegistro, SourceSystem, EsRegistroActual
        FROM dbo.DimCliente
        WHERE ClienteID = :id AND Activo = 1;
        """)
        res = self.conn.execute(q, {"id": cliente_id})
        row = res.mappings().first()
        return dict(row) if row else None

    def get_dimproductos(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        offset = (page - 1) * limit
        q = text("""
        SELECT ProductoID, SKU, Nombre, Categoria, SourceSystem, EsRegistroActual
        FROM dbo.DimProducto
        WHERE Activo = 1
        ORDER BY ProductoID
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;
        """)
        total_q = text("SELECT COUNT(1) AS total FROM dbo.DimProducto WHERE Activo = 1;")
        res = self.conn.execute(q, {"offset": offset, "limit": limit})
        rows = [dict(r) for r in res.mappings().all()]
        total = self.conn.execute(total_q).scalar_one()
        return {"data": rows, "total": total}

    def get_dimproducto_by_id(self, producto_id: int) -> Optional[Dict[str, Any]]:
        q = text("""
        SELECT ProductoID, SKU, Nombre, Categoria, SourceSystem, EsRegistroActual
        FROM dbo.DimProducto
        WHERE ProductoID = :id AND Activo = 1;
        """)
        res = self.conn.execute(q, {"id": producto_id})
        row = res.mappings().first()
        return dict(row) if row else None

    def get_dimtiempos(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        offset = (page - 1) * limit
        q = text("""
        SELECT TiempoID, Fecha, Anio, Semestre, Trimestre, Mes, NombreMes, Dia, 
               DiaSemana, NombreDiaSemana, EsFinDeSemana, MesAnio
        FROM dbo.DimTiempo
        WHERE Activo = 1
        ORDER BY TiempoID
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;
        """)
        total_q = text("SELECT COUNT(1) AS total FROM dbo.DimTiempo WHERE Activo = 1;")
        res = self.conn.execute(q, {"offset": offset, "limit": limit})
        rows = [dict(r) for r in res.mappings().all()]
        total = self.conn.execute(total_q).scalar_one()
        return {"data": rows, "total": total}

    def get_dimtiempo_by_id(self, tiempo_id: int) -> Optional[Dict[str, Any]]:
        q = text("""
        SELECT TiempoID, Fecha, Anio, Semestre, Trimestre, Mes, NombreMes, Dia, 
               DiaSemana, NombreDiaSemana, EsFinDeSemana, MesAnio
        FROM dbo.DimTiempo
        WHERE TiempoID = :id AND Activo = 1;
        """)
        res = self.conn.execute(q, {"id": tiempo_id})
        row = res.mappings().first()
        return dict(row) if row else None

    def get_factventas(self, page: int = 1, limit: int = 50) -> Dict[str, Any]:
        offset = (page - 1) * limit
        q = text("""
        SELECT VentaID, ClienteID, ProductoID, TiempoID, CanalID, OrdenKeyNatural,
               MonedaOrigen, TotalUSD, Cantidad, PrecioUnitUSD, DescuentoPct,
               TipoCambioAplicado, SourceSystem, FechaCarga
        FROM dbo.FactVentas
        WHERE Activo = 1
        ORDER BY VentaID DESC
        OFFSET :offset ROWS FETCH NEXT :limit ROWS ONLY;
        """)
        total_q = text("SELECT COUNT(1) AS total FROM dbo.FactVentas WHERE Activo = 1;")
        res = self.conn.execute(q, {"offset": offset, "limit": limit})
        rows = [dict(r) for r in res.mappings().all()]
        total = self.conn.execute(total_q).scalar_one()
        return {"data": rows, "total": total}

    def _bulk_insert_rows(self, table: str, allowed_cols: List[str], reader: csv.DictReader) -> Dict[str, Any]:
        inserted = 0
        errors: List[Dict[str, Any]] = []
        cols = [c for c in reader.fieldnames or [] if c in allowed_cols]
        if not cols:
            return {"success": False, "message": "No valid columns in CSV for table " + table}
        col_list_sql = ", ".join(cols)
        param_list = ", ".join([f":{c}" for c in cols])
        q = text(f"INSERT INTO {table} ({col_list_sql}) VALUES ({param_list});")
        for row_num, row in enumerate(reader, start=2):
            try:
                params = {c: (row.get(c) if row.get(c) != "" else None) for c in cols}
                with self.conn.begin():
                    self.conn.execute(q, params)
                inserted += 1
            except Exception as e:
                errors.append({"row": row_num, "error": str(e)})
        return {"success": True, "inserted": inserted, "errors": errors or None}

    def bulk_upload_dimcliente(self, file_content: bytes) -> Dict[str, Any]:
        text_content = file_content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text_content))
        # allowed DW columns for DimCliente
        allowed = ["ClienteID","ClienteKeyNatural","Nombre","Email","Genero","Pais","FechaRegistro",
                   "SourceSystem","FechaInicioValidez","FechaFinValidez","EsRegistroActual","Activo"]
        return self._bulk_insert_rows("dbo.DimCliente", allowed, reader)

    def bulk_upload_dimproducto(self, file_content: bytes) -> Dict[str, Any]:
        text_content = file_content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text_content))
        allowed = ["ProductoID","SKU","Nombre","Categoria","SourceSystem",
                   "FechaInicioValidez","FechaFinValidez","EsRegistroActual","Activo"]
        return self._bulk_insert_rows("dbo.DimProducto", allowed, reader)

    def bulk_upload_dimtiempo(self, file_content: bytes) -> Dict[str, Any]:
        text_content = file_content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text_content))
        allowed = ["TiempoID","Fecha","Anio","Semestre","Trimestre","Mes","NombreMes",
                   "Dia","DiaSemana","NombreDiaSemana","EsFinDeSemana","MesAnio","Activo"]
        return self._bulk_insert_rows("dbo.DimTiempo", allowed, reader)

    def bulk_upload_factventas(self, file_content: bytes) -> Dict[str, Any]:
        text_content = file_content.decode("utf-8")
        reader = csv.DictReader(io.StringIO(text_content))
        allowed = ["VentaID","ClienteID","ProductoID","TiempoID","CanalID","OrdenKeyNatural",
                   "MonedaOrigen","TotalUSD","Cantidad","PrecioUnitUSD","DescuentoPct",
                   "TipoCambioAplicado","SourceSystem","FechaCarga","Activo"]
        return self._bulk_insert_rows("dbo.FactVentas", allowed, reader)