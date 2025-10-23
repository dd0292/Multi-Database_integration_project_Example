from fastapi import APIRouter, HTTPException, status, Depends
from api.services.mongo.clientes_service import ClienteService
from api.schemas.mongo import ClienteResponse
from api.dependencies import get_mongo_clientes_service
from api.schemas.froms import ClienteFormData

router = APIRouter(prefix="/clientes", tags=["mongo-clientes"])

@router.post("/", response_model=ClienteResponse)
def create_cliente(
    cliente: ClienteFormData,
    service: ClienteService = Depends(get_mongo_clientes_service)
):
    try:
        return service.create_cliente(cliente)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating cliente: {str(e)}"
        )

@router.get("/", response_model=dict)
def get_clientes(
    page: int = 1, 
    limit: int = 20,
    service: ClienteService = Depends(get_mongo_clientes_service)
):
    try:
        return service.get_clientes(page=page, limit=limit)
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error fetching clientes: {str(e)}"
        )

@router.get("/{cliente_id}", response_model=ClienteResponse)
def get_cliente(
    cliente_id: str,
    service: ClienteService = Depends(get_mongo_clientes_service)
):
    cliente = service.get_cliente_by_id(cliente_id)
    if not cliente:
        raise HTTPException(status_code=404, detail="Cliente not found")
    return cliente

@router.patch("/{cliente_id}", response_model=ClienteResponse)
def update_cliente(
    cliente_id: str,
    cliente_update: ClienteFormData,
    service: ClienteService = Depends(get_mongo_clientes_service)
):
    updated_cliente = service.update_cliente(cliente_id, cliente_update)
    if not updated_cliente:
        raise HTTPException(status_code=404, detail="Cliente not found")
    return updated_cliente

@router.delete("/{cliente_id}")
def delete_cliente(
    cliente_id: str,
    service: ClienteService = Depends(get_mongo_clientes_service)
):
    if not service.delete_cliente(cliente_id):
        raise HTTPException(status_code=404, detail="Cliente not found")
    return {"message": "Cliente deleted successfully"}