import json
from sqlalchemy import text

from api.config import settings
from api.database.mssql_connection import get_engine


def obtener_recomendaciones(productos: list[str], fuente: str):
    """
    Retorna reglas de asociación relevantes según los productos escogidos,
    usando únicamente el sistema de conexión existente de SQL Server.
    
    productos: lista de ProductoID como STR (porque vienen del query del frontend)
    fuente: 'MSSQL' | 'MYSQL' | 'MONGO' | 'SUPABASE' | 'NEO4J'
    """

    engine = get_engine(settings.SQLSERVER_DB_DW)

    # 1. Obtener reglas de la fuente específica
    query = text("""
        SELECT 
            Antecedente,
            Consecuente,
            Soporte,
            Confianza,
            Lift
        FROM dwh.ReglasAsociacion
        WHERE Fuente = :fuente
    """)

    rows = engine.execute(query, {"fuente": fuente}).fetchall()

    recomendaciones = []

    # Convertir productos a string para comparación (como vienen en el JSON)
    productos_str = set([str(p) for p in productos])

    # 2. Procesar reglas
    for row in rows:
        antecedente = set(json.loads(row.Antecedente))  # ejemplo: ["12","55"]
        consecuente = json.loads(row.Consecuente)

        # Condición Apriori: antecedente ⊆ productos_seleccionados
        if antecedente.issubset(productos_str):
            recomendaciones.append({
                "antecedente": list(antecedente),
                "consecuente": consecuente,
                "soporte": row.Soporte,
                "confianza": row.Confianza,
                "lift": row.Lift
            })

    # 3. Ordenar por Lift (más relevante primero)
    recomendaciones.sort(key=lambda r: r["lift"], reverse=True)

    # Retornar top 10 (puedes ajustarlo)
    return recomendaciones[:10]
