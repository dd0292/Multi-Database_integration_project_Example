import mysql.connector
import pyodbc
from decimal import Decimal
from api.config import settings
from etl.transformations.unify_gender import unify_gender
from etl.transformations.format_dates import parse_mysql_date
from etl.transformations.normalize_currency import clean_amount_str


# ------------------------------------------------------
#  CONEXIONES
# ------------------------------------------------------

def get_mysql_conn():
    return mysql.connector.connect(
        host=settings.MYSQL_HOST,
        port=settings.MYSQL_PORT,
        user=settings.MYSQL_USER,
        password=settings.MYSQL_PASSWORD,
        database=settings.MYSQL_DB,
    )


def get_sqlsrv_conn():
    return pyodbc.connect(
        f"DRIVER={settings.SQLSERVER_DRIVER};"
        f"SERVER={settings.SQLSERVER_HOST},{settings.SQLSERVER_PORT};"
        f"DATABASE={settings.SQLSERVER_DB_DW};"
        f"UID={settings.SQLSERVER_USER};"
        f"PWD={settings.SQLSERVER_PASSWORD};"
        "Encrypt=yes;TrustServerCertificate=yes;"
    )


# ------------------------------------------------------
#  TIPO DE CAMBIO (CRC -> USD)
# ------------------------------------------------------

def get_tasa_crc_to_usd(fecha):
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
    return Decimal(row[0]) if row else Decimal("1")


# ------------------------------------------------------
#  LOAD A STAGING
# ------------------------------------------------------

def load_mysql_staging(rows_cliente, rows_producto, rows_tiempo, rows_canal, rows_fact):
    conn = get_sqlsrv_conn()
    cur = conn.cursor()
    cur.fast_executemany = True

    # --------------------------
    # STAGING CLIENTE
    # --------------------------
    if rows_cliente:
        cur.executemany("""
            INSERT INTO stg.Cliente
            (SourceSystem, SourceClienteID, Nombre, Email, Genero, Pais, FechaRegistro)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, rows_cliente)

    # --------------------------
    # STAGING PRODUCTO
    # --------------------------
    if rows_producto:
        cur.executemany("""
            INSERT INTO stg.Producto
            (SourceSystem, SourceProductoID, SKU, CodigoAlterno, Nombre, Categoria)
            VALUES (?, ?, ?, ?, ?, ?)
        """, rows_producto)

    # --------------------------
    # STAGING TIEMPO
    # --------------------------
    if rows_tiempo:
        cur.executemany("""
            INSERT INTO stg.Tiempo (Fecha)
            VALUES (?)
        """, rows_tiempo)

    # --------------------------
    # STAGING CANAL
    # --------------------------
    if rows_canal:
        cur.executemany("""
            INSERT INTO stg.Canal (SourceSystem, Canal)
            VALUES (?, ?)
        """, rows_canal)

    # --------------------------
    # STAGING FACTVENTAS (MYSQL)
    # --------------------------
    if rows_fact:
        cur.executemany("""
            INSERT INTO stg.FactVentas_MySQL (
                SourceSystem, Source_Order_Id, Source_Order_Detalle_Id,
                Source_Cliente_Id, Source_Producto_Id,
                ClienteNombre, ClienteGenero, ClientePais,
                ProductoNombre, ProductoCategoria,
                FechaOrden, Canal, MontoUSD, Cantidad
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, rows_fact)

    conn.commit()
    cur.close()
    conn.close()


# ------------------------------------------------------
#  MAIN ETL
# ------------------------------------------------------

def run_mysql_etl():

    conn = get_mysql_conn()
    cur = conn.cursor(dictionary=True)

    # --------------------------
    # SELECT BASE (PDF ALIGNED)
    # --------------------------
    cur.execute("""
        SELECT
            od.id AS detalle_id,
            od.cantidad,
            od.precio_unit,

            o.id AS orden_id,
            o.fecha,
            o.canal,
            o.moneda,
            o.total,

            c.id AS cliente_id,
            c.nombre AS cliente_nombre,
            c.correo AS cliente_correo,
            c.genero AS cliente_genero,
            c.pais AS cliente_pais,
            c.created_at AS cliente_fecha_registro,

            p.id AS producto_id,
            p.nombre AS producto_nombre,
            p.categoria AS producto_categoria,
            p.codigo_alt AS producto_codigo_alt
        FROM OrdenDetalle od
        JOIN Orden o   ON o.id = od.orden_id
        JOIN Cliente c ON c.id = o.cliente_id
        JOIN Producto p ON p.id = od.producto_id
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()

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

        # --------------------------
        # FECHA (string -> datetime)
        # --------------------------
        fecha = parse_mysql_date(r["fecha"])

        # --------------------------
        # GÉNERO (M/F/X -> normalizado)
        # --------------------------
        genero = unify_gender(r["cliente_genero"])

        # --------------------------
        # MONEDA (string -> Decimal USD)
        # --------------------------
        total = clean_amount_str(r["total"])
        if r["moneda"] == "CRC":
            tasa = get_tasa_crc_to_usd(fecha)
            usd = total / tasa
        else:
            usd = total

        # --------------------------
        # CLIENTE
        # --------------------------
        if r["cliente_id"] not in seen_clients:
            seen_clients.add(r["cliente_id"])
            staging_cliente.append((
                "MySQL",
                str(r["cliente_id"]),
                r["cliente_nombre"],
                r["cliente_correo"],
                genero,
                r["cliente_pais"],
                fecha.date()
            ))

        # --------------------------
        # PRODUCTO
        # --------------------------
        if r["producto_id"] not in seen_products:
            seen_products.add(r["producto_id"])
            staging_producto.append((
                "MySQL",
                str(r["producto_id"]),   # interno
                None,                    # no hay SKU oficial
                r["producto_codigo_alt"],# ✅ CÓDIGO FUNCIONAL (PDF)
                r["producto_nombre"],
                r["producto_categoria"]
            ))

        # --------------------------
        # TIEMPO
        # --------------------------
        if fecha.date() not in seen_dates:
            seen_dates.add(fecha.date())
            staging_tiempo.append((fecha.date(),))

        # --------------------------
        # CANAL
        # --------------------------
        canal = r["canal"] or "WEB"
        if canal not in seen_channels:
            seen_channels.add(canal)
            staging_canal.append(("MySQL", canal))

        # --------------------------
        # FACTVENTAS
        # ⚠️ USAR CODIGO_ALT (NO PRODUCTO_ID)
        # --------------------------
        staging_fact.append((
            "MySQL",
            str(r["orden_id"]),
            str(r["detalle_id"]),
            str(r["cliente_id"]),
            r["producto_codigo_alt"],   # ✅ PDF-COMPLIANT
            r["cliente_nombre"],
            genero,
            r["cliente_pais"],
            r["producto_nombre"],
            r["producto_categoria"],
            fecha,
            canal,
            usd,
            r["cantidad"],
        ))

    load_mysql_staging(
        staging_cliente,
        staging_producto,
        staging_tiempo,
        staging_canal,
        staging_fact
    )

    print(f"[MySQL] ETL → STAGING completado. "
          f"Clientes={len(staging_cliente)}, Productos={len(staging_producto)}, Ventas={len(staging_fact)}")
