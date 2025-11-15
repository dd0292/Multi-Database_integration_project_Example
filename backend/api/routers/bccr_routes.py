from fastapi import APIRouter, Depends, Query, HTTPException
from typing import Optional
from api.config import settings
from ..services.bccr_service import bccr_service

router = APIRouter()

@router.get("/exchange-rates")
async def get_exchange_rates(
    email: str = Query(settings.BCCR_EMAIL, description="BCCR registered email (must be .cr domain)"),
    token: str = Query(settings.BCCR_TOKEN, description="BCCR API token"),
    fecha_inicio: Optional[str] = Query(None, description="Start date (dd/mm/yyyy)"),
    fecha_final: Optional[str] = Query(None, description="End date (dd/mm/yyyy)")
):
    """
    Smart exchange rates endpoint:
    - Single date: Returns compra/venta for that day
    - Date range: Returns historical compra/venta for each day in range
    """
    return bccr_service.get_exchange_rates(email, token, fecha_inicio, fecha_final)

@router.get("/health")
async def health_check():
    return {"status": "BCCR router is working"}

@router.get("/email-requirements")
async def get_email_requirements():
    return {
        "requirements": [
            "Must be a valid email with Costa Rican domain (.cr, .fi.cr, .go.cr, etc.)"
        ]
    }