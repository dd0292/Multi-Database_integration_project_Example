from etl.mysql_to_dw import run_mysql_etl
from etl.mongo_to_dw import run_mongo_etl
from etl.neo4j_to_dw import run_neo4j_etl
from etl.supabase_to_dw import run_supabase_etl
from etl.mssql_to_dw import run_mssql_etl
from etl.staging_to_dw import run_staging_to_dw
from etl.bccr_to_staging import run_bccr_etl

def run_all():
    print(" Empezando procesos ETL")

    print("Cargando tipo de cambio del BCCR")
    run_bccr_etl()
    
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

if __name__ == "__main__":
    run_all()
