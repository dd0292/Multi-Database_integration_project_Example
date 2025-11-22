-------------------------------------------------------------------
-- CREAR SCHEMA STAGING
-------------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'stg')
    EXEC('CREATE SCHEMA stg');
GO


/******************************************************************
    STAGING PARA DIMENSIONES
******************************************************************/


-------------------------------------------------------------------
-- STAGING CLIENTE (unificado para todas las fuentes)
-------------------------------------------------------------------
IF OBJECT_ID('stg.Cliente','U') IS NOT NULL DROP TABLE stg.Cliente;
CREATE TABLE stg.Cliente (
    SourceSystem NVARCHAR(20) NOT NULL,
    SourceClienteID NVARCHAR(100) NOT NULL,
    Nombre NVARCHAR(120),
    Email NVARCHAR(150),
    Genero NVARCHAR(20),
    Pais NVARCHAR(60),
    FechaRegistro DATETIME NULL,
    FechaCarga DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE INDEX IX_stg_Cliente_Source
ON stg.Cliente (SourceSystem, SourceClienteID);
GO


-------------------------------------------------------------------
-- STAGING PRODUCTO
-------------------------------------------------------------------
IF OBJECT_ID('stg.Producto','U') IS NOT NULL DROP TABLE stg.Producto;
CREATE TABLE stg.Producto (
    SourceSystem NVARCHAR(20) NOT NULL,
    SourceProductoID NVARCHAR(100) NOT NULL,
    SKU NVARCHAR(40) NULL,
    CodigoAlterno NVARCHAR(80) NULL,
    CodigoMongo NVARCHAR(80) NULL,
    CodigoNeo4j NVARCHAR(80) NULL,
    Nombre NVARCHAR(150),
    Categoria NVARCHAR(80),
    FechaCarga DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE INDEX IX_stg_Producto_Source
ON stg.Producto (SourceSystem, SourceProductoID);
GO


-------------------------------------------------------------------
-- STAGING TIEMPO
-------------------------------------------------------------------
IF OBJECT_ID('stg.Tiempo','U') IS NOT NULL DROP TABLE stg.Tiempo;
CREATE TABLE stg.Tiempo (
    Fecha DATE NOT NULL,
    FechaCarga DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE INDEX IX_stg_Tiempo_Fecha
ON stg.Tiempo (Fecha);
GO


-------------------------------------------------------------------
-- STAGING CANAL
-------------------------------------------------------------------
IF OBJECT_ID('stg.Canal','U') IS NOT NULL DROP TABLE stg.Canal;
CREATE TABLE stg.Canal (
    SourceSystem NVARCHAR(20) NOT NULL,
    Canal NVARCHAR(20) NOT NULL,
    FechaCarga DATETIME2 NOT NULL DEFAULT SYSDATETIME()
);
GO

CREATE INDEX IX_stg_Canal_Source
ON stg.Canal (SourceSystem, Canal);
GO


-------------------------------------------------------------------
-- STAGING FACT VENTAS: MySQL
-------------------------------------------------------------------
IF OBJECT_ID('stg.FactVentas_MySQL','U') IS NOT NULL DROP TABLE stg.FactVentas_MySQL;
CREATE TABLE stg.FactVentas_MySQL (
    SourceSystem NVARCHAR(20),
    Source_Order_Id NVARCHAR(100),
    Source_Order_Detalle_Id NVARCHAR(100),
    Source_Cliente_Id NVARCHAR(100),
    Source_Producto_Id NVARCHAR(100),
    ClienteNombre NVARCHAR(120),
    ClienteGenero NVARCHAR(20),
    ClientePais NVARCHAR(60),
    ProductoNombre NVARCHAR(150),
    ProductoCategoria NVARCHAR(80),
    FechaOrden DATETIME,
    Canal NVARCHAR(20),
    MontoUSD DECIMAL(18,2),
    Cantidad INT,
    FechaCarga DATETIME2 DEFAULT SYSDATETIME()
);
GO


-------------------------------------------------------------------
-- STAGING FACT VENTAS: MongoDB
-------------------------------------------------------------------
IF OBJECT_ID('stg.FactVentas_Mongo','U') IS NOT NULL DROP TABLE stg.FactVentas_Mongo;
CREATE TABLE stg.FactVentas_Mongo (
    SourceSystem NVARCHAR(20),
    Source_Order_Id NVARCHAR(100),
    Source_Producto_Id NVARCHAR(100),
    Source_Cliente_Id NVARCHAR(100),
    SKU_Oficial NVARCHAR(40),
    ClienteNombre NVARCHAR(120),
    ClienteGenero NVARCHAR(20),
    ClientePais NVARCHAR(60),
    ProductoNombre NVARCHAR(150),
    ProductoCategoria NVARCHAR(80),
    FechaOrden DATETIME,
    Canal NVARCHAR(20),
    MontoUSD DECIMAL(18,2),
    Cantidad INT,
    FechaCarga DATETIME2 DEFAULT SYSDATETIME()
);
GO


-------------------------------------------------------------------
-- STAGING FACT VENTAS: SQL Server Transaccional
-------------------------------------------------------------------
IF OBJECT_ID('stg.FactVentas_MSSQL','U') IS NOT NULL DROP TABLE stg.FactVentas_MSSQL;
CREATE TABLE stg.FactVentas_MSSQL (
    SourceSystem NVARCHAR(20),
    Source_Order_Id NVARCHAR(100),
    Source_Producto_Id NVARCHAR(100),
    Source_Cliente_Id NVARCHAR(100),
    SKU_Oficial NVARCHAR(40),
    ClienteNombre NVARCHAR(120),
    ClienteGenero NVARCHAR(20),
    ClientePais NVARCHAR(60),
    ProductoNombre NVARCHAR(150),
    ProductoCategoria NVARCHAR(80),
    FechaOrden DATETIME,
    Canal NVARCHAR(20),
    MontoUSD DECIMAL(18,2),
    Cantidad INT,
    FechaCarga DATETIME2 DEFAULT SYSDATETIME()
);
GO


-------------------------------------------------------------------
-- STAGING FACT VENTAS: Neo4j
-------------------------------------------------------------------
IF OBJECT_ID('stg.FactVentas_Neo4j','U') IS NOT NULL DROP TABLE stg.FactVentas_Neo4j;
CREATE TABLE stg.FactVentas_Neo4j (
    SourceSystem NVARCHAR(20),
    Source_Order_Id NVARCHAR(100),
    Source_Producto_Id NVARCHAR(100),
    Source_Cliente_Id NVARCHAR(100),
    SKU_Oficial NVARCHAR(40),
    ClienteNombre NVARCHAR(120),
    ClienteGenero NVARCHAR(20),
    ClientePais NVARCHAR(60),
    ProductoNombre NVARCHAR(150),
    ProductoCategoria NVARCHAR(80),
    FechaOrden DATETIME,
    Canal NVARCHAR(20),
    MontoUSD DECIMAL(18,2),
    Cantidad INT,
    FechaCarga DATETIME2 DEFAULT SYSDATETIME()
);
GO


-------------------------------------------------------------------
-- STAGING FACT VENTAS: Supabase
-------------------------------------------------------------------
IF OBJECT_ID('stg.FactVentas_Supabase','U') IS NOT NULL DROP TABLE stg.FactVentas_Supabase;
CREATE TABLE stg.FactVentas_Supabase (
    SourceSystem NVARCHAR(20),
    Source_Order_Id NVARCHAR(100),
    Source_Producto_Id NVARCHAR(100),
    Source_Cliente_Id NVARCHAR(100),
    SKU_Oficial NVARCHAR(40),
    ClienteNombre NVARCHAR(120),
    ClienteGenero NVARCHAR(20),
    ClientePais NVARCHAR(60),
    ProductoNombre NVARCHAR(150),
    ProductoCategoria NVARCHAR(80),
    FechaOrden DATETIME,
    Canal NVARCHAR(20),
    MontoUSD DECIMAL(18,2),
    Cantidad INT,
    FechaCarga DATETIME2 DEFAULT SYSDATETIME()
);
GO


-------------------------------------------------------------------
-- STAGING TIPO DE CAMBIO
-------------------------------------------------------------------
IF OBJECT_ID('stg.Tipo_Cambio','U') IS NOT NULL DROP TABLE stg.Tipo_Cambio;
CREATE TABLE stg.Tipo_Cambio (
    Fecha DATE NOT NULL,
    De CHAR(3) NOT NULL,
    A CHAR(3) NOT NULL,
    Tasa DECIMAL(12,6) NOT NULL,
    Fuente NVARCHAR(50) DEFAULT 'BCCR',
    FechaCarga DATETIME2 DEFAULT SYSDATETIME(),
    UNIQUE (Fecha, De, A)
);
GO

