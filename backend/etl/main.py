import sys
import os
# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from analytics.apriori.apriori_runner import run_apriori

from etl.mysql_to_dw import run_mysql_etl
from etl.mongo_to_dw import run_mongo_etl
from etl.neo4j_to_dw import run_neo4j_etl
from etl.supabase_to_dw import run_supabase_etl
from etl.mssql_to_dw import run_mssql_etl
from etl.staging_to_dw import run_staging_to_dw
from etl.bccr_to_staging import actualizar_datos_recientes

def run_all():
    print(" Empezando procesos ETL")

    print("Cargando tipo de cambio del BCCR")
    actualizar_datos_recientes()
    
    print("Corriendo ETL MySQL…")
    run_mysql_etl()

    print("Corriendo ETL MongoDB…")
    run_mongo_etl()
    
    print("Corriendo ETL Neo4j…")
    run_neo4j_etl()

    print("Corriendo ETL Supabase…")
    run_supabase_etl()

    print("Corriendo ETL MS SQL Server…")
    run_mssql_etl()

    print("Corriendo ETL DW...")
    run_staging_to_dw()
    print("ETLs completados.")

    print("Ejecutando Apriori...")
    run_apriori()

    print("Proceso completo: ETL + Apriori terminados.")

if __name__ == "__main__":
    run_all()
