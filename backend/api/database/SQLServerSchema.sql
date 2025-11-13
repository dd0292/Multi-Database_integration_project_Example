-- Crear base de datos transaccional
CREATE DATABASE Ventas_Transactional;
GO

USE Ventas_Transactional;
GO

-- Tabla Cliente
CREATE TABLE Cliente (
    ClienteId INT IDENTITY(1,1) PRIMARY KEY,
    Nombre NVARCHAR(120) NOT NULL,
    Email NVARCHAR(150) UNIQUE,
    Genero NVARCHAR(12) CHECK (Genero IN ('Masculino','Femenino')),
    Pais NVARCHAR(60) NOT NULL,
    FechaRegistro DATE NOT NULL DEFAULT (GETDATE()),
    Activo BIT NOT NULL DEFAULT 1
);

-- Tabla Producto
CREATE TABLE Producto (
    ProductoId INT IDENTITY(1,1) PRIMARY KEY,
    SKU NVARCHAR(40) UNIQUE NOT NULL,
    Nombre NVARCHAR(150) NOT NULL,
    Categoria NVARCHAR(80) NOT NULL,
    Activo BIT NOT NULL DEFAULT 1
);

-- Tabla Orden
CREATE TABLE Orden (
    OrdenId INT IDENTITY(1,1) PRIMARY KEY,
    ClienteId INT NOT NULL FOREIGN KEY REFERENCES dbo.Cliente(ClienteId),
    Fecha DATETIME2 NOT NULL DEFAULT (SYSDATETIME()),
    Canal NVARCHAR(20) NOT NULL CHECK (Canal IN ('WEB','TIENDA','APP')),
    Moneda CHAR(3) NOT NULL DEFAULT 'USD',
    Total DECIMAL(18,2) NOT NULL,
    Activo BIT NOT NULL DEFAULT 1
);

-- Tabla OrdenDetalle
CREATE TABLE OrdenDetalle (
    OrdenDetalleId INT IDENTITY(1,1) PRIMARY KEY,
    OrdenId INT NOT NULL FOREIGN KEY REFERENCES dbo.Orden(OrdenId),
    ProductoId INT NOT NULL FOREIGN KEY REFERENCES dbo.Producto(ProductoId),
    Cantidad INT NOT NULL CHECK (Cantidad > 0),
    PrecioUnit DECIMAL(18,2) NOT NULL,
    DescuentoPct DECIMAL(5,2) NULL,
    Activo BIT NOT NULL DEFAULT 1
);

-- Índices para mejor performance
CREATE INDEX IX_Orden_Fecha ON Orden(Fecha);
CREATE INDEX IX_Orden_Cliente ON Orden(ClienteId);
CREATE INDEX IX_OrdenDetalle_Producto ON OrdenDetalle(ProductoId);
CREATE INDEX IX_OrdenDetalle_Orden ON OrdenDetalle(OrdenId);