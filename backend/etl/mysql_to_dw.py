import mysql.connector
import pyodbc
from decimal import Decimal
from api.config import settings
from etl.transformations.unify_gender import unify_gender
from etl.transformations.format_dates import parse_mysql_date
from etl.transformations.normalize_currency import clean_amount_str


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
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=DataEnvironmentDW;"
        "UID=sa;"
        "PWD=TuPassword;"
    )


def get_tasa_crc_to_usd(fecha):
    conn = get_sqlsrv_conn()
    cur = conn.cursor()
    cur.execute("""
        SELECT TOP 1 tasa
        FROM stg.tipo_cambio
        WHERE de='CRC' AND a='USD'
        ORDER BY fecha DESC
    """)
    row = cur.fetchone()
    cur.close()
    conn.close()
    return Decimal(row[0]) if row else Decimal(1)


def extract_mysql_data():
    conn = get_mysql_conn()
    cur = conn.cursor(dictionary=True)

    cur.execute("""
        SELECT *
        FROM OrdenDetalle od
        JOIN Orden o ON o.id = od.orden_id
        JOIN Cliente c ON c.id = o.cliente_id
        JOIN Producto p ON p.id = od.producto_id
    """)

    rows = cur.fetchall()
    cur.close()
    conn.close()
    return rows


def transform_mysql_rows(rows):
    final = []
    for r in rows:
        fecha = parse_mysql_date(r["fecha"])
        genero = unify_gender(r["genero"])

        total = clean_amount_str(r["total"])
        if r["moneda"] == "CRC":
            tasa = get_tasa_crc_to_usd(fecha)
            usd = total / tasa
        else:
            usd = total

        final.append((
            "MySQL",
            r["orden_id"],
            r["id"],
            r["cliente_id"],
            r["producto_id"],
            r["nombre"],
            genero,
            r["pais"],
            r["nombre"],
            r["categoria"],
            fecha,
            r["canal"],
            usd,
            r["cantidad"]
        ))
    return final


def load_mysql_staging(rows):
    conn = get_sqlsrv_conn()
    cur = conn.cursor()
    cur.fast_executemany = True

    cur.executemany("""
        INSERT INTO stg.FactVentas_MySQL (
            source_system, source_order_id, source_order_detalle_id,
            source_cliente_id, source_producto_id,
            ClienteNombre, ClienteGenero, ClientePais,
            ProductoNombre, ProductoCategoria,
            FechaOrden, Canal, MontoUSD, Cantidad
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)

    conn.commit()
    cur.close()
    conn.close()


def run_mysql_etl():
    raw = extract_mysql_data()
    transformed = transform_mysql_rows(raw)
    load_mysql_staging(transformed)
    print("ETL MySQL → DW completado")
