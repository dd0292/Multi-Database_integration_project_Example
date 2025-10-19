-- Crear la base de datos del Data Warehouse
CREATE DATABASE DW;
GO

USE DW;
GO

-- Esquema para las tablas dimensionales y de hechos
CREATE SCHEMA dwh;
GO

-- Esquema para tablas de apoyo ETL
CREATE SCHEMA staging;
GO

-- ------------------------------------
-- TABLAS DE DIMENSIONES
-- ------------------------------------

-- DIMENSIÓN CLIENTE
CREATE TABLE dwh.DimCliente (
    ClienteID INT IDENTITY(1,1) PRIMARY KEY,
    ClienteID_Natural VARCHAR(100) NOT NULL,        -- Clave original de la fuente
    Nombre NVARCHAR(120) NOT NULL,
    Email NVARCHAR(150) NULL,
    Genero NVARCHAR(15) NOT NULL CHECK (Genero IN ('Masculino', 'Femenino', 'No Especificado')),
    Pais NVARCHAR(60) NOT NULL,
    FechaRegistro DATE NOT NULL,
    FuenteOrigen NVARCHAR(20) NOT NULL CHECK (FuenteOrigen IN ('SQL Server', 'MySQL', 'MongoDB', 'Supabase', 'Neo4j')),
    FechaCreacion DATETIME2 DEFAULT GETDATE(),
    FechaActualizacion DATETIME2 DEFAULT GETDATE()
);

-- DIMENSIÓN PRODUCTO
CREATE TABLE dwh.DimProducto (
    ProductoID INT IDENTITY(1,1) PRIMARY KEY,
    SKU_Oficial NVARCHAR(40) NOT NULL UNIQUE,       -- SKU unificado
    Nombre NVARCHAR(150) NOT NULL,
    Categoria NVARCHAR(80) NOT NULL,
    FuenteOrigen NVARCHAR(20) NOT NULL,
    FechaCreacion DATETIME2 DEFAULT GETDATE(),
    FechaActualizacion DATETIME2 DEFAULT GETDATE()
);

-- DIMENSIÓN TIEMPO (tabla de calendario)
CREATE TABLE dwh.DimTiempo (
    TiempoID INT PRIMARY KEY,                       -- Formato YYYYMMDD
    FechaCompleta DATE NOT NULL UNIQUE,
    Dia INT NOT NULL CHECK (Dia BETWEEN 1 AND 31),
    Mes INT NOT NULL CHECK (Mes BETWEEN 1 AND 12),
    Trimestre INT NOT NULL CHECK (Trimestre BETWEEN 1 AND 4),
    Año INT NOT NULL,
    NombreMes NVARCHAR(20) NOT NULL,
    NombreDiaSemana NVARCHAR(20) NOT NULL,
    DiaSemana INT NOT NULL CHECK (DiaSemana BETWEEN 1 AND 7),
    EsFinDeSemana BIT NOT NULL,                     -- 1 = Fin de semana, 0 = Día laboral
    MesAño NVARCHAR(7) NOT NULL,                    -- Formato 'YYYY-MM'
    FechaCreacion DATETIME2 DEFAULT GETDATE()
);

-- DIMENSIÓN CANAL
CREATE TABLE dwh.DimCanal (
    CanalID INT IDENTITY(1,1) PRIMARY KEY,
    NombreCanal NVARCHAR(20) NOT NULL UNIQUE,
    Descripcion NVARCHAR(100) NULL,
    FechaCreacion DATETIME2 DEFAULT GETDATE()
);

-- ------------------------------------
-- TABLA DE HECHOS PRINCIPAL
-- ------------------------------------

-- HECHOS DE VENTAS
CREATE TABLE dwh.FactVentas (
    VentaID BIGINT IDENTITY(1,1) PRIMARY KEY,
    TiempoID INT NOT NULL FOREIGN KEY REFERENCES dwh.DimTiempo(TiempoID),
    ClienteID INT NOT NULL FOREIGN KEY REFERENCES dwh.DimCliente(ClienteID),
    ProductoID INT NOT NULL FOREIGN KEY REFERENCES dwh.DimProducto(ProductoID),
    CanalID INT NOT NULL FOREIGN KEY REFERENCES dwh.DimCanal(CanalID),
    OrdenID_Natural VARCHAR(100) NOT NULL,          -- Clave original de la orden
    MonedaOrigen CHAR(3) NOT NULL CHECK (MonedaOrigen IN ('USD', 'CRC')),
    TotalVentaUSD DECIMAL(18,2) NOT NULL,
    Cantidad INT NOT NULL CHECK (Cantidad > 0),
    PrecioUnitUSD DECIMAL(18,2) NOT NULL,
    DescuentoPct DECIMAL(5,2) NULL CHECK (DescuentoPct BETWEEN 0 AND 100),
    TipoCambio DECIMAL(10,4) NULL,                  -- Tasa usada si la moneda era CRC
    FuenteOrigen NVARCHAR(20) NOT NULL,
    FechaCreacion DATETIME2 DEFAULT GETDATE()
);

-- ------------------------------------
-- APOYO ETLS
-- ------------------------------------
-- TABLA PUENTE PARA HOMOLOGACIÓN DE PRODUCTOS
CREATE TABLE staging.MapProducto (
    MapID INT IDENTITY(1,1) PRIMARY KEY,
    FuenteOrigen NVARCHAR(20) NOT NULL,
    CodigoFuente NVARCHAR(100) NOT NULL,            -- codigo_alt, codigo_mongo, etc.
    SKU_Oficial NVARCHAR(40) NOT NULL FOREIGN KEY REFERENCES dwh.DimProducto(SKU_Oficial),
    FechaCreacion DATETIME2 DEFAULT GETDATE(),
    UNIQUE (FuenteOrigen, CodigoFuente)             -- Evitar mapeos duplicados
);


-- ------------------------------------
-- OPTIONAL
-- ------------------------------------
-- Índices para FactVentas (consultas frecuentes)
CREATE INDEX IX_FactVentas_Tiempo ON dwh.FactVentas(TiempoID);
CREATE INDEX IX_FactVentas_Cliente ON dwh.FactVentas(ClienteID);
CREATE INDEX IX_FactVentas_Producto ON dwh.FactVentas(ProductoID);
CREATE INDEX IX_FactVentas_Canal ON dwh.FactVentas(CanalID);
CREATE INDEX IX_FactVentas_Fuente ON dwh.FactVentas(FuenteOrigen);

-- Índices para MetasVentas
CREATE INDEX IX_MetasVentas_ClienteProducto ON dwh.MetasVentas(ClienteID, ProductoID);
CREATE INDEX IX_MetasVentas_AnioMes ON dwh.MetasVentas(Año, Mes);

-- Índices para DimTiempo
CREATE INDEX IX_DimTiempo_Fecha ON dwh.DimTiempo(FechaCompleta);
CREATE INDEX IX_DimTiempo_AnioMes ON dwh.DimTiempo(Año, Mes);

-- Índices para tablas ETL
CREATE INDEX IX_MapProducto_SKU ON staging.MapProducto(SKU_Oficial);
