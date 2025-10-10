from fastapi import FastAPI
from backend.api.routers import mysql_routes, supabase_routes, mongo_routes, neo4j_routes, dw_routes

app = FastAPI(title="Data Environment API")

# Register routes
app.include_router(mysql_routes.router, prefix="/mysql", tags=["MySQL"])
app.include_router(supabase_routes.router, prefix="/supabase", tags=["Supabase"])
app.include_router(mongo_routes.router, prefix="/mongo", tags=["MongoDB"])
app.include_router(neo4j_routes.router, prefix="/neo4j", tags=["Neo4j"])
app.include_router(dw_routes.router, prefix="/dw", tags=["DataWarehouse"])

@app.get("/")
def root():
    return {"status": "API is running"}
