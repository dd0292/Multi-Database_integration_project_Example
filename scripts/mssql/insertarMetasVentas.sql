truncate table dbo.MetasVentas;
go
WITH TopClientes AS (
    SELECT TOP 50 ClienteID
    FROM DimCliente
    WHERE Nombre like 'Cliente MSSQL%'
	ORDER BY ClienteID
	
),
TopProductos AS (
    SELECT TOP 50 ProductoID
    FROM DimProducto
    ORDER BY ProductoID
),
Anios AS (
    SELECT 2024 AS Anio
    UNION ALL
    SELECT 2025
),
Meses AS (
    SELECT v AS Mes
    FROM (VALUES (1),(2),(3),(4),(5),(6),(7),(8),(9),(10),(11),(12)) M(v)
)

-- 2. Generar todas las combinaciones posibles
INSERT INTO MetasVentas (ClienteID, ProductoID, Anio, Mes, MetaUSD)
SELECT 
    c.ClienteID,
    p.ProductoID,
    a.Anio,
    m.Mes,
    -- Meta generada: entre 5,000 y 20,000 con ligera variación estacional
    CAST( (0 + (ABS(CHECKSUM(NEWID())) % 500)) AS DECIMAL(18,2)) 
FROM TopClientes c
CROSS JOIN TopProductos p
CROSS JOIN Anios a
CROSS JOIN Meses m;

--------------------------------------------------------------
-- Confirmación
--------------------------------------------------------------
SELECT COUNT(*) AS RegistrosInsertados
FROM MetasVentas;