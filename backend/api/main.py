from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
#from api.routers import mysql_routes, supabase_routes, mongo_routes, neo4j_routes, dw_routes
from api.routers import mysql_routes
from api.routers import mongo_routes
from api.routers import supabase_routes
from api.routers import mongo_routes, neo4j_routes, bccr_routes
from api.config import settings


app = FastAPI(
    title="Multi-Database API",
    description="API with some databases...",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    # Use the frontend_origin helper so env can supply either FRONTEND_URI or host/port
    allow_origins=[settings.frontend_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(mysql_routes.router, prefix="/mysql", tags=["MySQL"])
app.include_router(supabase_routes.router, prefix="/supabase", tags=["Supabase"])
app.include_router(mongo_routes.router, prefix="/mongo", tags=["MongoDB"])
app.include_router(neo4j_routes.router, prefix="/neo4j", tags=["Neo4j"])
# app.include_router(dw_routes.router, prefix="/dw", tags=["DataWarehouse"])

app.include_router(bccr_routes.router, prefix="/bccr", tags=["BCCR Exchange Rates"])

@app.get("/")
def root():
    return {"status": "API is running"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=settings.BACKEND_HOST,
        port=settings.BACKEND_PORT,
        reload=True
    )