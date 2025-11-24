CREATE TABLE dwh.ReglasAsociacion (
    ReglaID INT IDENTITY(1,1) PRIMARY KEY,
    Fuente NVARCHAR(20) NOT NULL,                -- 'MSSQL', 'MYSQL', 'MONGO', 'SUPABASE', 'NEO4J'
    Antecedente NVARCHAR(MAX) NOT NULL,          -- JSON array
    Consecuente NVARCHAR(MAX) NOT NULL,          -- JSON array
    Soporte FLOAT NOT NULL,
    Confianza FLOAT NOT NULL,
    Lift FLOAT NOT NULL,
    FechaGeneracion DATETIME2 DEFAULT SYSDATETIME()
);
