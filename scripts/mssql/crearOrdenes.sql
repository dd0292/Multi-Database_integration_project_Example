DECLARE @TotalOrdenes INT = 20;
DECLARE @FechaInicio DATE = '2024-06-01';
DECLARE @FechaFin   DATE = '2025-12-31';

;WITH Clientes AS (
    SELECT TOP (50)
        ClienteID,
        Email,
        rn = ROW_NUMBER() OVER (ORDER BY NEWID())
    FROM Cliente
    WHERE Email IS NOT NULL
),
ClienteCount AS (
    SELECT MAX(rn) AS cnt FROM Clientes
),
Productos AS (
    SELECT ProductoID, PrecioUnitario = ABS(CHECKSUM(NEWID()) % 15000 / 1.0)
    FROM Producto
),
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
                  + (ABS(CHECKSUM(NEWID())) % 5),
                  @FechaInicio
                )
    FROM Numeros
),
Ordenes AS (
    SELECT
        s.n AS OrdenID,
        c.Email,
        CAST(s.Fecha AS DATE) AS Fecha,
        CASE ABS(CHECKSUM(NEWID())) % 3 
            WHEN 0 THEN 'WEB'
            WHEN 1 THEN 'TIENDA'
            ELSE 'APP'
        END AS Canal,
        'USD' AS Moneda,
        (ABS(CHECKSUM(NEWID())) % 3) + 1 AS NumProductos
    FROM SpreadDates s
    CROSS JOIN ClienteCount cc
    JOIN Clientes c
        ON c.rn = ((ABS(CHECKSUM(NEWID(), s.n)) % cc.cnt) + 1)
),
Items AS (
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
    WHERE p.rn <= o.NumProductos
),
OrderesWithItems AS (
    SELECT 
        o.OrdenID,
        o.Email,
        o.Fecha,
        o.Canal,
        o.Moneda,
        itemsJson = (
            SELECT 
                i.ProductoID AS producto_id,
                i.Cantidad AS cantidad,
                i.PrecioUnit AS precio_unit
            FROM Items i
            WHERE i.OrdenID = o.OrdenID
            FOR JSON PATH
        )
    FROM Ordenes o
)
SELECT 
    Email AS email,
    Fecha AS fecha,
    Canal AS canal,
    Moneda AS moneda,
    itemsJson AS items
FROM OrderesWithItems
WHERE itemsJson IS NOT NULL  -- filter out orders with no items
ORDER BY Fecha
FOR JSON PATH, WITHOUT_ARRAY_WRAPPER;
