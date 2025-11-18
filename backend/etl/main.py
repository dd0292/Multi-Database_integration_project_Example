from etl.mysql_to_dw import run_mysql_etl
from etl.mongo_to_dw import run_mongo_etl

def run_all():
    print("Corriendo ETL MySQL…")
    run_mysql_etl()

    print("Corriendo ETL MongoDB…")
    run_mongo_etl()

    print("ETLs completados.")

if __name__ == "__main__":
    run_all()
