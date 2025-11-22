import os
from decimal import Decimal
from datetime import datetime
import pyodbc
from neo4j import GraphDatabase
from dotenv import load_dotenv

from etl.transformations.unify_gender import unify_gender

load_dotenv()


def get_neo4j_conn():
    return GraphDatabase.driver(
        os.getenv("NEO4J_URI"),
        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
    )


def get_sqlsrv_dw_conn():
    return pyodbc.connect(
        f"DRIVER={os.getenv('SQLSERVER_DRIVER')};"
        f"SERVER={os.getenv('SQLSERVER_HOST')},{os.getenv('SQLSERVER_PORT')};"
        f"DATABASE={os.getenv('SQLSERVER_DB_DW')};"
        f"UID={os.getenv('SQLSERVER_USER')};"
        f"PWD={os.getenv('SQLSERVER_PASSWORD')};"
        "Encrypt=no;TrustServerCertificate=yes;"
    )


def get_tasa_crc_to_usd(fecha):
    conn = get_sqlsrv_dw_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT TOP 1 Tasa
        FROM stg.Tipo_Cambio
        WHERE De = 'CRC' AND A = 'USD'
        ORDER BY Fecha DESC
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


def load_neo4j_staging(rows_cliente, rows_producto, rows_tiempo, rows_canal, rows_fact):
    conn = get_sqlsrv_dw_conn()
    cur = conn.cursor()
    cur.fast_executemany = True

    if rows_cliente:
        cur.executemany("""
            INSERT INTO stg.Cliente
            (SourceSystem, SourceClienteID, Nombre, Email, Genero, Pais, FechaRegistro)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, rows_cliente)

    if rows_producto:
        cur.executemany("""
            INSERT INTO stg.Producto
            (SourceSystem, SourceProductoID, SKU, CodigoAlterno, CodigoMongo, CodigoNeo4j, Nombre, Categoria)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, rows_producto)

    if rows_tiempo:
        cur.executemany("""
            INSERT INTO stg.Tiempo (Fecha)
            VALUES (?)
        """, rows_tiempo)

    if rows_canal:
        cur.executemany("""
            INSERT INTO stg.Canal (SourceSystem, Canal)
            VALUES (?, ?)
        """, rows_canal)

    if rows_fact:
        cur.executemany("""
            INSERT INTO stg.FactVentas_Neo4j (
                SourceSystem, Source_Order_Id, Source_Producto_Id, Source_Cliente_Id,
                SKU_Oficial, ClienteNombre, ClienteGenero, ClientePais,
                ProductoNombre, ProductoCategoria, FechaOrden, Canal,
                MontoUSD, Cantidad
            )
            VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        """, rows_fact)

    conn.commit()
    cur.close()
    conn.close()


def run_neo4j_etl():
    print("\n[Neo4j] Iniciando ETL → STAGING")
    rows = extract_neo4j_data()
    if not rows:
        print("[Neo4j] No hay datos")
        return

    staging_cliente = []
    staging_producto = []
    staging_tiempo = []
    staging_canal = []
    staging_fact = []

    seen_clients = set()
    seen_products = set()
    seen_dates = set()
    seen_channels = set()

    for r in rows:
        fecha_raw = r.get("orden_fecha")

        fecha = None
        if fecha_raw:
            try:
                # Maneja 2024-01-15T10:20:00.000000Z
                fecha = datetime.fromisoformat(
                    fecha_raw.replace("Z", "+00:00")
                )
            except:
                try:
                    fecha = datetime.strptime(fecha_raw, "%Y-%m-%d")
                except:
                    print("[Neo4j]  Fecha inválida detectada:", fecha_raw)
                    continue
        else:
            fecha = datetime.now()

        # Género
        genero = unify_gender(r.get("cliente_genero"))

        # Total + moneda
        total = Decimal(str(r.get("total") or 0))
        moneda = r.get("moneda") or "USD"
        if moneda == "CRC":
            tasa = get_tasa_crc_to_usd(fecha)
            usd = total / tasa if tasa != 0 else total
        else:
            usd = total

        # ----- Cliente -----
        cliente_id = str(r.get("cliente_id"))
        cliente_key = f"Neo4j|{cliente_id}"
        if cliente_key not in seen_clients:
            seen_clients.add(cliente_key)
            staging_cliente.append((
                "Neo4j",
                cliente_id,
                r.get("cliente_nombre"),
                None,
                genero,
                r.get("cliente_pais"),
                fecha.date()
            ))

        # ----- Producto -----
        prod_id = str(r.get("producto_id"))
        prod_key = f"Neo4j|{prod_id}"
        if prod_key not in seen_products:
            seen_products.add(prod_key)
            staging_producto.append((
                "Neo4j",
                prod_id,
                r.get("sku"),
                r.get("codigo_alt"),
                r.get("codigo_mongo"),
                prod_id,  # CodigoNeo4j
                r.get("producto_nombre"),
                r.get("categoria") or "Sin Categoría",
            ))

        # ----- Tiempo -----
        if fecha.date() not in seen_dates:
            seen_dates.add(fecha.date())
            staging_tiempo.append((fecha.date(),))

        # ----- Canal -----
        canal = r.get("canal") or "WEB"
        if canal not in seen_channels:
            seen_channels.add(canal)
            staging_canal.append(("Neo4j", canal))

        # ----- SKU oficial estimado -----
        sku_oficial = (
            r.get("sku")
            or r.get("codigo_alt")
            or r.get("codigo_mongo")
            or f"NEO_{prod_id}"
        )

        # ----- Fact -----
        staging_fact.append((
            "Neo4j",
            str(r.get("orden_id")),
            prod_id,
            cliente_id,
            sku_oficial,
            r.get("cliente_nombre"),
            genero,
            r.get("cliente_pais"),
            r.get("producto_nombre"),
            r.get("categoria") or "Sin Categoría",
            fecha,
            canal,
            usd,
            r.get("cantidad") or 1,
        ))

    load_neo4j_staging(staging_cliente, staging_producto, staging_tiempo, staging_canal, staging_fact)
    print(f"[Neo4j] ETL → STAGING completado. "
          f"Clientes={len(staging_cliente)}, Productos={len(staging_producto)}, Ventas={len(staging_fact)}\n")
