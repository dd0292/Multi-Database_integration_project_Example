USE Ventas_Transactional;
GO

DECLARE 
    @i INT = 1,
    @SKU NVARCHAR(40),
    @Nombre NVARCHAR(150),
    @Categoria NVARCHAR(80);

-- Lista de categorías
DECLARE @Categorias TABLE (Valor NVARCHAR(80));
INSERT INTO @Categorias VALUES
('Bebidas'),
('Snacks'),
('Lácteos'),
('Carnes'),
('Frutas'),
('Verduras'),
('Aseo Personal'),
('Panadería'),
('Tecnología'),
('Hogar'),
('Abarrotes'),
('Cuidado del Hogar');

-- Lista de nombres base
DECLARE @Nombres TABLE (Valor NVARCHAR(150));
INSERT INTO @Nombres VALUES
('Producto MSSQL Premium'),
('Producto  MSSQL Especial'),
('Producto MSSQL  Estándar'),
('Producto MSSQL  Orgánico'),
('Producto MSSQL Económico'),
('Producto MSSQL Clásico'),
('Producto MSSQL Importado'),
('Producto MSSQL Nacional'),
('Producto MSSQL Popular'),
('Producto MSSQL Gourmet');

WHILE @i <= 200
BEGIN
    -- SKU único
    SET @SKU = CONCAT('SKU', FORMAT(@i, '0000'));

    -- Nombre aleatorio + número
    DECLARE @base NVARCHAR(150);
    SELECT TOP 1 @base = Valor FROM @Nombres ORDER BY NEWID();
    SET @Nombre = CONCAT(@base, ' ', @i);

    -- Categoría aleatoria pero repetible
    SELECT TOP 1 @Categoria = Valor FROM @Categorias ORDER BY NEWID();

    INSERT INTO dbo.Producto (SKU, Nombre, Categoria, Activo)
    VALUES (@SKU, @Nombre, @Categoria, 1);

    SET @i = @i + 1;
END;
GO