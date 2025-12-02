import os
from decimal import Decimal
from datetime import datetime
import pyodbc
from dotenv import load_dotenv
from decimal import Decimal, ROUND_HALF_UP

from etl.transformations.unify_gender import unify_gender

load_dotenv()


def get_mssql_source_conn():
    """Conexión al SQL Server transaccional (Ventas_Transactional)."""
    return pyodbc.connect(
        f"DRIVER={os.getenv('SQLSERVER_DRIVER')};"
        f"SERVER={os.getenv('SQLSERVER_HOST')},{os.getenv('SQLSERVER_PORT')};"
        f"DATABASE={os.getenv('SQLSERVER_DB_TRANSAC')};"
        f"UID={os.getenv('SQLSERVER_USER')};"
        f"PWD={os.getenv('SQLSERVER_PASSWORD')};"
        "Encrypt=no;TrustServerCertificate=yes;"
    )


def get_sqlsrv_dw_conn():
    """Conexión al DW (Ventas_DW)."""
    return pyodbc.connect(
        f"DRIVER={os.getenv('SQLSERVER_DRIVER')};"
        f"SERVER={os.getenv('SQLSERVER_HOST')},{os.getenv('SQLSERVER_PORT')};"
        f"DATABASE={os.getenv('SQLSERVER_DB_DW')};"
        f"UID={os.getenv('SQLSERVER_USER')};"
        f"PWD={os.getenv('SQLSERVER_PASSWORD')};"
        "Encrypt=no;TrustServerCertificate=yes;"
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
            c.Nombre  AS ClienteNombre,
            c.Email   AS ClienteEmail,
            c.Genero  AS ClienteGenero,
            c.Pais    AS ClientePais,
            p.Nombre  AS ProductoNombre,
            p.SKU,
            p.Categoria AS ProductoCategoria
        FROM dbo.OrdenDetalle od
        JOIN dbo.Orden o   ON od.OrdenId = o.OrdenId
        JOIN dbo.Cliente c ON o.ClienteId = c.ClienteId
        JOIN dbo.Producto p ON od.ProductoId = p.ProductoId
        """
        cur.execute(query)
        cols = [d[0] for d in cur.description]
        rows = [dict(zip(cols, row)) for row in cur.fetchall()]

        cur.close()
        conn.close()
        return rows

    except Exception as e:
        print(f"[MS SQL] Error extrayendo datos: {e}")
        return []


def load_mssql_staging(rows_cliente, rows_producto, rows_tiempo, rows_canal, rows_fact):
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
            INSERT INTO stg.FactVentas_MSSQL (
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


def _clear_staging_for_source(cur, source_system: str, fact_table_name: str):
    # Remove previous staging rows for this source so ETL is idempotent for re-runs.
    cur.execute("DELETE FROM stg.Cliente WHERE SourceSystem = ?", (source_system,))
    cur.execute("DELETE FROM stg.Producto WHERE SourceSystem = ?", (source_system,))
    cur.execute("DELETE FROM stg.Canal WHERE SourceSystem = ?", (source_system,))
    # Delete source-specific fact staging (stg.FactVentas_MSSQL)
    cur.execute(f"DELETE FROM {fact_table_name}")


def run_mssql_etl():
    print("\n[MS SQL] Iniciando ETL → STAGING")
    # Clear previous staging rows that belong to MSSQL
    conn_dw = get_sqlsrv_dw_conn()
    cur_dw = conn_dw.cursor()
    _clear_staging_for_source(cur_dw, "MSSQL", "stg.FactVentas_MSSQL")
    conn_dw.commit()
    cur_dw.close()
    conn_dw.close()

    rows = extract_mssql_data()
    if not rows:
        print("[MS SQL] No hay datos")
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
        # Fecha
        fecha = r["Fecha"]
        if isinstance(fecha, str):
            fecha = datetime.fromisoformat(fecha)

        # Género
        genero = unify_gender(r["ClienteGenero"])

        # Monto en USD (esta fuente siempre USD)
        precio = Decimal(str(r["PrecioUnit"]))
        cantidad = int(r["Cantidad"])
        descuento = Decimal(str(r["DescuentoPct"] or 0))
        monto = (precio * cantidad) * (1 - descuento / Decimal("100"))
        monto = monto.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)

        # ----- Cliente -----
        cliente_key = f"MSSQL|{r['ClienteId']}"
        if cliente_key not in seen_clients:
            seen_clients.add(cliente_key)
            staging_cliente.append((
                "MSSQL",
                str(r["ClienteId"]),
                r["ClienteNombre"],
                r["ClienteEmail"],
                genero,
                r["ClientePais"],
                fecha.date()
            ))

        # ----- Producto -----
        prod_key = f"MSSQL|{r['ProductoId']}"
        if prod_key not in seen_products:
            seen_products.add(prod_key)
            staging_producto.append((
                "MSSQL",
                str(r["ProductoId"]),
                r["SKU"],          # SKU oficial
                r["ProductoNombre"],
                r["ProductoCategoria"],
            ))

        # ----- Tiempo -----
        if fecha.date() not in seen_dates:
            seen_dates.add(fecha.date())
            staging_tiempo.append((fecha.date(),))

        # ----- Canal -----
        canal = r["Canal"] or "WEB"
        if canal not in seen_channels:
            seen_channels.add(canal)
            staging_canal.append(("MSSQL", canal))

        # ----- Fact -----
        staging_fact.append((
            "MSSQL",
            str(r["OrdenId"]),
            str(r["ProductoId"]),
            str(r["ClienteId"]),
            r["SKU"],                 # SKU_Oficial
            r["ClienteNombre"],
            genero,
            r["ClientePais"],
            r["ProductoNombre"],
            r["ProductoCategoria"],
            fecha,
            canal,
            monto,
            cantidad,
        ))

    load_mssql_staging(staging_cliente, staging_producto, staging_tiempo, staging_canal, staging_fact)
    print(f"[MS SQL] ETL → STAGING completado. "
          f"Clientes={len(staging_cliente)}, Productos={len(staging_producto)}, Ventas={len(staging_fact)}\n")
