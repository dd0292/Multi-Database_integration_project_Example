from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime
from typing import Optional
from api.services.mongo.productos_service import ProductoService
from api.schemas.mongo import ProductoResponse
from api.dependencies import get_mongo_productos_service
from api.schemas.froms import ProductoFormData

router = APIRouter(prefix="/productos", tags=["mongo-productos"])

@router.post("/", response_model=ProductoResponse)
def create_producto(
    producto: ProductoFormData,
    service: ProductoService = Depends(get_mongo_productos_service)
):
    try:
        return service.create_producto(producto)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating producto: {str(e)}"
        )

@router.get("/", response_model=dict)
def get_productos(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    service: ProductoService = Depends(get_mongo_productos_service)
):
    try:
        return service.get_productos(page=page, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching productos: {str(e)}"
        )

@router.get("/search", response_model=dict)
def search_productos(
    query: str = Query(..., description="Search term for name or category"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    service: ProductoService = Depends(get_mongo_productos_service)
):
    try:
        return service.search_productos(query=query, page=page, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error searching productos: {str(e)}"
        )

@router.get("/categoria/{categoria}", response_model=dict)
def get_productos_by_categoria(
    categoria: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    service: ProductoService = Depends(get_mongo_productos_service)
):
    try:
        return service.get_productos_by_categoria(categoria=categoria, page=page, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching productos by category: {str(e)}"
        )

@router.get("/{producto_id}", response_model=ProductoResponse)
def get_producto(
    producto_id: str,
    service: ProductoService = Depends(get_mongo_productos_service)
):
    producto = service.get_producto_by_id(producto_id)
    if not producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    return producto

@router.patch("/{producto_id}", response_model=ProductoResponse)
def update_producto(
    producto_id: str,
    producto_update: ProductoFormData,
    service: ProductoService = Depends(get_mongo_productos_service)
):
    updated_producto = service.update_producto(producto_id, producto_update)
    if not updated_producto:
        raise HTTPException(status_code=404, detail="Producto not found")
    return updated_producto

@router.delete("/{producto_id}")
def delete_producto(
    producto_id: str,
    service: ProductoService = Depends(get_mongo_productos_service)
):
    if not service.delete_producto(producto_id):
        raise HTTPException(status_code=404, detail="Producto not found")
    return {"message": "Producto deleted successfully"}