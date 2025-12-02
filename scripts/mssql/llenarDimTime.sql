DECLARE @StartDate DATE = '2026-01-01';
DECLARE @EndDate   DATE = '2026-12-31';

;WITH Dates AS (
    SELECT @StartDate AS Fecha
    UNION ALL
    SELECT DATEADD(DAY, 1, Fecha)
    FROM Dates
    WHERE Fecha < @EndDate
)
INSERT INTO DimTiempo (
    TiempoID,
    Fecha,
    Anio,
    Semestre,
    Trimestre,
    Mes,
    NombreMes,
    Dia,
    DiaSemana,
    NombreDiaSemana,
    EsFinDeSemana,
    MesAnio
)
SELECT
    CONVERT(INT, FORMAT(Fecha, 'yyyyMMdd')) AS TiempoID,
    Fecha,
    YEAR(Fecha) AS Anio,
    CASE WHEN MONTH(Fecha) <= 6 THEN 1 ELSE 2 END AS Semestre,
    CASE 
        WHEN MONTH(Fecha) BETWEEN 1 AND 3 THEN 1
        WHEN MONTH(Fecha) BETWEEN 4 AND 6 THEN 2
        WHEN MONTH(Fecha) BETWEEN 7 AND 9 THEN 3
        ELSE 4
    END AS Trimestre,
    MONTH(Fecha) AS Mes,
    DATENAME(MONTH, Fecha) AS NombreMes,
    DAY(Fecha) AS Dia,
    DATEPART(WEEKDAY, Fecha) AS DiaSemana,
    DATENAME(WEEKDAY, Fecha) AS NombreDiaSemana,
    CASE WHEN DATENAME(WEEKDAY, Fecha) IN ('Saturday','Sunday') THEN 1 ELSE 0 END AS EsFinDeSemana,
    FORMAT(Fecha, 'yyyy-MM') AS MesAnio
FROM Dates
OPTION (MAXRECURSION 1000);



