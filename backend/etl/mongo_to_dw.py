from decimal import Decimal
import pyodbc
from datetime import datetime
from api.database.mongo_connection import get_db
from etl.transformations.unify_gender import unify_gender


def get_sqlsrv_conn():
    return pyodbc.connect(
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost,1433;"
        "DATABASE=DataEnvironmentDW;"
        "UID=sa;"
        "PWD=TuPassword;"
    )


def get_tasa():
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


def extract_mongo():
    db = get_db()

    clientes = {str(c["_id"]): c for c in db.clientes.find()}
    productos = {str(p["_id"]): p for p in db.productos.find()}

    final = []

    for o in db.ordenes.find():
        cliente = clientes.get(str(o["cliente_id"]))
        fecha = datetime.fromisoformat(o["fecha"]["$date"].replace("Z", "+00:00"))

        for item in o["items"]:
            producto = productos[str(item["producto_id"])]

            final.append({
                "orden_id": str(o["_id"]),
                "cliente_id": str(o["cliente_id"]),
                "producto_id": str(item["producto_id"]),
                "cantidad": item["cantidad"],
                "total_crc": o["total"],
                "fecha": fecha,
                "canal": o["canal"],
                "producto_nombre": producto["nombre"],
                "producto_categoria": producto["categoria"],
                "cliente_nombre": cliente["nombre"],
                "cliente_genero": cliente["genero"],
                "cliente_pais": cliente["pais"]
            })
    return final


def transform_mongo(raw):
    tasa = get_tasa()
    final = []

    for r in raw:
        usd = Decimal(r["total_crc"]) / tasa
        genero = unify_gender(r["cliente_genero"])

        final.append((
            "MongoDB",
            r["orden_id"],
            r["producto_id"],
            r["cliente_id"],
            None,  # sku_oficial
            r["cliente_nombre"],
            genero,
            r["cliente_pais"],
            r["producto_nombre"],
            r["producto_categoria"],
            r["fecha"],
            r["canal"],
            usd,
            r["cantidad"],
        ))
    return final


def load_mongo_staging(rows):
    conn = get_sqlsrv_conn()
    cur = conn.cursor()
    cur.fast_executemany = True

    cur.executemany("""
        INSERT INTO stg.FactVentas_Mongo (
            source_system, source_order_id, source_producto_id, source_cliente_id,
            sku_oficial, ClienteNombre, ClienteGenero, ClientePais,
            ProductoNombre, ProductoCategoria, FechaOrden, Canal,
            MontoUSD, Cantidad
        ) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)
    """, rows)

    conn.commit()
    cur.close()
    conn.close()


def run_mongo_etl():
    raw = extract_mongo()
    transformed = transform_mongo(raw)
    load_mongo_staging(transformed)
    print("ETL MongoDB → DW completado")
