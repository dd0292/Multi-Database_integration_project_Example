import psycopg2
import pyodbc
from decimal import Decimal
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

from etl.transformations.unify_gender import unify_gender
def get_supabase_conn():
    supabase_url = os.getenv("SUPABASE_URL")
    host = supabase_url.replace("https://", "").replace(".supabase.co", "")
    
    return psycopg2.connect(
        host=f"db.{host}.supabase.co",
        port=5432,
        database="postgres",
        user=os.getenv("SUPABASE_USER"),
        password=os.getenv("SUPABASE_PASSWORD")
    )

def get_sqlsrv_conn():
    return pyodbc.connect(
        f"DRIVER={os.getenv('SQLSERVER_DRIVER')};"
        f"SERVER={os.getenv('SQLSERVER_HOST')},{os.getenv('SQLSERVER_PORT')};"
        f"DATABASE={os.getenv('SQLSERVER_DB_DW')};"
        f"UID={os.getenv('SQLSERVER_USER')};"
        f"PWD={os.getenv('SQLSERVER_PASSWORD')};"
    )

def get_tasa_crc_to_usd(fecha):
    conn = get_sqlsrv_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT TOP 1 tasa
        FROM stg.tipo_cambio
        WHERE de = 'CRC' AND a = 'USD'
        ORDER BY fecha DESC
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return Decimal(row[0]) if row else Decimal(1)
def extract_supabase_data():
    try:
        conn = get_supabase_conn()
        cur = conn.cursor()

        query = """
        SELECT 
            od.orden_detalle_id,
            od.orden_id,
            od.producto_id,
            od.cantidad,
            od.precio_unit,
            o.cliente_id,
            o.fecha,
            o.canal,
            o.moneda,
            o.total,
            c.nombre as cliente_nombre,
            c.genero as cliente_genero,
            c.pais as cliente_pais,
            p.nombre as producto_nombre,
            p.sku,
            p.categoria as producto_categoria
        FROM orden_detalle od
        JOIN orden o ON od.orden_id = o.orden_id
        JOIN cliente c ON o.cliente_id = c.cliente_id
        JOIN producto p ON od.producto_id = p.producto_id
        """

        cur.execute(query)
        rows = [dict(zip([d[0] for d in cur.description], row)) for row in cur.fetchall()]

        cur.close()
        conn.close()
        return rows

    except Exception as e:
        print(f"[Supabase] Error extrayendo datos: {e}")
        return []
def transform_supabase_rows(rows):
    if not rows:
        return []

    final = []

    for r in rows:
        try:
            fecha = r["fecha"]
            if isinstance(fecha, str):
                fecha = datetime.fromisoformat(fecha.replace("Z", "+00:00"))

            genero = unify_gender(r["cliente_genero"])

            total = Decimal(str(r["total"]))
            if r["moneda"] == "CRC":
                tasa = get_tasa_crc_to_usd(fecha)
                usd = total / tasa
            else:
                usd = total

            sku_oficial = r["sku"] or f"SERV_{r['producto_nombre'][:30].replace(' ', '_')}"

            final.append((
                "Supabase",
                str(r["orden_id"]),
                str(r["producto_id"]),
                str(r["cliente_id"]),
                sku_oficial,
                r["cliente_nombre"],
                genero,
                r["cliente_pais"],
                r["producto_nombre"],
                r["producto_categoria"],
                fecha,
                r["canal"],
                usd,
                r["cantidad"]
            ))

        except Exception as e:
            print(f"[Supabase] Error transformando fila: {e}")
            continue

    return final
def load_supabase_staging(rows):
    if not rows:
        print("[Supabase] No hay datos para cargar")
        return

    conn = get_sqlsrv_conn()
    cur = conn.cursor()
    cur.fast_executemany = True

    try:
        cur.executemany("""
            INSERT INTO stg.FactVentas_Supabase (
                source_system, source_order_id, source_producto_id, source_cliente_id,
                sku_oficial, ClienteNombre, ClienteGenero, ClientePais,
                ProductoNombre, ProductoCategoria, FechaOrden, Canal,
                MontoUSD, Cantidad
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, rows)

        conn.commit()
        print(f"[Supabase] Cargados {len(rows)} registros")
    except Exception as e:
        print(f"[Supabase] Error cargando datos: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def run_supabase_etl():
    print("\nETL Supabase a DW ")
    raw = extract_supabase_data()
    transformed = transform_supabase_rows(raw)
    load_supabase_staging(transformed)
    print("ETL Supabase completado\n")
