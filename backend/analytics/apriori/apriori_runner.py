import json
import pandas as pd
from mlxtend.frequent_patterns import apriori, association_rules
from sqlalchemy import text

from api.config import settings
from api.database.mssql_connection import get_engine

MIN_SUPPORT = 0.02       # 2%
MIN_CONFIDENCE = 0.3      # 30%


def cargar_dataset(fuente: str):
    """
    Carga el dataset desde la vista del DW filtrando por fuente.
    """
    engine = get_engine(settings.SQLSERVER_DB_DW)

    query = text("""
        SELECT Transaccion, ProductoID, SourceSystem
        FROM dbo.vwAprioriDataset
        WHERE UPPER(SourceSystem) = UPPER(:fuente)
    """)

    df = pd.read_sql(query, engine, params={"fuente": fuente})
    return df


def generar_one_hot(df: pd.DataFrame):
    """
    Convierte transacciones → matriz one-hot (transaction x product).
    """
    basket = (
        df.groupby(["Transaccion", "ProductoID"])["ProductoID"]
          .count()
          .unstack()
          .fillna(0)
    )
    return basket.astype(bool)


def guardar_reglas(rules, fuente: str):
    engine = get_engine(settings.SQLSERVER_DB_DW)

    # Filter out invalid rules before saving
    valid_rules = rules[
        (rules['support'] > 0) & 
        (rules['confidence'] > 0) & 
        (rules['lift'].notna())
    ]
    
    if valid_rules.empty:
        print(f"[{fuente}] No valid rules to save.")
        return

    # 1. Eliminar reglas antiguas de esa misma fuente
    with engine.connect() as conn:
        conn.execute(text("DELETE FROM dbo.ReglasAsociacion WHERE UPPER(Fuente) = UPPER(:f)"), {"f": fuente})
        conn.commit()

    # 2. Preparar nuevas reglas
    df = pd.DataFrame({
        "Fuente": fuente,
        "Antecedente": rules["antecedents"].apply(lambda s: json.dumps(list(s))),
        "Consecuente": rules["consequents"].apply(lambda s: json.dumps(list(s))),
        "Soporte": rules["support"],
        "Confianza": rules["confidence"],
        "Lift": rules["lift"],
    })

    # 3. Insertar reglas nuevas
    df.to_sql(
        "ReglasAsociacion",
        engine,
        schema="dbo",
        if_exists="append",
        index=False
    )


def procesar_fuente(fuente: str):
    print(f"\n=== Ejecutando Apriori para fuente: {fuente} ===")

    df = cargar_dataset(fuente)

    if df.empty:
        print(f"[{fuente}] No existen datos suficientes para Apriori.")
        return

    # One-hot
    basket = generar_one_hot(df)

    # Conjuntos frecuentes
    itemsets = apriori(
        basket,
        min_support=MIN_SUPPORT,
        use_colnames=True
    )

    if itemsets.empty:
        print(f"[{fuente}] Sin itemsets frecuentes.")
        return

    # Reglas
    rules = association_rules(
        itemsets,
        metric="confidence",
        min_threshold=MIN_CONFIDENCE
    )

    if rules.empty:
        print(f"[{fuente}] Sin reglas generadas.")
        return

    guardar_reglas(rules, fuente)

    print(f"[{fuente}] Reglas guardadas exitosamente.")


def run_apriori():
    """
    Ejecuta Apriori para cada fuente posible dentro del DW.
    """
    fuentes = ["MONGODB", "SUPABASE", "NEO4J"]

    for f in fuentes:
        procesar_fuente(f)
