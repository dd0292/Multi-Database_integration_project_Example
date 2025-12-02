import os
import mysql.connector
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime
import pyodbc
from dotenv import load_dotenv

from supabase import create_client
from etl.transformations.unify_gender import unify_gender

load_dotenv()

# ---------------------------
# Inicializar Supabase SDK
# ---------------------------
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


# ---------------------------
# Conexión DW SQL Server
# ---------------------------
def get_sqlsrv_dw_conn():
    return pyodbc.connect(
        f"DRIVER={os.getenv('SQLSERVER_DRIVER')};"
        f"SERVER={os.getenv('SQLSERVER_HOST')},{os.getenv('SQLSERVER_PORT')};"
        f"DATABASE={os.getenv('SQLSERVER_DB_DW')};"
        f"UID={os.getenv('SQLSERVER_USER')};"
        f"PWD={os.getenv('SQLSERVER_PASSWORD')};"
        "Encrypt=no;TrustServerCertificate=yes;"
    )




# ---------------------------
# Obtener tasa CRC → USD
# ---------------------------
def get_tasa_crc_to_usd():
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


# ---------------------------
# EXTRAER DATOS DESDE SUPABASE
# ---------------------------
def extract_supabase_data():

    detalles = supabase.table("orden_detalle").select("*").execute().data
    if not detalles:
        return []

    ordenes_dict = {
        o["orden_id"]: o
        for o in supabase.table("orden").select("*").execute().data
    }

    clientes_dict = {
        c["cliente_id"]: c
        for c in supabase.table("cliente").select("*").execute().data
    }

    productos_dict = {
        p["producto_id"]: p
        for p in supabase.table("producto").select("*").execute().data
    }

    rows = []
    for d in detalles:
        o = ordenes_dict.get(d["orden_id"])
        c = clientes_dict.get(o["cliente_id"]) if o else None
        p = productos_dict.get(d["producto_id"])

        if not o or not c or not p:
            continue

        rows.append({
            "orden_id": d["orden_id"],
            "orden_detalle_id": d["orden_detalle_id"],
            "cliente_id": o["cliente_id"],
            "producto_id": d["producto_id"],
            "cantidad": d["cantidad"],
            "precio_unit": Decimal(str(d["precio_unit"])),
            "total": Decimal(str(o["total"])),
            "moneda": o["moneda"],
            "fecha": o["fecha"],
            "canal": o["canal"],
            "cliente_nombre": c["nombre"],
            "cliente_genero": c["genero"],
            "cliente_pais": c["pais"],
            "cliente_email": c["email"],
            "sku": p["sku"],
            "producto_nombre": p["nombre"],
            "producto_categoria": p["categoria"]
        })

    return rows


# ---------------------------
# CARGAR A STAGING
# ---------------------------
def load_supabase_staging(rows_cliente, rows_producto, rows_tiempo, rows_canal, rows_fact):
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
            (SourceSystem, SourceProductoID, SKU, Nombre, Categoria)
            VALUES (?, ?, ?, ?, ?)
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
            INSERT INTO stg.FactVentas_Supabase (
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


# ---------------------------
# ETL PRINCIPAL
# ---------------------------
def run_supabase_etl():

    print("\n[Supabase] Iniciando ETL → STAGING")

    conn_dw = get_sqlsrv_dw_conn()
    try:
        _clear_staging_for_source(conn_dw, "Supabase", "stg.FactVentas_Supabase")
    finally:
        conn_dw.close()

    rows = extract_supabase_data()
    if not rows:
        print("[Supabase] No hay datos")
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

    tasa = get_tasa_crc_to_usd()

    for r in rows:

        # Fecha
        fecha = r["fecha"]
        if isinstance(fecha, str):
            fecha = datetime.fromisoformat(fecha.replace("Z", "+00:00"))

        # Conversión USD
        total_linea = r["precio_unit"] * r["cantidad"]
        if r["moneda"] == "CRC":
            # Convert CRC -> USD: handle either CRC-per-USD or USD-per-CRC
            if tasa == 0:
                usd = total_linea.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            elif tasa < Decimal("0.01"):
                usd = (total_linea * tasa).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
            else:
                usd = (total_linea / tasa).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)
        else:
            usd = total_linea.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        genero = unify_gender(r["cliente_genero"])

        # ----- Cliente
        if r["cliente_id"] not in seen_clients:
            seen_clients.add(r["cliente_id"])
            staging_cliente.append((
                "Supabase",
                str(r["cliente_id"]),
                r["cliente_nombre"],
                r["cliente_email"],
                genero,
                r["cliente_pais"],
                fecha.date()
            ))

        # ----- Producto
        if r["producto_id"] not in seen_products:
            seen_products.add(r["producto_id"])
            staging_producto.append((
                "Supabase",
                str(r["producto_id"]),
                r["sku"],     # puede ser NULL en algunos → se resolverá luego
                r["producto_nombre"],
                r["producto_categoria"],
            ))

        # ----- Tiempo
        if fecha.date() not in seen_dates:
            seen_dates.add(fecha.date())
            staging_tiempo.append((fecha.date(),))

        # ----- Canal
        canal = r["canal"] or "WEB"
        if canal not in seen_channels:
            seen_channels.add(canal)
            staging_canal.append(("Supabase", canal))

        # ----- Fact
        staging_fact.append((
            "Supabase",
            str(r["orden_id"]),
            str(r["producto_id"]),
            str(r["cliente_id"]),
            r["sku"],                # SKU_Oficial (si existe)
            r["cliente_nombre"],
            genero,
            r["cliente_pais"],
            r["producto_nombre"],
            r["producto_categoria"],
            fecha,
            canal,
            usd,
            r["cantidad"]
        ))

    load_supabase_staging(staging_cliente, staging_producto, staging_tiempo, staging_canal, staging_fact)

    print(f"[Supabase] ETL → STAGING completado. "
          f"Clientes={len(staging_cliente)}, Productos={len(staging_producto)}, Ventas={len(staging_fact)}\n")
