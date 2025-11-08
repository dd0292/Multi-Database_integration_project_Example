import os
from dotenv import load_dotenv

load_dotenv()

class Settings:

    # Connection Fontend
    BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
    FRONTEND_PORT = os.getenv("FRONTEND_PORT", "5173")
    FRONTEND_HOST = os.getenv("FRONTEND_URI", "localhost")

    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB = os.getenv("MONGO_DB", "sales_mongo")
    
    # MySQL
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "sales_mysql")
    
    #MSSQL Server
    SQLSERVER_HOST = os.getenv( "SQLSERVER_HOST", "localhost")
    SQLSERVER_PORT = os.getenv( "SQLSERVER_PORT", "1433")
    SQLSERVER_DB = os.getenv("SQLSERVER_DB", "Ventas_DW")
    SQLSERVER_USER = os.getenv( "SQLSERVER_USER", "admin")
    SQLSERVER_PASSWORD = os.getenv( "SQLSERVER_PASSWORD", "")
    SQLSERVER_DRIVER = os.getenv( "SQLSERVER_DRIVER", "ODBC Driver 17 for SQL Server")



settings = Settings()