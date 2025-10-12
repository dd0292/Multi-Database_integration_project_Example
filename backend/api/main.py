from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
#from api.routers import mysql_routes, supabase_routes, mongo_routes, neo4j_routes, dw_routes
from api.routers import mongo_routes
import os
from dotenv import load_dotenv


load_dotenv()

FRONTEND_PORT = os.getenv("FRONTEND_PORT")
FRONTEND_URI = os.getenv("FRONTEND_URI", "http://localhost:")


app = FastAPI(title="Data Environment API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"{FRONTEND_URI}{FRONTEND_PORT}"],
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
