-- Crear base de datos del Data Warehouse
CREATE DATABASE Ventas_DW;
GO

USE Ventas_DW;
GO

-- Tabla Dimensión Cliente
CREATE TABLE DimCliente (
    ClienteID INT IDENTITY(1,1) PRIMARY KEY,
    ClienteKeyNatural NVARCHAR(100), -- ID original del sistema fuente
    Nombre NVARCHAR(120) NOT NULL,
    Email NVARCHAR(150),
    Genero NVARCHAR(15) NOT NULL CHECK (Genero IN ('M','F','X')),
    Pais NVARCHAR(60) NOT NULL,
    FechaRegistro DATE NOT NULL,
    SourceSystem NVARCHAR(20) , -- Sistema de origen (SQL Server, MySQL, etc.)
    FechaInicioValidez DATE NOT NULL DEFAULT (GETDATE()),
    FechaFinValidez DATE NULL,
    EsRegistroActual BIT NOT NULL DEFAULT 1
);

-- Tabla Dimensión Producto
CREATE TABLE DimProducto (
    ProductoID INT IDENTITY(1,1) PRIMARY KEY,
    SKU NVARCHAR(40) NOT NULL, -- SKU oficial unificado
    Nombre NVARCHAR(150) NOT NULL,
    Categoria NVARCHAR(80) NOT NULL,
    SourceSystem NVARCHAR(20),
    FechaInicioValidez DATE NOT NULL DEFAULT (GETDATE()),
    FechaFinValidez DATE NULL,
    EsRegistroActual BIT NOT NULL DEFAULT 1
);

-- Tabla Dimensión Tiempo
CREATE TABLE DimTiempo (
    TiempoID INT PRIMARY KEY, -- Formato YYYYMMDD
    Fecha DATE NOT NULL UNIQUE,
    Anio INT NOT NULL,
    Semestre INT NOT NULL CHECK (Semestre IN (1,2)),
    Trimestre INT NOT NULL CHECK (Trimestre IN (1,2,3,4)),
    Mes INT NOT NULL CHECK (Mes BETWEEN 1 AND 12),
    NombreMes NVARCHAR(20) NOT NULL,
    Dia INT NOT NULL CHECK (Dia BETWEEN 1 AND 31),
    DiaSemana INT NOT NULL CHECK (DiaSemana BETWEEN 1 AND 7),
    NombreDiaSemana NVARCHAR(15) NOT NULL,
    EsFinDeSemana BIT NOT NULL,
    MesAnio NVARCHAR(7) NOT NULL -- Formato 'YYYY-MM'
);

-- Tabla Dimensión Canal
CREATE TABLE DimCanal (
    CanalID INT IDENTITY(1,1) PRIMARY KEY,
    CodigoCanal NVARCHAR(20) NOT NULL UNIQUE,
    NombreCanal NVARCHAR(50) NOT NULL,
    Descripcion NVARCHAR(100) NULL
);

-- Tabla de Hechos Ventas
CREATE TABLE FactVentas (
    VentaID BIGINT IDENTITY(1,1) PRIMARY KEY,
    ClienteID INT NOT NULL FOREIGN KEY REFERENCES DimCliente(ClienteID),
    ProductoID INT NOT NULL FOREIGN KEY REFERENCES DimProducto(ProductoID),
    TiempoID INT NOT NULL FOREIGN KEY REFERENCES DimTiempo(TiempoID),
    CanalID INT NOT NULL FOREIGN KEY REFERENCES DimCanal(CanalID),
    OrdenKeyNatural NVARCHAR(100), -- ID original de la orden
    MonedaOrigen CHAR(3) NOT NULL, -- Moneda original de la transacción
    TotalUSD DECIMAL(18,2) NOT NULL, -- Total convertido a USD
    Cantidad INT NOT NULL CHECK (Cantidad > 0),
    PrecioUnitUSD DECIMAL(18,2) NOT NULL, -- Precio unitario en USD
    DescuentoPct DECIMAL(5,2) NULL,
    TipoCambioAplicado DECIMAL(12,6) NULL, -- Tasa de cambio aplicada
    SourceSystem NVARCHAR(20) NOT NULL,
    FechaCarga DATETIME2 NOT NULL DEFAULT (SYSDATETIME())
);

-- Tabla de Metas de Ventas
CREATE TABLE MetasVentas (
    MetaID INT IDENTITY(1,1) PRIMARY KEY,
    ClienteID INT NOT NULL FOREIGN KEY REFERENCES DimCliente(ClienteID),
    ProductoID INT NOT NULL FOREIGN KEY REFERENCES DimProducto(ProductoID),
    Anio INT NOT NULL,
    Mes INT NOT NULL CHECK (Mes BETWEEN 1 AND 12),
    MetaUSD DECIMAL(18,2) NOT NULL,
    FechaCreacion DATETIME2 NOT NULL DEFAULT (SYSDATETIME()),
    UsuarioCreacion NVARCHAR(50) NOT NULL DEFAULT (SYSTEM_USER)
);

-- Tabla de Tipos de Cambio
CREATE TABLE TipoCambio (
    TipoCambioID INT IDENTITY(1,1) PRIMARY KEY,
    Fecha DATE NOT NULL,
    MonedaOrigen CHAR(3) NOT NULL DEFAULT 'CRC',
    MonedaDestino CHAR(3) NOT NULL DEFAULT 'USD',
    TasaCambio DECIMAL(12,6) NOT NULL,
    Fuente NVARCHAR(50) NOT NULL DEFAULT 'BCCR',
    FechaCarga DATETIME2 NOT NULL DEFAULT (SYSDATETIME()),
    UNIQUE (Fecha, MonedaOrigen, MonedaDestino)
);

-- Tabla puente para homologación de productos
CREATE TABLE MapProductoEquivalencia (
    EquivalenciaID INT IDENTITY(1,1) PRIMARY KEY,
    SKU_Oficial NVARCHAR(40) NOT NULL FOREIGN KEY REFERENCES DimProducto(SKU),
    SourceSystem NVARCHAR(20) ,
    CodigoOrigen NVARCHAR(100) NOT NULL, -- codigo_alt, codigo_mongo, etc.
    TipoCodigo NVARCHAR(20) NOT NULL, -- 'ALTERNO', 'MONGO', 'NEO4J'
    FechaMapeo DATE NOT NULL DEFAULT (GETDATE()),
    EsActivo BIT NOT NULL DEFAULT 1,
    UNIQUE (SourceSystem, CodigoOrigen, TipoCodigo)
);

-- Índices para optimización
CREATE INDEX IX_FactVentas_Tiempo ON FactVentas(TiempoID);
CREATE INDEX IX_FactVentas_Cliente ON FactVentas(ClienteID);
CREATE INDEX IX_FactVentas_Producto ON FactVentas(ProductoID);
CREATE INDEX IX_FactVentas_Canal ON FactVentas(CanalID);
CREATE INDEX IX_MetasVentas_ClienteProducto ON MetasVentas(ClienteID, ProductoID);
CREATE INDEX IX_MetasVentas_AnioMes ON MetasVentas(Anio, Mes);
CREATE INDEX IX_TipoCambio_Fecha ON TipoCambio(Fecha);
CREATE INDEX IX_DimCliente_KeyNatural ON DimCliente(ClienteKeyNatural, SourceSystem);
CREATE INDEX IX_MapProducto_Codigos ON MapProductoEquivalencia(CodigoOrigen, SourceSystem);