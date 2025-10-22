CREATE DATABASE DW_SALES COLLATE SQL_Latin1_General_CP1_CI_AS; --COLLATE por si hay default distinto
GO
-- CHANGE PATHs ON LINES WITH BULK (Ctrl+F) 
USE DW_SALES;
GO
-- __________________________________________________________________
-- Crear tablas de dimensiones y hechos
-- __________________________________________________________________
-- DimDate
CREATE TABLE DimDate (
    DateKey INT PRIMARY KEY, -- YYYYMMDD
    DateValue DATE NOT NULL,
    [Year] INT,
    [Quarter] INT,
    [Month] INT,
    [Day] INT,
    MonthName NVARCHAR(20),
    QuarterName NVARCHAR(10),
    IsBusinessDay BIT,
    FiscalYear INT,
    TipoCambio_USD_CRC DECIMAL(18,6) NULL
);
-- DimCustomer
CREATE TABLE DimCustomer (
    CustomerKey INT IDENTITY(1,1) PRIMARY KEY,
    CardCode NVARCHAR(50) UNIQUE,
    CardName NVARCHAR(200),
    CardType CHAR(1),
    Zone NVARCHAR(100),
    Country NVARCHAR(100)
);

-- DimProduct
CREATE TABLE DimProduct (
    ProductKey INT IDENTITY(1,1) PRIMARY KEY,
    ItemCode NVARCHAR(50) UNIQUE,
    ItemName NVARCHAR(200),
    Brand NVARCHAR(100),
    OnHand DECIMAL(18,4),
    AvgPrice DECIMAL(18,4)
);

-- DimCurrency
CREATE TABLE DimCurrency (
    CurrencyKey INT IDENTITY(1,1) PRIMARY KEY,
    CurrencyCode NVARCHAR(10), -- e.g. 'COL','USD',
    Description NVARCHAR(100)
);

-- Fact_Sales
CREATE TABLE Fact_Sales (
    SalesKey BIGINT IDENTITY(1,1) PRIMARY KEY,
    DateKey INT NOT NULL,
    CustomerKey INT NULL,
    ProductKey INT NULL,
    CurrencyKey INT NULL,
    Qty DECIMAL(18,4) DEFAULT 0,
    UnitPrice DECIMAL(18,4) DEFAULT 0,
    DocTotal_CRC DECIMAL(18,4) DEFAULT 0,
    DocTotal_USD DECIMAL(18,4) DEFAULT 0,
    InsertedAt DATETIME2 DEFAULT SYSUTCDATETIME()
);
-- __________________________________________________________________
-- Llenado de dimensiones
-- __________________________________________________________________
USE DW_SALES;
GO

DECLARE @start DATE = '2024-01-01';
DECLARE @end DATE   = '2025-12-31';

;WITH dates AS (
    SELECT @start AS d
    UNION ALL
    SELECT DATEADD(day,1,d)
    FROM dates
    WHERE DATEADD(day,1,d) <= @end
)
INSERT INTO DimDate (DateKey, DateValue, [Year], [Quarter], [Month], [Day], MonthName, QuarterName, IsBusinessDay, FiscalYear)
SELECT
    CONVERT(INT, FORMAT(d,'yyyyMMdd')) AS DateKey,
    d AS DateValue,
    YEAR(d),
    DATEPART(quarter,d),
    MONTH(d),
    DAY(d),
    DATENAME(month,d),
    'Q' + CONVERT(VARCHAR(1),DATEPART(quarter,d)),
    CASE WHEN DATEPART(weekday,d) IN (1,7) THEN 0 ELSE 1 END,
    YEAR(d)
FROM dates
OPTION (MAXRECURSION 0);

CREATE TABLE DW_SALES.dbo.TC_Staging (
    Fecha DATE,
    TipoCambio_USD_CRC DECIMAL(18,6)
);

BULK INSERT TC_Staging
FROM '<YOUR PATH>\TIPOS_DE_CAMBIO.csv'
WITH (
    FIRSTROW = 2,
    FIELDTERMINATOR = ',',
    ROWTERMINATOR = '\n',
    CODEPAGE = '65001'
);

UPDATE d
SET d.TipoCambio_USD_CRC = t.TipoCambio_USD_CRC
FROM DimDate d
JOIN TC_Staging t ON d.DateValue = t.Fecha;

-- (Opcional)
;WITH MissingRates AS (
    SELECT d.DateValue, d.DateKey
    FROM DimDate d
    WHERE d.TipoCambio_USD_CRC IS NULL
)
UPDATE d
SET TipoCambio_USD_CRC = (
    SELECT TOP 1 t.TipoCambio_USD_CRC
    FROM TC_Staging t
    WHERE t.Fecha < d.DateValue
    ORDER BY t.Fecha DESC
)
FROM DimDate d
WHERE d.TipoCambio_USD_CRC IS NULL;

IF OBJECT_ID('DW_SALES.dbo.TC_Staging','U') IS NOT NULL
    DROP TABLE DW_SALES.dbo.TC_Staging;
GO


INSERT INTO DimCustomer (CardCode, CardName, CardType, Zone, Country)
VALUES ('AGG000','AGGREGATED_CLIENT','C', NULL, NULL);

INSERT INTO DimCustomer (CardCode, CardName, CardType, Zone, Country)
SELECT DISTINCT
    o.CardCode,
    o.CardName,
    o.CardType,
    zon.Code,
    o.Country
FROM DB_SALES.dbo.OCRD o
LEFT JOIN DB_SALES.dbo.ZONAS zon ON o.U_Zona = zon.Code
WHERE o.CardType IN ('C','S'); 
GO
INSERT INTO DimProduct (ItemCode, ItemName, Brand, OnHand, AvgPrice)
SELECT DISTINCT
    i.ItemCode,
    i.ItemName,
    i.u_mARCA,
    i.OnHand,
    o.AvgPrice
FROM DB_SALES.dbo.OITM AS i
LEFT JOIN DB_SALES.dbo.OITW o ON i.ItemCode = o.ItemCode
GO
INSERT INTO DimCurrency (CurrencyCode, Description)
VALUES ('COL','Colones'),
       ('USD','Dólares');
GO
USE DW_SALES;
GO

-- __________________________________________________________________
-- Llenado de Fact_Sales desde tablas de DB_SALES
-- __________________________________________________________________

INSERT INTO Fact_Sales (
    DateKey, CustomerKey, ProductKey, CurrencyKey,
    Qty, UnitPrice, DocTotal_CRC, DocTotal_USD
)
SELECT
    CONVERT(INT, FORMAT(o.DocDate,'yyyyMMdd')) AS DateKey,
    COALESCE(c.CustomerKey, agg.CustomerKey) AS CustomerKey,
    p.ProductKey,
    cur.CurrencyKey,
    inv.Quantity,
    inv.Price,
    o.DocTotal,
    o.DocTotalFC
FROM DB_SALES.dbo.INV1 inv
JOIN DB_SALES.dbo.OINV o ON inv.DocEntry = o.DocEntry
LEFT JOIN DimCustomer c ON c.CardCode = o.CardCode
LEFT JOIN DimProduct p ON p.ItemCode = inv.ItemCode
LEFT JOIN DimCurrency cur ON cur.CurrencyCode = COALESCE(o.DocCur,'COL')
LEFT JOIN DimDate dd ON dd.DateValue = CAST(o.DocDate AS DATE)
CROSS JOIN (SELECT CustomerKey FROM DimCustomer WHERE CardCode = 'AGG000') AS agg;
GO
INSERT INTO Fact_Sales (
    DateKey, CustomerKey, ProductKey, CurrencyKey,
    Qty, UnitPrice, DocTotal_CRC, DocTotal_USD
)
SELECT
    CONVERT(INT, FORMAT(o.DocDate,'yyyyMMdd')) AS DateKey,
    COALESCE(c.CustomerKey, agg.CustomerKey) AS CustomerKey,
    p.ProductKey,
    cur.CurrencyKey,
    -1 * rin.Quantity,
    rin.Price,
    -1 * o.DocTotal,
    -1 * o.DocTotalFC
FROM DB_SALES.dbo.RIN1 rin
JOIN DB_SALES.dbo.ORIN o ON rin.DocEntry = o.DocEntry
LEFT JOIN DimCustomer c ON c.CardCode = o.CardCode
LEFT JOIN DimProduct p ON p.ItemCode = rin.ItemCode
LEFT JOIN DimCurrency cur ON cur.CurrencyCode = COALESCE(o.DocCur,'COL')
LEFT JOIN DimDate dd ON dd.DateValue = CAST(o.DocDate AS DATE)
CROSS JOIN (SELECT CustomerKey FROM DimCustomer WHERE CardCode = 'AGG000') AS agg;
GO

-- __________________________________________________________________
-- AGG_VENTAS_USD.json processing 
-- __________________________________________________________________

DECLARE @json NVARCHAR(MAX);
SELECT @json = BulkColumn
FROM OPENROWSET(BULK '<YOUR PATH>\AGG_VENTAS_USD.json', SINGLE_CLOB) AS j;

-- Expand JSON: year, month, and each internal sale
SELECT 
    a.anio,
    a.mes,
    v.[item],
    v.[cantidad],
    v.[precio],
    v.[cantidad] * v.[precio] AS TotalUSD
INTO #tmpAggJson
FROM OPENJSON(@json)
WITH (
    anio INT '$.anio',
    mes INT '$.mes',
    ventas NVARCHAR(MAX) AS JSON
) AS a
CROSS APPLY OPENJSON(a.ventas)
WITH (
    [item] NVARCHAR(50) '$.item',
    [cantidad] DECIMAL(18,4) '$.cantidad',
    [precio] DECIMAL(18,4) '$.precio'
) AS v;

-- Check
SELECT TOP 10 * FROM #tmpAggJson;

INSERT INTO Fact_Sales (
    DateKey, CustomerKey, ProductKey, CurrencyKey,
    Qty, UnitPrice, DocTotal_CRC, DocTotal_USD
)
SELECT
    CONVERT(INT, FORMAT(DATEFROMPARTS(t.anio, t.mes, 1),'yyyyMMdd')) AS DateKey,
    agg.CustomerKey, 
    p.ProductKey,
    cur.CurrencyKey,
    t.cantidad,
    t.precio,
    (t.cantidad * t.precio) * COALESCE(dd.TipoCambio_USD_CRC,1) AS DocTotal_CRC,
    (t.cantidad * t.precio) AS DocTotal_USD
FROM #tmpAggJson t
LEFT JOIN DimProduct p ON p.ItemCode = t.item
CROSS JOIN (SELECT CustomerKey FROM DimCustomer WHERE CardCode = 'AGG000') AS agg
LEFT JOIN DimCurrency cur ON cur.CurrencyCode = 'USD'
LEFT JOIN DimDate dd ON dd.DateValue = DATEFROMPARTS(t.anio, t.mes, 1);
GO