DECLARE @TotalOrdenes INT = 100;   -- cuántas órdenes quieres generar
DECLARE @FechaInicio DATE = '2025-01-01';
DECLARE @FechaFin DATE   = '2025-12-31';

-----------------------------------------------------
-- 1. Tomar 50 clientes aleatorios con email
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
Numeros AS (
    SELECT TOP (@TotalOrdenes) ROW_NUMBER() OVER(ORDER BY (SELECT NULL)) AS n
    FROM sys.objects
),
Ordenes AS (
    SELECT 
        n.n AS OrdenID,
        c.Email,
        DATEADD(
            DAY,
            ABS(CHECKSUM(NEWID())) % (1 + DATEDIFF(DAY, @FechaInicio, @FechaFin)),
            @FechaInicio
        ) AS Fecha,
        CASE (ABS(CHECKSUM(NEWID())) % 3)
            WHEN 0 THEN 'WEB'
            WHEN 1 THEN 'TIENDA'
            ELSE 'APP'
        END AS Canal,
        'USD' AS Moneda,
        (ABS(CHECKSUM(NEWID())) % 3) + 1 AS NumProductos  -- 1 a 3 productos
    FROM Numeros n
    CROSS JOIN Clientes c
)
-----------------------------------------------------
-- 2. Generar items aleatorios para cada orden (1 a 3 productos únicos)
-----------------------------------------------------
, Items AS (
    SELECT 
        o.OrdenID,
        p.ProductoID,
        Cantidad = (ABS(CHECKSUM(NEWID())) % 5) + 1,
        PrecioUnit = CAST(p.PrecioUnitario AS DECIMAL(10,2))
    FROM Ordenes o
    CROSS APPLY (
        SELECT ProductoID, PrecioUnitario,
               ROW_NUMBER() OVER(ORDER BY NEWID()) AS rn
        FROM Productos
    ) p
    WHERE p.rn <= o.NumProductos  -- limita a 1-3 productos por orden
)
-----------------------------------------------------
-- 3. Armar JSON final
-----------------------------------------------------
SELECT TOP (@TotalOrdenes)
    o.Email AS email,
    o.Fecha AS fecha,
    o.Canal AS canal,
    o.Moneda AS moneda,
    (
        SELECT TOP 2 
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