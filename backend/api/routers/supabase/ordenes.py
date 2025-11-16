
from fastapi import APIRouter, HTTPException, status, Depends
from api.services.supabase.ordenes_service import OrdenService
from api.schemas.supabase import OrdenResponse, OrdenFormData
from api.dependencies import get_supabase_ordenes_service

router = APIRouter(prefix="/ordenes", tags=["supabase-ordenes"])

@router.post("/", response_model=OrdenResponse)
def create_orden(
	orden: OrdenFormData,
	service: OrdenService = Depends(get_supabase_ordenes_service)
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
	page: int = 1,
	limit: int = 20,
	service: OrdenService = Depends(get_supabase_ordenes_service)
):
	try:
		return service.get_ordenes(page=page, limit=limit)
	except Exception as e:
		raise HTTPException(
			status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
			detail=f"Error fetching ordenes: {str(e)}"
		)

@router.get("/{orden_id}", response_model=OrdenResponse)
def get_orden(
	orden_id: str,
	service: OrdenService = Depends(get_supabase_ordenes_service)
):
	orden = service.get_orden_by_id(orden_id)
	if not orden:
		raise HTTPException(status_code=404, detail="Orden not found")
	return orden

@router.patch("/{orden_id}", response_model=OrdenResponse)
def update_orden(
	orden_id: str,
	orden_update: OrdenFormData,
	service: OrdenService = Depends(get_supabase_ordenes_service)
):
	updated_orden = service.update_orden(orden_id, orden_update)
	if not updated_orden:
		raise HTTPException(status_code=404, detail="Orden not found")
	return updated_orden

@router.delete("/{orden_id}")
def delete_orden(
	orden_id: str,
	service: OrdenService = Depends(get_supabase_ordenes_service)
):
	if not service.delete_orden(orden_id):
		raise HTTPException(status_code=404, detail="Orden not found")
	return {"message": "Orden deleted successfully"}
