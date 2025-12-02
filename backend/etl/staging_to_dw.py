import pyodbc
from datetime import datetime
from decimal import Decimal
import os
try:
    import pycountry
except Exception:
    pycountry = None
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

    # ------------------------------------------------------------
    def _resolve_country_name(raw_val: str) -> str:
        if raw_val is None:
            return None
        v = raw_val.strip()
        if not v:
            return None

        key = v.upper()

        alias_map = {
            'CRC': 'Costa Rica', 'CR': 'Costa Rica', 'COSTARICA': 'Costa Rica', 'COSTA RICA': 'Costa Rica',
            'PA': 'Panama', 'PAN': 'Panama', 'PANAMA': 'Panama', 'PANAMÁ': 'Panama',
            'CHL': 'Chile', 'CL': 'Chile',
            'ESP': 'Spain', 'ES': 'Spain'
        }
        if key in alias_map:
            return alias_map[key]

        if pycountry:
            try:
                # alpha-2
                if len(key) == 2:
                    c = pycountry.countries.get(alpha_2=key)
                    if c:
                        return c.name
                # alpha-3
                if len(key) == 3:
                    c = pycountry.countries.get(alpha_3=key)
                    if c:
                        return c.name


                try:
                    c = pycountry.countries.lookup(v)
                    if c:
                        return c.name
                except LookupError:
                    pass


                for c in pycountry.countries:
                    if c.name.upper() == key:
                        return c.name
            except Exception:
                return v.title()

        return v.title()

    # 1) Normalizar valores distintos en stg.Cliente y actualizarlos
    cur.execute("SELECT DISTINCT Pais FROM stg.Cliente WHERE Pais IS NOT NULL AND LEN(LTRIM(RTRIM(Pais))) > 0;")
    rows = cur.fetchall()
    for (pais,) in rows:
        normalized = _resolve_country_name(pais)
        if normalized and normalized != pais:
            cur.execute(
                "UPDATE stg.Cliente SET Pais = ? WHERE UPPER(LTRIM(RTRIM(Pais))) = UPPER(LTRIM(RTRIM(?)));",
                normalized, pais
            )

    # 2) Normalizar filas activas existentes en DimCliente
    cur.execute("SELECT DISTINCT Pais FROM DimCliente WHERE EsRegistroActual = 1 AND Pais IS NOT NULL AND LEN(LTRIM(RTRIM(Pais))) > 0;")
    rows = cur.fetchall()
    for (pais,) in rows:
        normalized = _resolve_country_name(pais)
        if normalized and normalized != pais:
            cur.execute(
                "UPDATE DimCliente SET Pais = ? WHERE EsRegistroActual = 1 AND UPPER(LTRIM(RTRIM(Pais))) = UPPER(LTRIM(RTRIM(?)));",
                normalized, pais
            )

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

    # Ensure a sentinel 'unknown' product exists so Fact inserts can
    # reference a valid ProductoID when no SKU mapping is found.
    cur.execute("""
        IF NOT EXISTS (SELECT 1 FROM DimProducto WHERE SKU = '__UNKNOWN__')
        BEGIN
            INSERT INTO DimProducto (SKU, Nombre, Categoria, SourceSystem, FechaInicioValidez, EsRegistroActual, Activo)
            VALUES ('__UNKNOWN__', 'PRODUCTO_DESCONOCIDO', 'SIN CATEGORIA', 'SYSTEM', GETDATE(), 1, 1)
        END
    """)
    return cur.rowcount


# ------------------------------------------------------------
# PASO 2: CARGAR DimProducto DESDE stg.Producto  (VERSIÓN FINAL)
# ------------------------------------------------------------
def load_dim_producto(cur):

    # ======================================================
    # 1) NORMALIZAR CAMPOS
    # ======================================================
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

    # ======================================================
    # 2) ELIMINAR EQUIVALENCIAS INVÁLIDAS
    # ======================================================
    cur.execute("""
        DELETE FROM MapProductoEquivalencia
        WHERE UPPER(CodigoOrigen) = UPPER(SKU_Oficial);
    """)

    # ======================================================
    # 3) LIMPIAR CÓDIGOS REDUNDANTES EN STAGING
    # ======================================================

    cur.execute("""
        UPDATE stg.Producto
        SET CodigoNeo4j = NULL
        WHERE CodigoNeo4j IS NOT NULL
          AND (CodigoNeo4j = SKU OR CodigoNeo4j = SKU_Oficial);
    """)
    cur.execute("""
        UPDATE stg.Producto
        SET CodigoAlterno = NULL
        WHERE CodigoAlterno IS NOT NULL
          AND (CodigoAlterno = SKU OR CodigoAlterno = SKU_Oficial);
    """)
    cur.execute("""
        UPDATE stg.Producto
        SET CodigoMongo = NULL
        WHERE CodigoMongo IS NOT NULL
          AND (CodigoMongo = SKU OR CodigoMongo = SKU_Oficial);
    """)

    # ======================================================
    # 4) DEFINIR SKU OFICIAL DESDE MSSQL
    # ======================================================
    cur.execute("""
        UPDATE p
        SET SKU_Oficial = p.SKU
        FROM stg.Producto p
        WHERE p.SourceSystem = 'MSSQL'
          AND p.SKU IS NOT NULL;
    """)

    # ======================================================
    # 5) HEREDAR SKU OFICIAL DESDE MSSQL
    # ======================================================
    cur.execute("""
        UPDATE p
        SET SKU_Oficial = m.SKU
        FROM stg.Producto p
        JOIN stg.Producto m
          ON m.Nombre = p.Nombre
         AND m.Categoria = p.Categoria
         AND m.SourceSystem = 'MSSQL'
        WHERE p.SKU_Oficial IS NULL;
    """)


    # ======================================================
    # 7) INSERTAR EN DIMPRODUCTO
    # ======================================================
    cur.execute("""
        WITH candidates AS (
            SELECT
                SKU_Oficial,
                MIN(COALESCE(Nombre, 'DESCONOCIDO')) AS Nombre,
                MIN(COALESCE(Categoria, 'SIN CATEGORIA')) AS Categoria,
                MIN(SourceSystem) AS SourceSystem
            FROM stg.Producto
            WHERE SKU_Oficial IS NOT NULL
            GROUP BY SKU_Oficial
        )
        INSERT INTO DimProducto (SKU, Nombre, Categoria, SourceSystem)
        SELECT
            c.SKU_Oficial,
            c.Nombre,
            c.Categoria,
            c.SourceSystem
        FROM candidates c
        WHERE NOT EXISTS (
            SELECT 1 FROM DimProducto d WHERE UPPER(d.SKU) = UPPER(c.SKU_Oficial)
        );
    """)

    # ======================================================
    # 6) INSERTAR EN MAPPRODUCTOEQUIVALENCIA 
    # ======================================================
    cur.execute("""
        INSERT INTO MapProductoEquivalencia (CodigoOrigen, SKU_Oficial, SourceSystem, TipoCodigo)
        SELECT s.CodigoOrigen, s.SKU_Oficial, s.SourceSystem, s.TipoCodigo
        FROM (
            SELECT
                UPPER(LTRIM(RTRIM(COALESCE(p.SKU, p.CodigoAlterno)))) AS CodigoOrigen,
                MIN(UPPER(LTRIM(RTRIM(p.SKU_Oficial)))) AS SKU_Oficial,
                UPPER(LTRIM(RTRIM(p.SourceSystem))) AS SourceSystem,
                CASE WHEN p.SKU IS NOT NULL THEN 'SKU' ELSE 'ALTERNO' END AS TipoCodigo
            FROM stg.Producto p
            WHERE p.SKU_Oficial IS NOT NULL
              AND COALESCE(p.SKU, p.CodigoAlterno) IS NOT NULL
            GROUP BY UPPER(LTRIM(RTRIM(COALESCE(p.SKU, p.CodigoAlterno)))), UPPER(LTRIM(RTRIM(p.SourceSystem))), CASE WHEN p.SKU IS NOT NULL THEN 'SKU' ELSE 'ALTERNO' END
        ) s
        WHERE NOT EXISTS (
            SELECT 1 FROM MapProductoEquivalencia m
            WHERE UPPER(LTRIM(RTRIM(m.CodigoOrigen))) = s.CodigoOrigen
              AND UPPER(LTRIM(RTRIM(m.SourceSystem))) = s.SourceSystem
              AND UPPER(LTRIM(RTRIM(m.TipoCodigo))) = s.TipoCodigo
        )
        AND EXISTS (
            SELECT 1 FROM DimProducto d WHERE UPPER(d.SKU) = UPPER(s.SKU_Oficial)
        );
    """)

    # Variantes específicas para MySQL: insertar la versión con prefijo ALT + zero-pad (ej. ALT0062)
    cur.execute("""
        INSERT INTO MapProductoEquivalencia (CodigoOrigen, SKU_Oficial, SourceSystem, TipoCodigo)
        SELECT s.CodigoAlt, s.SKU_Oficial, s.SourceSystem, s.TipoCodigo
        FROM (
            SELECT
                'ALT' + RIGHT('0000' + UPPER(CAST(UPPER(LTRIM(RTRIM(COALESCE(p.SKU, p.CodigoAlterno)))) AS VARCHAR(20))), 4) AS CodigoAlt,
                MIN(UPPER(LTRIM(RTRIM(p.SKU_Oficial)))) AS SKU_Oficial,
                'MYSQL' AS SourceSystem,
                'ALTERNO' AS TipoCodigo
            FROM stg.Producto p
            WHERE UPPER(p.SourceSystem) = 'MYSQL'
              AND p.SKU_Oficial IS NOT NULL
              AND COALESCE(p.SKU, p.CodigoAlterno) IS NOT NULL
            GROUP BY 'ALT' + RIGHT('0000' + UPPER(CAST(UPPER(LTRIM(RTRIM(COALESCE(p.SKU, p.CodigoAlterno)))) AS VARCHAR(20))), 4)
        ) s
        WHERE NOT EXISTS (
            SELECT 1 FROM MapProductoEquivalencia m
            WHERE UPPER(LTRIM(RTRIM(m.CodigoOrigen))) = s.CodigoAlt
              AND UPPER(LTRIM(RTRIM(m.SourceSystem))) = s.SourceSystem
              AND UPPER(LTRIM(RTRIM(m.TipoCodigo))) = s.TipoCodigo
        )
        AND EXISTS (
            SELECT 1 FROM DimProducto d WHERE UPPER(d.SKU) = UPPER(s.SKU_Oficial)
        );
    """)

    # También insertar la forma numérica (sin prefijo) por si los Source_Producto_Id vienen como números
    cur.execute("""
        INSERT INTO MapProductoEquivalencia (CodigoOrigen, SKU_Oficial, SourceSystem, TipoCodigo)
        SELECT s.CodigoOrigen, s.SKU_Oficial, s.SourceSystem, s.TipoCodigo
        FROM (
            SELECT
                UPPER(LTRIM(RTRIM(COALESCE(p.SKU, p.CodigoAlterno)))) AS CodigoOrigen,
                MIN(UPPER(LTRIM(RTRIM(p.SKU_Oficial)))) AS SKU_Oficial,
                'MYSQL' AS SourceSystem,
                CASE WHEN p.SKU IS NOT NULL THEN 'SKU' ELSE 'ALTERNO' END AS TipoCodigo
            FROM stg.Producto p
            WHERE UPPER(p.SourceSystem) = 'MYSQL'
              AND p.SKU_Oficial IS NOT NULL
              AND COALESCE(p.SKU, p.CodigoAlterno) IS NOT NULL
            GROUP BY UPPER(LTRIM(RTRIM(COALESCE(p.SKU, p.CodigoAlterno)))), CASE WHEN p.SKU IS NOT NULL THEN 'SKU' ELSE 'ALTERNO' END
        ) s
        WHERE NOT EXISTS (
            SELECT 1 FROM MapProductoEquivalencia m
            WHERE UPPER(LTRIM(RTRIM(m.CodigoOrigen))) = s.CodigoOrigen
              AND UPPER(LTRIM(RTRIM(m.SourceSystem))) = s.SourceSystem
              AND UPPER(LTRIM(RTRIM(m.TipoCodigo))) = s.TipoCodigo
        )
        AND EXISTS (
            SELECT 1 FROM DimProducto d WHERE UPPER(d.SKU) = UPPER(s.SKU_Oficial)
        );
    """)


    # ======================================================
    # 8) LIMPIAR DUPLICADOS HISTÓRICOS
    # ======================================================
    cur.execute("""
        WITH CTE AS (
            SELECT *,
                   ROW_NUMBER() OVER (
                       PARTITION BY SourceSystem, CodigoOrigen, TipoCodigo
                       ORDER BY SKU_Oficial
                   ) AS rn
            FROM MapProductoEquivalencia
        )
        DELETE FROM CTE WHERE rn > 1;
    """)

    # ======================================================
    # 9) MAPEO IDENTIDAD - MSSQL
    # ======================================================
    cur.execute("""
        INSERT INTO MapProductoEquivalencia (SKU_Oficial, SourceSystem, CodigoOrigen, TipoCodigo)
        SELECT DISTINCT
            p.SKU,
            'MSSQL',
            p.SKU,
            'SKU'
        FROM stg.Producto p
        WHERE p.SourceSystem = 'MSSQL'
          AND p.SKU IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM MapProductoEquivalencia m
              WHERE m.SourceSystem = 'MSSQL'
                AND m.CodigoOrigen = p.SKU
          );
    """)

    # ======================================================
    # 10) MAPEO IDENTIDAD - MYSQL
    # ======================================================
    cur.execute("""
        INSERT INTO MapProductoEquivalencia (SKU_Oficial, SourceSystem, CodigoOrigen, TipoCodigo)
        SELECT DISTINCT
            p.SKU_Oficial,
            'MYSQL',
            p.SKU_Oficial,
            'SKU'
        FROM stg.Producto p
        WHERE p.SourceSystem = 'MYSQL'
          AND p.SKU_Oficial IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM MapProductoEquivalencia m
              WHERE m.SourceSystem = 'MYSQL'
                AND m.CodigoOrigen = p.SKU_Oficial
          );
    """)

    # ======================================================
    # 11) MAPEO IDENTIDAD - SUPABASE
    # ======================================================
    cur.execute("""
        INSERT INTO MapProductoEquivalencia (SKU_Oficial, SourceSystem, CodigoOrigen, TipoCodigo)
        SELECT DISTINCT
            p.SKU_Oficial,
            'SUPABASE',
            p.SKU_Oficial,
            'SKU'
        FROM stg.Producto p
        WHERE p.SourceSystem = 'SUPABASE'
          AND p.SKU_Oficial IS NOT NULL
          AND NOT EXISTS (
              SELECT 1 FROM MapProductoEquivalencia m
              WHERE m.SourceSystem = 'SUPABASE'
                AND m.CodigoOrigen = p.SKU_Oficial
          );
    """)

    # ======================================================
    # 12) MAPEOS ADICIONALES (ALTERNO, MONGO, NEO4J)
    # ======================================================

    cur.execute("""
        MERGE MapProductoEquivalencia AS target
        USING (
            SELECT MIN(SKU_Oficial), SourceSystem, SKU, 'SKU'
            FROM stg.Producto
            WHERE SKU IS NOT NULL AND SKU <> SKU_Oficial
            GROUP BY SourceSystem, SKU
        ) AS s (SKU_Oficial, SourceSystem, CodigoOrigen, TipoCodigo)
        ON target.SourceSystem = s.SourceSystem
       AND target.CodigoOrigen = s.CodigoOrigen
       AND target.TipoCodigo = s.TipoCodigo
        WHEN NOT MATCHED THEN
          INSERT (SKU_Oficial, SourceSystem, CodigoOrigen, TipoCodigo)
          VALUES (s.SKU_Oficial, s.SourceSystem, s.CodigoOrigen, s.TipoCodigo);
    """)

    cur.execute("""
        MERGE MapProductoEquivalencia AS target
        USING (
            SELECT MIN(SKU_Oficial), SourceSystem, CodigoAlterno, 'ALTERNO'
            FROM stg.Producto
            WHERE CodigoAlterno IS NOT NULL AND CodigoAlterno <> SKU_Oficial
            GROUP BY SourceSystem, CodigoAlterno
        ) AS s (SKU_Oficial, SourceSystem, CodigoOrigen, TipoCodigo)
        ON target.SourceSystem = s.SourceSystem
       AND target.CodigoOrigen = s.CodigoOrigen
       AND target.TipoCodigo = s.TipoCodigo
        WHEN NOT MATCHED THEN
          INSERT (SKU_Oficial, SourceSystem, CodigoOrigen, TipoCodigo)
          VALUES (s.SKU_Oficial, s.SourceSystem, s.CodigoOrigen, s.TipoCodigo);
    """)

    cur.execute("""
        MERGE MapProductoEquivalencia AS target
        USING (
            SELECT MIN(SKU_Oficial), SourceSystem, CodigoMongo, 'MONGO'
            FROM stg.Producto
            WHERE CodigoMongo IS NOT NULL AND CodigoMongo <> SKU_Oficial
            GROUP BY SourceSystem, CodigoMongo
        ) AS s (SKU_Oficial, SourceSystem, CodigoOrigen, TipoCodigo)
        ON target.SourceSystem = s.SourceSystem
       AND target.CodigoOrigen = s.CodigoOrigen
       AND target.TipoCodigo = s.TipoCodigo
        WHEN NOT MATCHED THEN
          INSERT (SKU_Oficial, SourceSystem, CodigoOrigen, TipoCodigo)
          VALUES (s.SKU_Oficial, s.SourceSystem, s.CodigoOrigen, s.TipoCodigo);
    """)

    cur.execute("""
        MERGE MapProductoEquivalencia AS target
        USING (
            SELECT MIN(SKU_Oficial), SourceSystem, CodigoNeo4j, 'NEO4J'
            FROM stg.Producto
            WHERE CodigoNeo4j IS NOT NULL AND CodigoNeo4j <> SKU_Oficial
            GROUP BY SourceSystem, CodigoNeo4j
        ) AS s (SKU_Oficial, SourceSystem, CodigoOrigen, TipoCodigo)
        ON target.SourceSystem = s.SourceSystem
       AND target.CodigoOrigen = s.CodigoOrigen
       AND target.TipoCodigo = s.TipoCodigo
        WHEN NOT MATCHED THEN
          INSERT (SKU_Oficial, SourceSystem, CodigoOrigen, TipoCodigo)
          VALUES (s.SKU_Oficial, s.SourceSystem, s.CodigoOrigen, s.TipoCodigo);
    """)

    # ======================================================
    # 13) RETURN TOTAL
    # ======================================================
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
# ------------------------------------------------------------
def load_fact_ventas(cur):
    cur.execute("""
        SELECT 'MySQL' AS src, COUNT(*) AS total_rows, COUNT(DISTINCT Source_Order_Id) AS distinct_orders FROM stg.FactVentas_MySQL
        UNION ALL
        SELECT 'MSSQL', COUNT(*), COUNT(DISTINCT Source_Order_Id) FROM stg.FactVentas_MSSQL
        UNION ALL
        SELECT 'Mongo', COUNT(*), COUNT(DISTINCT Source_Order_Id) FROM stg.FactVentas_Mongo
        UNION ALL
        SELECT 'Neo4j', COUNT(*), COUNT(DISTINCT Source_Order_Id) FROM stg.FactVentas_Neo4j
        UNION ALL
        SELECT 'Supabase', COUNT(*), COUNT(DISTINCT Source_Order_Id) FROM stg.FactVentas_Supabase;
    """)
    for r in cur.fetchall():
        print("Staging:", r[0], "rows=", r[1], "distinct_orders=", r[2])

    cur.execute("""
        WITH union_all AS (
            SELECT SourceSystem, Source_Order_Id, Source_Cliente_Id, Source_Producto_Id, FechaOrden, Canal, MontoUSD, Cantidad, 'USD' AS MonedaOrigen, NULL AS DescuentoPct, NULL AS TipoCambioAplicado, NULL AS SKU_Oficial
            FROM stg.FactVentas_MySQL
            UNION ALL
            SELECT SourceSystem, Source_Order_Id, Source_Cliente_Id, Source_Producto_Id, FechaOrden, Canal, MontoUSD, Cantidad, 'USD', NULL, NULL, SKU_Oficial
            FROM stg.FactVentas_MSSQL
            UNION ALL
            SELECT SourceSystem, Source_Order_Id, Source_Cliente_Id, Source_Producto_Id, FechaOrden, Canal, MontoUSD, Cantidad, 'USD', NULL, NULL, SKU_Oficial
            FROM stg.FactVentas_Mongo
            UNION ALL
            SELECT SourceSystem, Source_Order_Id, Source_Cliente_Id, Source_Producto_Id, FechaOrden, Canal, MontoUSD, Cantidad, 'USD', NULL, NULL, SKU_Oficial
            FROM stg.FactVentas_Neo4j
            UNION ALL
            SELECT SourceSystem, Source_Order_Id, Source_Cliente_Id, Source_Producto_Id, FechaOrden, Canal, MontoUSD, Cantidad, 'USD', NULL, NULL, SKU_Oficial
            FROM stg.FactVentas_Supabase
        ), deduped AS (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY UPPER(LTRIM(RTRIM(SourceSystem))), UPPER(LTRIM(RTRIM(Source_Order_Id)))
                ORDER BY COALESCE(FechaOrden, '1900-01-01') DESC
            ) AS rn
            FROM union_all
        )
        SELECT SourceSystem, COUNT(*) FROM deduped WHERE rn = 1 GROUP BY SourceSystem;
    """)
    for r in cur.fetchall():
        print("Deduped staging (per order):", r[0], "rows=", r[1])

    # --- INSERTAR: solo una fila por orden, normalizada, y solo cuando los joins son iguales
    cur.execute("""
        WITH union_all AS (
            SELECT SourceSystem, Source_Order_Id, Source_Cliente_Id, Source_Producto_Id, FechaOrden, Canal, MontoUSD, Cantidad, 'USD' AS MonedaOrigen, NULL AS DescuentoPct, NULL AS TipoCambioAplicado, NULL AS SKU_Oficial
            FROM stg.FactVentas_MySQL
            UNION ALL
            SELECT SourceSystem, Source_Order_Id, Source_Cliente_Id, Source_Producto_Id, FechaOrden, Canal, MontoUSD, Cantidad, 'USD', NULL, NULL, SKU_Oficial
            FROM stg.FactVentas_MSSQL
            UNION ALL
            SELECT SourceSystem, Source_Order_Id, Source_Cliente_Id, Source_Producto_Id, FechaOrden, Canal, MontoUSD, Cantidad, 'USD', NULL, NULL, SKU_Oficial
            FROM stg.FactVentas_Mongo
            UNION ALL
            SELECT SourceSystem, Source_Order_Id, Source_Cliente_Id, Source_Producto_Id, FechaOrden, Canal, MontoUSD, Cantidad, 'USD', NULL, NULL, SKU_Oficial
            FROM stg.FactVentas_Neo4j
            UNION ALL
            SELECT SourceSystem, Source_Order_Id, Source_Cliente_Id, Source_Producto_Id, FechaOrden, Canal, MontoUSD, Cantidad, 'USD', NULL, NULL, SKU_Oficial
            FROM stg.FactVentas_Supabase
        ), deduped AS (
            SELECT *, ROW_NUMBER() OVER (
                PARTITION BY UPPER(LTRIM(RTRIM(SourceSystem))), UPPER(LTRIM(RTRIM(Source_Order_Id)))
                ORDER BY COALESCE(FechaOrden, '1900-01-01') DESC
            ) AS rn
            FROM union_all
        ), f AS (
            SELECT * FROM deduped WHERE rn = 1
        )

        INSERT INTO FactVentas (
            ClienteID, ProductoID, TiempoID, CanalID,
            OrdenKeyNatural, MonedaOrigen, TotalUSD, Cantidad,
            PrecioUnitUSD, DescuentoPct, TipoCambioAplicado, SourceSystem
        )
        SELECT
            dc.ClienteID,
            COALESCE(dp.ProductoID, (SELECT TOP 1 ProductoID FROM DimProducto WHERE SKU = '__UNKNOWN__')) AS ProductoID,
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
        FROM f

        INNER JOIN DimCliente dc
            ON dc.ClienteKeyNatural = f.Source_Cliente_Id
           AND dc.EsRegistroActual = 1
                

        OUTER APPLY (
            SELECT TOP 1 mpe.SKU_Oficial
            FROM MapProductoEquivalencia mpe
            WHERE UPPER(LTRIM(RTRIM(mpe.SourceSystem))) = UPPER(LTRIM(RTRIM(f.SourceSystem)))
            AND UPPER(LTRIM(RTRIM(mpe.CodigoOrigen))) =
                UPPER(LTRIM(RTRIM(
                        CASE 
                            WHEN f.SourceSystem = 'MSSQL' OR f.SourceSystem = 'SUPABASE'
                                THEN COALESCE(f.SKU_Oficial, f.Source_Producto_Id)
                            ELSE f.Source_Producto_Id
                        END
                )))
            ORDER BY mpe.SKU_Oficial
        ) skuMap



        LEFT JOIN DimProducto dp
            ON skuMap.SKU_Oficial IS NOT NULL
           AND UPPER(dp.SKU) = UPPER(skuMap.SKU_Oficial)


        INNER JOIN DimCanal dcan
            ON dcan.CodigoCanal = f.Canal

                WHERE NOT EXISTS (
            SELECT 1 FROM FactVentas fv
                        WHERE UPPER(LTRIM(RTRIM(fv.OrdenKeyNatural))) = UPPER(LTRIM(RTRIM(f.Source_Order_Id)))
                            AND UPPER(LTRIM(RTRIM(fv.SourceSystem))) = UPPER(LTRIM(RTRIM(f.SourceSystem)))
        );
    """)
    return cur.rowcount


def run_staging_to_dw():
    """
    Conecta al DW y ejecuta los pasos de carga (Dim y Fact),
    confiere commit/rollback y cierra la conexión.
    """
    conn = None
    try:
        conn = get_sqlsrv_dw_conn()
        cur = conn.cursor()

        print("Cargando DimCliente:", load_dim_cliente(cur))
        print("Cargando DimProducto:", load_dim_producto(cur))
        print("Cargando DimTiempo:", load_dim_tiempo(cur))
        print("Cargando DimCanal:", load_dim_canal(cur))
        print("Cargando FactVentas:", load_fact_ventas(cur))

        conn.commit()
    except Exception as e:
        if conn:
            conn.rollback()
        print("Error en run_staging_to_dw:", e)
        raise
    finally:
        if conn:
            conn.close()

