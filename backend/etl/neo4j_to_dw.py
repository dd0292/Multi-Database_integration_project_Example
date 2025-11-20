from neo4j import GraphDatabase
import pyodbc
from decimal import Decimal
from datetime import datetime
import os
from dotenv import load_dotenv

load_dotenv()

from etl.transformations.unify_gender import unify_gender

def get_neo4j_conn():
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
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
def extract_neo4j_data():
    driver = get_neo4j_conn()

    query = """
    MATCH (cliente:Cliente)-[:REALIZO]->(orden:Orden)
    MATCH (orden)-[contiene:CONTIENE]->(producto:Producto)
    OPTIONAL MATCH (producto)-[:PERTENECE_A]->(categoria:Categoria)
    RETURN 
        cliente.id as cliente_id,
        cliente.nombre as cliente_nombre,
        cliente.genero as cliente_genero,
        cliente.pais as cliente_pais,
        orden.id as orden_id,
        orden.fecha as orden_fecha,
        orden.canal as canal,
        orden.moneda as moneda,
        orden.total as total,
        producto.id as producto_id,
        producto.nombre as producto_nombre,
        producto.sku as sku,
        producto.codigo_alt as codigo_alt,
        producto.codigo_mongo as codigo_mongo,
        categoria.nombre as categoria,
        contiene.cantidad as cantidad,
        contiene.precio_unit as precio_unit
    """

    try:
        with driver.session() as session:
            data = [dict(record) for record in session.run(query)]
        return data
    except Exception as e:
        print(f"[Neo4j] Error extrayendo datos: {e}")
        return []
    finally:
        driver.close()


def transform_neo4j_rows(rows):
    if not rows:
        return []

    final = []

    for r in rows:
        try:
            # Fecha
            fecha_raw = r.get("orden_fecha")
            if fecha_raw:
                if "T" in fecha_raw:
                    fecha = datetime.fromisoformat(fecha_raw.replace("Z", "+00:00"))
                else:
                    fecha = datetime.strptime(fecha_raw, "%Y-%m-%d %H:%M:%S")
            else:
                fecha = datetime.now()
            genero = unify_gender(r.get("cliente_genero", "No especificado"))
            total = Decimal(str(r.get("total") or 0))
            moneda = r.get("moneda", "USD")

            if moneda == "CRC":
                tasa = get_tasa_crc_to_usd(fecha)
                usd = total / tasa
            else:
                usd = total
            sku_oficial = (
                r.get("sku")
                or r.get("codigo_alt")
                or r.get("codigo_mongo")
                or f"NEO_{r.get('producto_id', 'X')}"
            )

            final.append((
                "Neo4j",
                r.get("orden_id"),
                r.get("producto_id"),
                r.get("cliente_id"),
                sku_oficial,
                r.get("cliente_nombre"),
                genero,
                r.get("cliente_pais"),
                r.get("producto_nombre"),
                r.get("categoria") or "Sin Categoría",
                fecha,
                r.get("canal") or "WEB",
                usd,
                r.get("cantidad") or 1
            ))

        except Exception as e:
            print(f"[Neo4j] Error transformando fila: {e}")
            continue

    return final


# Carga
def load_neo4j_staging(rows):
    if not rows:
        print("[Neo4j] No hay datos para cargar")
        return

    conn = get_sqlsrv_conn()
    cur = conn.cursor()
    cur.fast_executemany = True

    try:
        cur.executemany("""
            INSERT INTO stg.FactVentas_Neo4j (
                source_system, source_order_id, source_producto_id, source_cliente_id,
                sku_oficial, ClienteNombre, ClienteGenero, ClientePais,
                ProductoNombre, ProductoCategoria, FechaOrden, Canal,
                MontoUSD, Cantidad
            ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, rows)

        conn.commit()
        print(f"[Neo4j] Cargados {len(rows)} registros")
    except Exception as e:
        print(f"[Neo4j] Error cargando datos: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

def run_neo4j_etl():
    print("\nETL Neo4j a DW")
    raw = extract_neo4j_data()
    transformed = transform_neo4j_rows(raw)
    load_neo4j_staging(transformed)
    print("ETL Neo4j completado\n")
