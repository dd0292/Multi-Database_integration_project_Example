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
    
    

settings = Settings()