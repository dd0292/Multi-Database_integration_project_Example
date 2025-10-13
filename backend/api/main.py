from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
#from api.routers import mysql_routes, supabase_routes, mongo_routes, neo4j_routes, dw_routes
from api.routers import mongo_routes
import os
from dotenv import load_dotenv


load_dotenv()
BACKEND_HOST = os.getenv("BACKEND_HOST", "0.0.0.0")
BACKEND_PORT = int(os.getenv("BACKEND_PORT", "8000"))
FRONTEND_PORT = os.getenv("FRONTEND_PORT", "5173")
FRONTEND_HOST = os.getenv("FRONTEND_URI", "localhost")



app = FastAPI(title="Data Environment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://{FRONTEND_HOST}:{FRONTEND_PORT}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Register routes
#app.include_router(mysql_routes.router, prefix="/mysql", tags=["MySQL"])
#app.include_router(supabase_routes.router, prefix="/supabase", tags=["Supabase"])
app.include_router(mongo_routes.router, prefix="/mongo", tags=["MongoDB"])
#app.include_router(neo4j_routes.router, prefix="/neo4j", tags=["Neo4j"])
#app.include_router(dw_routes.router, prefix="/dw", tags=["DataWarehouse"])

@app.get("/")
def root():
    return {"status": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=BACKEND_HOST,
        port=BACKEND_PORT,
        reload=True
    )