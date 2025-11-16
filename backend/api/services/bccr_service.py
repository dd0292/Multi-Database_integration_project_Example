import re
import logging
import requests
from api.config import settings
from fastapi import HTTPException
from xml.etree import ElementTree
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Union

logger = logging.getLogger(__name__)

class BCCRService:
    def __init__(self):
        self.bccr_url = 'https://gee.bccr.fi.cr/Indicadores/Suscripciones/WS/wsindicadoreseconomicos.asmx/ObtenerIndicadoresEconomicos'
    
    def _validate_email_format(self, email: str) -> bool:
        """
        BCCR email validation
        """
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(pattern, email):
            return False
        
        valid_domains = ['.cr', '.fi.cr', '.go.cr', '.ac.cr', '.ucr.ac.cr', '.com']
        return any(domain in email.lower() for domain in valid_domains)
    
    def _parse_bccr_response(self, xml_content: str, indicator_type: str) -> Union[float, List[Dict]]:
        """Parse BCCR XML response and extract value(s)"""
        try:
            root = ElementTree.fromstring(xml_content)
            
            # Check for errors
            error_node = root.find('.//Error')
            if error_node is not None and error_node.text:
                error_msg = error_node.text.strip()
                raise HTTPException(status_code=400, detail=f"BCCR API error: {error_msg}")
            
            # Find all indicator nodes
            indicator_nodes = root.findall('.//INGC011_CAT_INDICADORECONOMIC')
            
            if not indicator_nodes:
                raise HTTPException(status_code=404, detail=f"No data found for {indicator_type}")
            
            # If only one record, return single value
            if len(indicator_nodes) == 1:
                valor_node = indicator_nodes[0].find('NUM_VALOR')
                if valor_node is not None and valor_node.text:
                    return float(valor_node.text)
                else:
                    raise HTTPException(status_code=500, detail=f"No value found in response for {indicator_type}")
            
            # Multiple records - return historical data
            historical_data = []
            for node in indicator_nodes:
                fecha_node = node.find('DES_FECHA')
                valor_node = node.find('NUM_VALOR')
                
                if fecha_node is not None and fecha_node.text and valor_node is not None and valor_node.text:
                    # Extract date part only (remove timezone)
                    fecha_str = fecha_node.text.split('T')[0] if 'T' in fecha_node.text else fecha_node.text
                    
                    historical_data.append({
                        'fecha': fecha_str,
                        'valor': round(float(valor_node.text), 4)
                    })
            
            return historical_data
            
        except ElementTree.ParseError as e:
            logger.error(f"XML parsing error for {indicator_type}: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Invalid XML response from BCCR API")
    
    def _is_single_day_range(self, fecha_inicio: str, fecha_final: str) -> bool:
        """Check if the date range represents a single day"""
        try:
            # Parse dates in dd/mm/yyyy format
            start = datetime.strptime(fecha_inicio, '%d/%m/%Y')
            end = datetime.strptime(fecha_final, '%d/%m/%Y')
            return start == end
        except:
            return False
    
    def get_exchange_rates(self, email: str, token: str, fecha_inicio: Optional[str] = None, fecha_final: Optional[str] = None) -> Dict:
        """
        Smart exchange rates endpoint - returns single value for single day, historical data for range
        """
        try:
            if not self._validate_email_format(email):
                raise HTTPException(
                    status_code=400, 
                    detail="Invalid email format for BCCR API. Must be a valid email with Costa Rican domain"
                )
            
            today = datetime.now()
            default_date = f"{today.day:02d}/{today.month:02d}/{today.year}"
            
            # Set dates - if only one provided, use it for both
            if fecha_inicio and not fecha_final:
                fecha_final = fecha_inicio
            elif not fecha_inicio and fecha_final:
                fecha_inicio = fecha_final
            elif not fecha_inicio and not fecha_final:
                fecha_inicio = fecha_final = default_date
            
            fecha_inicio = fecha_inicio or default_date
            fecha_final = fecha_final or default_date
            
            is_single_day = self._is_single_day_range(fecha_inicio, fecha_final)
            
            # Configure payload based on request type
            subniveles = 'N' if is_single_day else 'S'
            
            base_payload = {
                'FechaInicio': fecha_inicio,
                'FechaFinal': fecha_final,
                'Nombre': 'N',
                'SubNiveles': subniveles,
                'CorreoElectronico': email,
                'Token': token,
            }
            
            # Get both buy and sell rates
            payload_compra = {**base_payload, 'Indicador': 317}
            payload_venta = {**base_payload, 'Indicador': 318}
            
            compra_response = requests.post(self.bccr_url, data=payload_compra, timeout=30)
            venta_response = requests.post(self.bccr_url, data=payload_venta, timeout=30)
            
            compra_response.raise_for_status()
            venta_response.raise_for_status()
            
            # Parse responses
            compra_data = self._parse_bccr_response(compra_response.text, "compra (317)")
            venta_data = self._parse_bccr_response(venta_response.text, "venta (318)")
            
            # Build response based on data type
            if is_single_day:
                # Single day - return simple structure
                return {
                    'tipo': 'dato_unico',
                    'fecha': fecha_inicio,
                    'compra': round(float(compra_data), 2),
                    'venta': round(float(venta_data), 2),
                    'diferencia': round(float(venta_data) - float(compra_data), 2),
                    'moneda': 'USD',
                    'unidad': 'CRC',
                    'fecha_consulta': datetime.now().isoformat()
                }
            else:
                # Date range - return historical data
                # Ensure both datasets have the same structure
                if isinstance(compra_data, list) and isinstance(venta_data, list):
                    # Combine data by date
                    combined_data = []
                    
                    # Create lookup dictionaries for easier merging
                    compra_dict = {item['fecha']: item['valor'] for item in compra_data}
                    venta_dict = {item['fecha']: item['valor'] for item in venta_data}
                    
                    # Get all unique dates
                    all_dates = sorted(set(list(compra_dict.keys()) + list(venta_dict.keys())))
                    
                    for fecha in all_dates:
                        compra_val = compra_dict.get(fecha)
                        venta_val = venta_dict.get(fecha)
                        
                        if compra_val is not None and venta_val is not None:
                            combined_data.append({
                                'fecha': fecha,
                                'compra': compra_val,
                                'venta': venta_val,
                                'diferencia': round(venta_val - compra_val, 4)
                            })
                    
                    return {
                        'tipo': 'datos_historicos',
                        'rango': {
                            'fecha_inicio': fecha_inicio,
                            'fecha_final': fecha_final
                        },
                        'total_dias': len(combined_data),
                        'datos': combined_data,
                        'moneda': 'USD',
                        'unidad': 'CRC',
                        'fecha_consulta': datetime.now().isoformat()
                    }
                else:
                    raise HTTPException(status_code=500, detail="Unexpected data format from BCCR API")
            
        except requests.exceptions.Timeout:
            raise HTTPException(status_code=504, detail="BCCR service timeout")
        except requests.exceptions.RequestException as e:
            raise HTTPException(status_code=503, detail=f"BCCR service unavailable: {str(e)}")
        except HTTPException:
            raise
        except Exception as e:
            logger.error(f"Unexpected error: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Error fetching exchange rates: {str(e)}")

# Create singleton instance
bccr_service = BCCRService()