import pyodbc
from datetime import datetime
from decimal import Decimal
import os
from dotenv import load_dotenv

load_dotenv()

# -------------------------
# CONEXIÓN A DW
# -------------------------
def get_sqlsrv_dw_conn():
    return pyodbc.connect(
        f"DRIVER={os.getenv('SQLSERVER_DRIVER')};"
        f"SERVER={os.getenv('SQLSERVER_HOST')},{os.getenv('SQLSERVER_PORT')};"
        f"DATABASE={os.getenv('SQLSERVER_DB_DW')};"
        f"UID={os.getenv('SQLSERVER_USER')};"
        f"PWD={os.getenv('SQLSERVER_PASSWORD')};"
        "Encrypt=no;TrustServerCertificate=yes;"
    )

# ------------------------------------------------------------
# PASO 1: CARGAR DimCliente DESDE stg.Cliente
# ------------------------------------------------------------
def load_dim_cliente(cur):
    cur.execute("""
        INSERT INTO DimCliente
        (ClienteKeyNatural, Nombre, Email, Genero, Pais, FechaRegistro, 
         SourceSystem, FechaInicioValidez, EsRegistroActual, Activo)
        SELECT 
            s.SourceClienteID,
            s.Nombre,
            s.Email,
            s.Genero,
            s.Pais,
            s.FechaRegistro,
            s.SourceSystem,
            GETDATE(),
            1,
            1
        FROM stg.Cliente s
        WHERE NOT EXISTS (
            SELECT 1
            FROM DimCliente d
            WHERE d.ClienteKeyNatural = s.SourceClienteID
              AND d.SourceSystem = s.SourceSystem
              AND d.EsRegistroActual = 1
        );
    """)
    return cur.rowcount


# ------------------------------------------------------------
# PASO 2: CARGAR DimProducto DESDE stg.Producto  (VERSIÓN FINAL)
# ------------------------------------------------------------
def load_dim_producto(cur):

    # ======================================================================
    # 0) NORMALIZAR CAMPOS (UPPER + TRIM)
    # ======================================================================
    cur.execute("""
        UPDATE stg.Producto
        SET
            SKU           = UPPER(LTRIM(RTRIM(SKU))),
            SKU_Oficial   = UPPER(LTRIM(RTRIM(SKU_Oficial))),
            CodigoAlterno = UPPER(LTRIM(RTRIM(CodigoAlterno))),
            CodigoMongo   = UPPER(LTRIM(RTRIM(CodigoMongo))),
            CodigoNeo4j   = UPPER(LTRIM(RTRIM(CodigoNeo4j))),
            SourceSystem  = UPPER(LTRIM(RTRIM(SourceSystem)));
    """)

    # ======================================================================
    # 0.5) ELIMINAR EQUIVALENCIAS INVÁLIDAS (CodigoOrigen = SKU_Oficial)
    # ======================================================================
    cur.execute("""
        DELETE FROM MapProductoEquivalencia
        WHERE UPPER(LTRIM(RTRIM(CodigoOrigen))) =
              UPPER(LTRIM(RTRIM(SKU_Oficial)));
    """)

    # ======================================================================
    # 0.6) FILTRO FINAL EN STAGING:
    #     SI CodigoOrigen coincide con SKU o SKU_Oficial → eliminar
    #     (Esto evita duplicados en el MERGE)
    # ======================================================================

    # Neo4j
    cur.execute("""
        UPDATE stg.Producto
        SET CodigoNeo4j = NULL
        WHERE CodigoNeo4j IS NOT NULL
          AND (
                UPPER(CodigoNeo4j) = UPPER(SKU)
             OR UPPER(CodigoNeo4j) = UPPER(SKU_Oficial)
          );
    """)

    # Alterno
    cur.execute("""
        UPDATE stg.Producto
        SET CodigoAlterno = NULL
        WHERE CodigoAlterno IS NOT NULL
          AND (
                UPPER(CodigoAlterno) = UPPER(SKU)
             OR UPPER(CodigoAlterno) = UPPER(SKU_Oficial)
          );
    """)

    # Mongo
    cur.execute("""
        UPDATE stg.Producto
        SET CodigoMongo = NULL
        WHERE CodigoMongo IS NOT NULL
          AND (
                UPPER(CodigoMongo) = UPPER(SKU)
             OR UPPER(CodigoMongo) = UPPER(SKU_Oficial)
          );
    """)

    # ======================================================================
    # 1) MSSQL DEFINE SKU OFICIAL
    # ======================================================================
    cur.execute("""
        UPDATE p
        SET SKU_Oficial = p.SKU
        FROM stg.Producto p
        WHERE p.SourceSystem = 'MSSQL'
          AND p.SKU IS NOT NULL;
    """)

    # ======================================================================
    # 2) HEREDAR SKU OFICIAL DESDE MSSQL
    # ======================================================================
    cur.execute("""
        UPDATE p
        SET SKU_Oficial = m.SKU
        FROM stg.Producto p
        JOIN stg.Producto m
             ON m.Nombre     = p.Nombre
            AND m.Categoria  = p.Categoria
            AND m.SourceSystem = 'MSSQL'
        WHERE p.SKU_Oficial IS NULL;
    """)

    # ======================================================================
    # 3) GENERAR SKU_AUTO PARA LOS QUE NO TIENEN
    # ======================================================================
    cur.execute("""
        UPDATE stg.Producto
        SET SKU_Oficial = 'SKU_AUTO_' +
            RIGHT(REPLACE(CONVERT(VARCHAR(36), NEWID()),'-',''), 8)
        WHERE SKU_Oficial IS NULL;
    """)

    # ======================================================================
    # 4) INSERTAR DimProducto SI NO EXISTE
    # ======================================================================
    cur.execute("""
        INSERT INTO DimProducto (SKU, Nombre, Categoria, SourceSystem)
        SELECT
            p.SKU_Oficial,
            p.Nombre,
            p.Categoria,
            MIN(p.SourceSystem)
        FROM stg.Producto p
        GROUP BY p.SKU_Oficial, p.Nombre, p.Categoria
        HAVING NOT EXISTS (
            SELECT 1 FROM DimProducto d
            WHERE d.SKU = p.SKU_Oficial
        );
    """)

    # ======================================================================
    # 5) MERGE FINAL (SIN DUPLICADOS)
    # ======================================================================

    # 5.1 – SKU
    cur.execute("""
        MERGE MapProductoEquivalencia AS target
        USING (
            SELECT DISTINCT
                SKU_Oficial,
                SourceSystem,
                SKU AS CodigoOrigen,
                'SKU' AS TipoCodigo
            FROM stg.Producto
            WHERE SKU IS NOT NULL
              AND LEN(SKU) > 0
              AND SKU <> SKU_Oficial
        ) AS source
        ON target.SKU_Oficial = source.SKU_Oficial
           AND target.SourceSystem = source.SourceSystem
           AND target.CodigoOrigen = source.CodigoOrigen
           AND target.TipoCodigo = source.TipoCodigo
        WHEN NOT MATCHED THEN
            INSERT (SKU_Oficial, SourceSystem, CodigoOrigen, TipoCodigo)
            VALUES (source.SKU_Oficial, source.SourceSystem, source.CodigoOrigen, source.TipoCodigo);
    """)

    # 5.2 – ALTERNO
    cur.execute("""
        MERGE MapProductoEquivalencia AS target
        USING (
            SELECT DISTINCT
                SKU_Oficial,
                SourceSystem,
                CodigoAlterno AS CodigoOrigen,
                'ALTERNO' AS TipoCodigo
            FROM stg.Producto
            WHERE CodigoAlterno IS NOT NULL
              AND LEN(CodigoAlterno) > 0
              AND CodigoAlterno <> SKU_Oficial
        ) AS source
        ON target.SKU_Oficial = source.SKU_Oficial
           AND target.SourceSystem = source.SourceSystem
           AND target.CodigoOrigen = source.CodigoOrigen
           AND target.TipoCodigo = source.TipoCodigo
        WHEN NOT MATCHED THEN
            INSERT (SKU_Oficial, SourceSystem, CodigoOrigen, TipoCodigo)
            VALUES (source.SKU_Oficial, source.SourceSystem, source.CodigoOrigen, source.TipoCodigo);
    """)

    # 5.3 – MONGO
    cur.execute("""
        MERGE MapProductoEquivalencia AS target
        USING (
            SELECT DISTINCT
                SKU_Oficial,
                SourceSystem,
                CodigoMongo AS CodigoOrigen,
                'MONGO' AS TipoCodigo
            FROM stg.Producto
            WHERE CodigoMongo IS NOT NULL
              AND LEN(CodigoMongo) > 0
              AND CodigoMongo <> SKU_Oficial
        ) AS source
        ON target.SKU_Oficial = source.SKU_Oficial
           AND target.SourceSystem = source.SourceSystem
           AND target.CodigoOrigen = source.CodigoOrigen
           AND target.TipoCodigo = source.TipoCodigo
        WHEN NOT MATCHED THEN
            INSERT (SKU_Oficial, SourceSystem, CodigoOrigen, TipoCodigo)
            VALUES (source.SKU_Oficial, source.SourceSystem, source.CodigoOrigen, source.TipoCodigo);
    """)

    # 5.4 – NEO4J
    cur.execute("""
        MERGE MapProductoEquivalencia AS target
        USING (
            SELECT DISTINCT
                SKU_Oficial,
                SourceSystem,
                CodigoNeo4j AS CodigoOrigen,
                'NEO4J' AS TipoCodigo
            FROM stg.Producto
            WHERE CodigoNeo4j IS NOT NULL
              AND LEN(CodigoNeo4j) > 0
              AND CodigoNeo4j <> SKU_Oficial
        ) AS source
        ON target.SKU_Oficial = source.SKU_Oficial
           AND target.SourceSystem = source.SourceSystem
           AND target.CodigoOrigen = source.CodigoOrigen
           AND target.TipoCodigo = source.TipoCodigo
        WHEN NOT MATCHED THEN
            INSERT (SKU_Oficial, SourceSystem, CodigoOrigen, TipoCodigo)
            VALUES (source.SKU_Oficial, source.SourceSystem, source.CodigoOrigen, source.TipoCodigo);
    """)

    # ======================================================================
    # RETORNAR TOTAL DimProducto
    # ======================================================================
    cur.execute("SELECT COUNT(*) FROM DimProducto;")
    return cur.fetchone()[0]


# ------------------------------------------------------------
# PASO 3: CARGAR DimTiempo DESDE stg.Tiempo
# ------------------------------------------------------------
def load_dim_tiempo(cur):
    cur.execute("""
        INSERT INTO DimTiempo (
            TiempoID, Fecha, Anio, Semestre, Trimestre,
            Mes, NombreMes, Dia, DiaSemana, NombreDiaSemana,
            EsFinDeSemana, MesAnio
        )
        SELECT DISTINCT
            CONVERT(INT, FORMAT(t.Fecha, 'yyyyMMdd')) AS TiempoID,
            t.Fecha,
            YEAR(t.Fecha),
            CASE WHEN MONTH(t.Fecha) <= 6 THEN 1 ELSE 2 END AS Semestre,
            DATEPART(QUARTER, t.Fecha) AS Trimestre,
            MONTH(t.Fecha),
            DATENAME(MONTH, t.Fecha),
            DAY(t.Fecha),
            DATEPART(WEEKDAY, t.Fecha),
            DATENAME(WEEKDAY, t.Fecha),
            CASE WHEN DATEPART(WEEKDAY, t.Fecha) IN (1,7) THEN 1 ELSE 0 END,
            FORMAT(t.Fecha, 'yyyy-MM')
        FROM stg.Tiempo t
        WHERE NOT EXISTS (
            SELECT 1 FROM DimTiempo d
            WHERE d.TiempoID = CONVERT(INT, FORMAT(t.Fecha, 'yyyyMMdd'))
        );
    """)

    return cur.rowcount



# ------------------------------------------------------------
# PASO 4: CARGAR DimCanal DESDE stg.Canal
# ------------------------------------------------------------
def load_dim_canal(cur):
    cur.execute("""
        INSERT INTO DimCanal (CodigoCanal, NombreCanal)
        SELECT DISTINCT
            Canal AS CodigoCanal,
            Canal AS NombreCanal
        FROM stg.Canal s
        WHERE NOT EXISTS (
            SELECT 1 FROM DimCanal d
            WHERE d.CodigoCanal = s.Canal
        );
    """)
    return cur.rowcount



# ------------------------------------------------------------
# PASO 5: CARGAR FactVentas
# (UNION TODOS LOS stg.FactVentas_*)
# ------------------------------------------------------------
def load_fact_ventas(cur):
    cur.execute("""
        INSERT INTO FactVentas (
            ClienteID, ProductoID, TiempoID, CanalID,
            OrdenKeyNatural, MonedaOrigen, TotalUSD, Cantidad,
            PrecioUnitUSD, DescuentoPct, TipoCambioAplicado, SourceSystem
        )
        SELECT
            dc.ClienteID,
            dp.ProductoID,
            CONVERT(VARCHAR(8), f.FechaOrden, 112) AS TiempoID,
            dcan.CanalID,
            f.Source_Order_Id,
            f.MonedaOrigen,
            f.MontoUSD,
            f.Cantidad,
            f.MontoUSD / NULLIF(f.Cantidad, 0),
            f.DescuentoPct,
            f.TipoCambioAplicado,
            f.SourceSystem
        FROM (

            SELECT 
                SourceSystem,
                Source_Order_Id,
                Source_Cliente_Id,
                Source_Producto_Id,
                FechaOrden,
                Canal,
                MontoUSD,
                Cantidad,
                'USD' AS MonedaOrigen,
                NULL AS DescuentoPct,
                NULL AS TipoCambioAplicado
            FROM stg.FactVentas_MySQL

            UNION ALL

            SELECT 
                SourceSystem,
                Source_Order_Id,
                Source_Cliente_Id,
                Source_Producto_Id,
                FechaOrden,
                Canal,
                MontoUSD,
                Cantidad,
                'USD',
                NULL,
                NULL
            FROM stg.FactVentas_MSSQL

            UNION ALL

            SELECT 
                SourceSystem,
                Source_Order_Id,
                Source_Cliente_Id,
                Source_Producto_Id,
                FechaOrden,
                Canal,
                MontoUSD,
                Cantidad,
                'USD',
                NULL,
                NULL
            FROM stg.FactVentas_Mongo

            UNION ALL

            SELECT 
                SourceSystem,
                Source_Order_Id,
                Source_Cliente_Id,
                Source_Producto_Id,
                FechaOrden,
                Canal,
                MontoUSD,
                Cantidad,
                'USD',
                NULL,
                NULL
            FROM stg.FactVentas_Neo4j

            UNION ALL

            SELECT 
                SourceSystem,
                Source_Order_Id,
                Source_Cliente_Id,
                Source_Producto_Id,
                FechaOrden,
                Canal,
                MontoUSD,
                Cantidad,
                'USD',
                NULL,
                NULL
            FROM stg.FactVentas_Supabase

        ) f

        INNER JOIN DimCliente dc
            ON dc.ClienteKeyNatural = f.Source_Cliente_Id
           AND dc.EsRegistroActual = 1

        INNER JOIN MapProductoEquivalencia mpe
            ON mpe.CodigoOrigen = f.Source_Producto_Id
           AND mpe.SourceSystem = f.SourceSystem

        INNER JOIN DimProducto dp
            ON dp.SKU = mpe.SKU_Oficial
           AND dp.EsRegistroActual = 1

        INNER JOIN DimCanal dcan
            ON dcan.CodigoCanal = f.Canal

        WHERE NOT EXISTS (
            SELECT 1 FROM FactVentas fv
            WHERE fv.OrdenKeyNatural = f.Source_Order_Id
              AND fv.SourceSystem = f.SourceSystem
        );
    """)

    return cur.rowcount



# ------------------------------------------------------------
# PROCESO PRINCIPAL
# ------------------------------------------------------------
def run_staging_to_dw():
    conn = get_sqlsrv_dw_conn()
    cur = conn.cursor()

    print("\n--- Cargando STAGING → DIMENSIONES ---")

    print("DimCliente:", load_dim_cliente(cur))
    print("DimProducto:", load_dim_producto(cur))
    print("DimTiempo:", load_dim_tiempo(cur))
    print("DimCanal:", load_dim_canal(cur))

    print("\n--- Cargando STAGING → FACTVENTAS ---")
    print("FactVentas:", load_fact_ventas(cur))

    conn.commit()
    cur.close()
    conn.close()

    print("\nETL COMPLETO: STAGING → DW")

