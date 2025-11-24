CREATE VIEW dwh.vwAprioriDataset AS
SELECT 
    OrdenID_Natural AS Transaccion,
    ProductoID
FROM dwh.FactVentas;
