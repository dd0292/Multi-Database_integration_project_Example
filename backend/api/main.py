from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from api.config import settings
from api.routers import mongo_routes, mssql_routes, dw_routes

from api.database.mssql_connection import init_engines, dispose_engines


@asynccontextmanager
async def lifespan(app):
    # startup
    init_engines(settings)
    try:
        yield
    finally:
        # shutdown
        dispose_engines()

app = FastAPI(
    title="Multi-Database API",
    description="API with some databases...",
    version="1.0.0",
    lifespan=lifespan
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[f"http://{settings.FRONTEND_HOST}:{settings.FRONTEND_PORT}"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(mongo_routes.router, prefix="/mongo", tags=["MongoDB"])
app.include_router(mssql_routes.router, prefix="/mssql", tags=["MSSQL (Transactional)"])
app.include_router(dw_routes.router, prefix="/dw", tags=["DataWarehouse"])

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