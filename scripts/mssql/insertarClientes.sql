USE Ventas_Transactional;
GO

DECLARE 
    @i INT = 1,
    @Nombre NVARCHAR(120),
    @Email NVARCHAR(150),
    @Genero NVARCHAR(12),
    @Pais NVARCHAR(10),
    @FechaRegistro DATE;

-- Arrays simulados (tabla temporal en memoria)
DECLARE @Paises TABLE (Valor NVARCHAR(5));
INSERT INTO @Paises VALUES ('CR'),('GT'),('SV'),('HN'),('NI'),('PA'),('BZ'),('US');

DECLARE @Generos TABLE (Valor NVARCHAR(12));
INSERT INTO @Generos VALUES ('Masculino'), ('Femenino');

WHILE @i <= 850
BEGIN
    -- Nombre base tipo ejemplo "Cliente 1"
    SET @Nombre = CONCAT('Cliente MSSQL ', @i);

    -- Email único
    SET @Email = CONCAT('cliente', @i, '@mail.mssql');

    -- Género aleatorio
    SELECT TOP 1 @Genero = Valor FROM @Generos ORDER BY NEWID();

    -- País aleatorio
    SELECT TOP 1 @Pais = Valor FROM @Paises ORDER BY NEWID();

    -- Fecha aleatoria entre 2024-01-01 y 2025-12-31
    SET @FechaRegistro = DATEADD(
        DAY,
        ABS(CHECKSUM(NEWID())) % DATEDIFF(DAY, '2024-01-01', '2025-06-01'),
        '2024-01-01'
    );

    INSERT INTO dbo.Cliente (Nombre, Email, Genero, Pais, FechaRegistro, Activo)
    VALUES (@Nombre, @Email, @Genero, @Pais, @FechaRegistro, 1);

    SET @i = @i + 1;
END;
GO