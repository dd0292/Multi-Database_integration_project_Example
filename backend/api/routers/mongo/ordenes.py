from fastapi import APIRouter, HTTPException, status, Depends, Query
from datetime import datetime
from typing import Optional
from api.services.mongo.ordenes_service import OrdenService
from api.schemas.mongo import OrdenResponse
from api.dependencies import get_mongo_ordenes_service
from api.schemas.froms import OrdenFormData

router = APIRouter(prefix="/ordenes", tags=["mongo-ordenes"])

@router.post("/", response_model=OrdenResponse)
def create_orden(
    orden: OrdenFormData,
    service: OrdenService = Depends(get_mongo_ordenes_service)
):
    try:
        return service.create_orden(orden)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating orden: {str(e)}"
        )

@router.get("/", response_model=dict)
def get_ordenes(
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    service: OrdenService = Depends(get_mongo_ordenes_service)
):
    try:
        return service.get_ordenes(page=page, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching ordenes: {str(e)}"
        )

@router.get("/cliente/{cliente_id}", response_model=dict)
def get_ordenes_by_cliente(
    cliente_id: str,
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    service: OrdenService = Depends(get_mongo_ordenes_service)
):
    try:
        return service.get_ordenes_by_cliente(cliente_id=cliente_id, page=page, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching ordenes by cliente: {str(e)}"
        )

@router.get("/fecha", response_model=dict)
def get_ordenes_by_fecha(
    fecha_inicio: datetime = Query(..., description="Start date (YYYY-MM-DD)"),
    fecha_fin: datetime = Query(..., description="End date (YYYY-MM-DD)"),
    page: int = Query(1, ge=1, description="Page number"),
    limit: int = Query(20, ge=1, le=100, description="Items per page"),
    service: OrdenService = Depends(get_mongo_ordenes_service)
):
    try:
        return service.get_ordenes_by_fecha(
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
            page=page,
            limit=limit
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching ordenes by date range: {str(e)}"
        )

@router.get("/stats", response_model=dict)
def get_ordenes_stats(
    service: OrdenService = Depends(get_mongo_ordenes_service)
):
    try:
        return service.get_ordenes_stats()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching ordenes statistics: {str(e)}"
        )

@router.get("/{orden_id}", response_model=OrdenResponse)
def get_orden(
    orden_id: str,
    service: OrdenService = Depends(get_mongo_ordenes_service)
):
    orden = service.get_orden_by_id(orden_id)
    if not orden:
        raise HTTPException(status_code=404, detail="Orden not found")
    return orden

@router.patch("/{orden_id}", response_model=OrdenResponse)
def update_orden(
    orden_id: str,
    orden_update: OrdenFormData,
    service: OrdenService = Depends(get_mongo_ordenes_service)
):
    updated_orden = service.update_orden(orden_id, orden_update)
    if not updated_orden:
        raise HTTPException(status_code=404, detail="Orden not found")
    return updated_orden

@router.delete("/{orden_id}")
def delete_orden(
    orden_id: str,
    service: OrdenService = Depends(get_mongo_ordenes_service)
):
    if not service.delete_orden(orden_id):
        raise HTTPException(status_code=404, detail="Orden not found")
    return {"message": "Orden deleted successfully"}