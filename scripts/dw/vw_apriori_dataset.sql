CREATE OR ALTER VIEW vwAprioriDataset
AS
SELECT
    -- Cada orden es una transacción
    fv.OrdenKeyNatural AS Transaccion,

    -- Producto comprado
    fv.ProductoID,

    -- De qué origen viene (MSSQL, MYSQL, MONGO, NEO4J, SUPABASE)
    fv.SourceSystem

FROM FactVentas fv
WHERE fv.ProductoID IS NOT NULL
  AND fv.OrdenKeyNatural IS NOT NULL;
GO