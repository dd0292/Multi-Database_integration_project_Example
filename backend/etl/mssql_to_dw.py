import pyodbc
from decimal import Decimal
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

from etl.transformations.unify_gender import unify_gender
def get_mssql_source_conn():
    return pyodbc.connect(
        f"DRIVER={os.getenv('SQLSERVER_DRIVER')};"
        f"SERVER={os.getenv('SQLSERVER_HOST')},{os.getenv('SQLSERVER_PORT')};"
        f"DATABASE={os.getenv('SQLSERVER_DB_TRANSAC')};"
        f"UID={os.getenv('SQLSERVER_USER')};"
        f"PWD={os.getenv('SQLSERVER_PASSWORD')};"
    )

def get_sqlsrv_dw_conn():
    return pyodbc.connect(
        f"DRIVER={os.getenv('SQLSERVER_DRIVER')};"
        f"SERVER={os.getenv('SQLSERVER_HOST')},{os.getenv('SQLSERVER_PORT')};"
        f"DATABASE={os.getenv('SQLSERVER_DB_DW')};"
        f"UID={os.getenv('SQLSERVER_USER')};"
        f"PWD={os.getenv('SQLSERVER_PASSWORD')};"
    )
def extract_mssql_data():
    try:
        conn = get_mssql_source_conn()
        cur = conn.cursor()

        query = """
        SELECT 
            od.OrdenDetalleId,
            od.OrdenId,
            od.ProductoId,
            od.Cantidad,
            od.PrecioUnit,
            od.DescuentoPct,
            o.ClienteId,
            o.Fecha,
            o.Canal,
            o.Moneda,
            o.Total,
            c.Nombre as ClienteNombre,
            c.Genero as ClienteGenero,
            c.Pais as ClientePais,
            p.Nombre as ProductoNombre,
            p.SKU,
            p.Categoria as ProductoCategoria
        FROM sales_ms.OrdenDetalle od
        JOIN sales_ms.Orden o ON od.OrdenId = o.OrdenId
        JOIN sales_ms.Cliente c ON o.ClienteId = c.ClienteId
        JOIN sales_ms.Producto p ON od.ProductoId = p.ProductoId
        """

        cur.execute(query)
        rows = [dict(zip([d[0] for d in cur.description], row)) for row in cur.fetchall()]

        cur.close()
        conn.close()
        return rows

    except Exception as e:
        print(f"[MS SQL] Error extrayendo datos: {e}")
        return []

def transform_mssql_rows(rows):
    if not rows:
        return []

    final = []

    for r in rows:
        try:
            fecha = r["Fecha"]
            if isinstance(fecha, str):
                fecha = datetime.fromisoformat(fecha)

            genero = unify_gender(r["ClienteGenero"])

            precio = Decimal(str(r["PrecioUnit"]))
            cantidad = r["Cantidad"]
            descuento = Decimal(str(r["DescuentoPct"] or 0))

            monto = (precio * cantidad) * (1 - descuento / 100)

            final.append((
                "MS_SQL",
                r["OrdenId"],
                r["ProductoId"],
                r["ClienteId"],
                r["SKU"],
                r["ClienteNombre"],
                genero,
                r["ClientePais"],
                r["ProductoNombre"],
                r["ProductoCategoria"],
                fecha,
                r["Canal"],
                monto,
                cantidad
            ))

        except Exception as e:
            print(f"[MS SQL] Error transformando fila: {e}")
            continue

    return final
def load_mssql_staging(rows):
    if not rows:
        print("[MS SQL] No hay datos para cargar")
        return

    conn = get_sqlsrv_dw_conn()
    cur = conn.cursor()
    cur.fast_executemany = True

    try:
        cur.executemany("""
            INSERT INTO stg.FactVentas_MSSQL (
                source_system, source_order_id, source_producto_id, source_cliente_id,
                sku_oficial, ClienteNombre, ClienteGenero, ClientePais,
                ProductoNombre, ProductoCategoria, FechaOrden, Canal,
                MontoUSD, Cantidad
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, rows)

        conn.commit()
        print(f"[MS SQL] Cargados {len(rows)} registros")
    except Exception as e:
        print(f"[MS SQL] Error cargando datos: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()
def run_mssql_etl():
    print("\nETL MS SQL a DW")
    raw = extract_mssql_data()
    transformed = transform_mssql_rows(raw)
    load_mssql_staging(transformed)
    print("ETL MS SQL completado\n")
