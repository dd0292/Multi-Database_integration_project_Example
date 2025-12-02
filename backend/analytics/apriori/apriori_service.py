import json
import pandas as pd
from sqlalchemy import text

from api.config import settings
from api.database.mssql_connection import get_connection


def obtener_recomendaciones(productos: list[str], fuente: str):
    """
    Retorna recomendaciones con nombres de productos usando DimProducto.
    """

    engine = get_connection(settings.SQLSERVER_DB_DW)

    # ========= 1. Cargar reglas desde SQL Server =========
    query = text("""
        SELECT 
            Antecedente,
            Consecuente,
            Soporte,
            Confianza,
            Lift
        FROM dbo.ReglasAsociacion
        WHERE UPPER(Fuente) = UPPER(:fuente)
    """)

    rows = engine.execute(query, {"fuente": fuente}).fetchall()

    # ========= 2. Cargar catálogo de productos =========
    df_prod = pd.read_sql(
        "SELECT ProductoID, Nombre FROM dbo.DimProducto WHERE EsRegistroActual = 1",
        engine
    )

    mapa_nombres = dict(zip(df_prod["ProductoID"].astype(str), df_prod["Nombre"]))

    # ========= 3. Procesar reglas =========
    recomendaciones = []

    productos_str = set([str(p) for p in productos])

    for row in rows:
        antecedente_ids = set(json.loads(row.Antecedente))
        consecuente_ids = json.loads(row.Consecuente)

        # Condición Apriori
        if antecedente_ids.issubset(productos_str):

            # Convertir IDs -> nombres
            antecedente_nombres = [mapa_nombres.get(pid, f"Producto {pid}") for pid in antecedente_ids]
            consecuente_nombres = [mapa_nombres.get(pid, f"Producto {pid}") for pid in consecuente_ids]

            recomendaciones.append({
                "antecedente_ids": list(antecedente_ids),
                "consecuente_ids": consecuente_ids,
                "antecedente": antecedente_nombres,
                "consecuente": consecuente_nombres,
                "soporte": row.Soporte,
                "confianza": row.Confianza,
                "lift": row.Lift
            })

    # ========= 4. Ordenar =========
    recomendaciones.sort(key=lambda r: r["lift"], reverse=True)

    # Retornar top 3
    return recomendaciones[:3]
