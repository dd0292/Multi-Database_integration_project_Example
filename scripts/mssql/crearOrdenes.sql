DECLARE @TotalOrdenes INT = 100;
DECLARE @FechaInicio DATE = '2025-01-01';
DECLARE @FechaFin   DATE = '2025-6-30';

-----------------------------------------------------
-- 1. Select 50 random clients
-----------------------------------------------------
;WITH Clientes AS (
    SELECT TOP 50 ClienteID, Email
    FROM Cliente
    WHERE Email IS NOT NULL
    ORDER BY NEWID()
),
Productos AS (
    SELECT ProductoID, PrecioUnitario = ABS(CHECKSUM(NEWID()) % 15000 / 1.0)
    FROM Producto
),

-----------------------------------------------------
-- 2. Generate evenly spread dates (1 date per order)
-----------------------------------------------------
Numeros AS (
    SELECT TOP (@TotalOrdenes)
           ROW_NUMBER() OVER (ORDER BY (SELECT NULL)) AS n
    FROM sys.objects
),
SpreadDates AS (
    SELECT 
        n,
        Fecha = DATEADD(
                    DAY,
                    (DATEDIFF(DAY, @FechaInicio, @FechaFin) * (n-1)) / @TotalOrdenes
                    + (ABS(CHECKSUM(NEWID())) % 5), -- jitter
                @FechaInicio)
    FROM Numeros
),

-----------------------------------------------------
-- 3. Create one order per date (matching a random client)
-----------------------------------------------------
Ordenes AS (
    SELECT
        s.n AS OrdenID,
        c.Email,
        s.Fecha,
        CASE ABS(CHECKSUM(NEWID())) % 3 
            WHEN 0 THEN 'WEB'
            WHEN 1 THEN 'TIENDA'
            ELSE 'APP'
        END AS Canal,
        'USD' AS Moneda,
        (ABS(CHECKSUM(NEWID())) % 3) + 1 AS NumProductos
    FROM SpreadDates s
    CROSS APPLY (
        SELECT TOP 1 Email FROM Clientes ORDER BY NEWID()
    ) c
),

-----------------------------------------------------
-- 4. Generate 1–3 items per order
-----------------------------------------------------
Items AS (
    SELECT 
        o.OrdenID,
        p.ProductoID,
        Cantidad = (ABS(CHECKSUM(NEWID())) % 5) + 1,
        PrecioUnit = CAST(p.PrecioUnitario AS DECIMAL(10,2))
    FROM Ordenes o
    CROSS APPLY (
        SELECT ProductoID, PrecioUnitario,
               ROW_NUMBER() OVER (ORDER BY NEWID()) AS rn
        FROM Productos
    ) p
    WHERE p.rn <= o.NumProductos
)

-----------------------------------------------------
-- 5. Final JSON
-----------------------------------------------------
SELECT 
    o.Email AS email,
    o.Fecha AS fecha,
    o.Canal AS canal,
    o.Moneda AS moneda,
    (
        SELECT 
            i.ProductoID AS producto_id,
            i.Cantidad AS cantidad,
            i.PrecioUnit AS precio_unit
        FROM Items i
        WHERE i.OrdenID = o.OrdenID
        FOR JSON PATH
    ) AS items
FROM Ordenes o
ORDER BY o.Fecha
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
