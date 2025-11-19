import os
from dotenv import load_dotenv

load_dotenv()

class Settings:

    # Connection Fontend
    BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
    BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))

    # Frontend origin configuration
    # Support either a full FRONTEND_URI (e.g. http://localhost:5173) or
    # separate FRONTEND_HOST and FRONTEND_PORT variables.
    FRONTEND_URI = os.getenv("FRONTEND_URI") or os.getenv("VITE_API_FRONTEND_URI")
    FRONTEND_HOST = os.getenv("FRONTEND_HOST", "localhost")
    FRONTEND_PORT = os.getenv("FRONTEND_PORT", "5173")

    @property
    def frontend_origin(self) -> str:
        """Return the allowed frontend origin for CORS.

        If FRONTEND_URI is provided, return it directly. Otherwise build
        http://{FRONTEND_HOST}:{FRONTEND_PORT}.
        """
        if self.FRONTEND_URI:
            return self.FRONTEND_URI
        return f"http://{self.FRONTEND_HOST}:{self.FRONTEND_PORT}"

    # MongoDB
    MONGO_URI = os.getenv("MONGO_URI")
    MONGO_DB = os.getenv("MONGO_DB", "sales_mongo")
    
    # MySQL
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = int(os.getenv("MYSQL_PORT", 3306))
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "")
    MYSQL_DB = os.getenv("MYSQL_DB", "sales_mysql")

    # Supabase
    SUPABASE_URL = os.getenv("SUPABASE_URL")
    SUPABASE_KEY = os.getenv("SUPABASE_KEY")
    
    # Neo4j
    NEO4J_URI = os.getenv("NEO4J_URI", "neo4j+s")
    NEO4J_USERNAME = os.getenv("NEO4J_USERNAME", "neo4j")
    NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
    NEO4J_DATABASE = os.getenv("NEO4J_DATABASE", "neo4j")
    AURA_INSTANCEID = os.getenv("AURA_INSTANCEID", "")
    AURA_INSTANCENAME = os.getenv("AURA_INSTANCENAME", "")

    # BCCR API
    BCCR_API_URL = os.getenv("BCCR_API_URL", "https://gee.bccr.fi.cr/Indicadores/Suscripciones/WS/wsindicadoreseconomicos.asmx/ObtenerIndicadoresEconomicos")
    BCCR_EMAIL = os.getenv("BCCR_EMAIL", "")
    BCCR_TOKEN = os.getenv("BCCR_TOKEN", "")
    
    # MSSQL Server (general connection details)
    SQLSERVER_HOST = os.getenv("SQLSERVER_HOST", "localhost")
    SQLSERVER_PORT = os.getenv("SQLSERVER_PORT", "1433")
    SQLSERVER_USER = os.getenv("SQLSERVER_USER", "sa")
    SQLSERVER_PASSWORD = os.getenv("SQLSERVER_PASSWORD", "")
    SQLSERVER_DRIVER = os.getenv("SQLSERVER_DRIVER", "ODBC Driver 17 for SQL Server")

    # MSSQL DB names (two databases)
    SQLSERVER_DB_DW = os.getenv("SQLSERVER_DB_DW", "Ventas_DW")

    SQLSERVER_DB_TRANSAC = os.getenv("SQLSERVER_DB_TRANSAC", "Ventas_Transactional")

settings = Settings()