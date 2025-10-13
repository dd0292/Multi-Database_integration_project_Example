import os
import uvicorn
from dotenv import load_dotenv
load_dotenv()

if __name__ == "__main__":
    host = os.getenv("BACKEND_HOST", "0.0.0.0")
    port = int(os.getenv("BACKEND_PORT", "8000"))
    
    uvicorn.run(
        "api.main:app",
        host=host,
        port=port,
        reload=True
    )