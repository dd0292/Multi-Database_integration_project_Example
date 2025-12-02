from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import os
import pyodbc
from dotenv import load_dotenv

from api.database.mongo_connection import MongoDBConnection
from etl.transformations.unify_gender import unify_gender

load_dotenv()


def get_sqlsrv_conn():
    """Conexión al DW (Ventas_DW)."""
    return pyodbc.connect(
        f"DRIVER={os.getenv('SQLSERVER_DRIVER')};"
        f"SERVER={os.getenv('SQLSERVER_HOST')},{os.getenv('SQLSERVER_PORT')};"
        f"DATABASE={os.getenv('SQLSERVER_DB_DW')};"
        f"UID={os.getenv('SQLSERVER_USER')};"
        f"PWD={os.getenv('SQLSERVER_PASSWORD')};"
        "Encrypt=no;TrustServerCertificate=yes;"
    )


def get_tasa_crc_to_usd():
    """Obtiene la última tasa CRC→USD desde stg.Tipo_Cambio."""
    conn = get_sqlsrv_conn()
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


def load_mongo_staging(rows_cliente, rows_producto, rows_tiempo, rows_canal, rows_fact):
    conn = get_sqlsrv_conn()
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
            (SourceSystem, SourceProductoID, SKU, CodigoAlterno, CodigoMongo, Nombre, Categoria)
            VALUES (?, ?, ?, ?, ?, ?, ?)
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
            INSERT INTO stg.FactVentas_Mongo (
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


def _clear_staging_for_source(conn, source_system: str, fact_table_name: str):
    """
    Remove previous staging rows for this source to make the ETL idempotent.
    conn is an open pyodbc connection to the DW.
    """
    cur = conn.cursor()
    try:
        cur.execute("DELETE FROM stg.Cliente WHERE SourceSystem = ?", (source_system,))
        cur.execute("DELETE FROM stg.Producto WHERE SourceSystem = ?", (source_system,))
        cur.execute("DELETE FROM stg.Canal WHERE SourceSystem = ?", (source_system,))
        cur.execute(f"DELETE FROM {fact_table_name}")
        conn.commit()
    finally:
        cur.close()


def run_mongo_etl():
    print("\n[MongoDB] Iniciando ETL → STAGING")

    # Clear previous staging rows that belong to MongoDB
    conn_dw = get_sqlsrv_conn()
    try:
        _clear_staging_for_source(conn_dw, "MongoDB", "stg.FactVentas_Mongo")
    finally:
        conn_dw.close()

    db = MongoDBConnection.get_db()

    clientes = {str(c["_id"]): c for c in db.clientes.find()}
    productos = {str(p["_id"]): p for p in db.productos.find()}

    tasa = get_tasa_crc_to_usd()

    staging_cliente = []
    staging_producto = []
    staging_tiempo = []
    staging_canal = []
    staging_fact = []

    seen_clients = set()
    seen_products = set()
    seen_dates = set()
    seen_channels = set()

    for o in db.ordenes.find():
        cliente_id = str(o["cliente_id"])
        cliente_doc = clientes.get(cliente_id)
        if not cliente_doc:
            continue

        # fecha puede venir como {"$date": "..."} o como string ISO
        fecha_raw = o.get("fecha")
        if isinstance(fecha_raw, dict) and "$date" in fecha_raw:
            fecha_str = fecha_raw["$date"]
        elif isinstance(fecha_raw, str):
            fecha_str = fecha_raw
        else:
            print(" Fecha inválida en documento Mongo:", fecha_raw)
            continue

        fecha = datetime.fromisoformat(fecha_str.replace("Z", "+00:00"))

        canal = o.get("canal", "WEB")
        total_crc = Decimal(str(o.get("total", 0)))

        # ---- Cliente staging ----
        if cliente_id not in seen_clients:
            seen_clients.add(cliente_id)
            staging_cliente.append((
                "MongoDB",
                cliente_id,
                cliente_doc.get("nombre"),
                cliente_doc.get("email"),
                unify_gender(cliente_doc.get("genero")),
                cliente_doc.get("pais"),
                fecha.date(),
            ))

        # ---- Tiempo staging ----
        if fecha.date() not in seen_dates:
            seen_dates.add(fecha.date())
            staging_tiempo.append((fecha.date(),))

        # ---- Canal staging ----
        if canal not in seen_channels:
            seen_channels.add(canal)
            staging_canal.append(("MongoDB", canal))

        # ---- Detalles / Producto + Fact ----
        for item in o["items"]:
            prod_id = str(item["producto_id"])
            prod_doc = productos.get(prod_id)
            if not prod_doc:
                continue

            # Producto staging
            if prod_id not in seen_products:
                seen_products.add(prod_id)
                staging_producto.append((
                    "MongoDB",                 # SourceSystem
                    prod_id,                   # SourceProductoID
                    prod_doc.get("equivalencias").get("sku"),         # SKU
                    prod_doc.get("equivalencias").get("codigo_alt"),                      # CodigoAlterno
                    prod_doc.get("codigo"),  # CodigoMongo
                    prod_doc.get("nombre"),
                    prod_doc.get("categoria"),
                ))

                cantidad = int(item.get("cantidad", 1))
                # Convert CRC -> USD: handle either CRC-per-USD or USD-per-CRC
                if tasa == 0:
                    usd = total_crc.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                elif tasa < Decimal("0.01"):
                    usd = (total_crc * tasa).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
                else:
                    usd = (total_crc / tasa).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

            staging_fact.append((
                "MongoDB",
                str(o["_id"]),                  # Source_Order_Id
                prod_id,                        # Source_Producto_Id
                cliente_id,                     # Source_Cliente_Id
                None,                           # SKU_Oficial (se resuelve luego)
                cliente_doc.get("nombre"),
                unify_gender(cliente_doc.get("genero")),
                cliente_doc.get("pais"),
                prod_doc.get("nombre"),
                prod_doc.get("categoria"),
                fecha,
                canal,
                usd,
                cantidad,
            ))

    load_mongo_staging(staging_cliente, staging_producto, staging_tiempo, staging_canal, staging_fact)
    print(f"[MongoDB] ETL → STAGING completado. "
          f"Clientes={len(staging_cliente)}, Productos={len(staging_producto)}, Ventas={len(staging_fact)}\n")
