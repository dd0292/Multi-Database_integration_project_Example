import logging
import pyodbc
import os
from datetime import datetime, timedelta
from decimal import Decimal
from dotenv import load_dotenv
from typing import List, Tuple
from api.services.bccr_service import bccr_service

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

def get_conn():
    """Get database connection"""
    return pyodbc.connect(
        f"DRIVER={os.getenv('SQLSERVER_DRIVER')};"
        f"SERVER={os.getenv('SQLSERVER_HOST')},{os.getenv('SQLSERVER_PORT')};"
        f"DATABASE={os.getenv('SQLSERVER_DB_DW')};"
        f"UID={os.getenv('SQLSERVER_USER')};"
        f"PWD={os.getenv('SQLSERVER_PASSWORD')};"
        "Encrypt=no;TrustServerCertificate=yes;"
    )

def obtener_datos_bccr(fecha_inicio: str, fecha_fin: str) -> List[Tuple]:
    """
    Get exchange rate data from BCCR service
    Returns: List of tuples (fecha, de_moneda, a_moneda, tasa, fuente)
    """
    try:
        # Get email and token from environment variables
        email = os.getenv('BCCR_EMAIL')
        token = os.getenv('BCCR_TOKEN')
        
        if not email or not token:
            logger.error("BCCR_EMAIL or BCCR_TOKEN not set in environment variables")
            return []
        
        # Convert dates from YYYY-MM-DD to DD/MM/YYYY format
        fecha_inicio_fmt = datetime.strptime(fecha_inicio, '%Y-%m-%d').strftime('%d/%m/%Y')
        fecha_fin_fmt = datetime.strptime(fecha_fin, '%Y-%m-%d').strftime('%d/%m/%Y')
        
        logger.info(f"Consultando BCCR: {fecha_inicio_fmt} a {fecha_fin_fmt}")
        
        # Use your existing BCCR service
        result = bccr_service.get_exchange_rates(
            email=email,
            token=token,
            fecha_inicio=fecha_inicio_fmt,
            fecha_final=fecha_fin_fmt
        )
        
        datos = []
        
        # Check if we got historical data
        if result.get('tipo') == 'datos_historicos':
            for dato in result.get('datos', []):
                try:
                    fecha_str = dato['fecha']
                    compra_rate = dato['compra']  # Buy rate (USD to CRC)
                    venta_rate = dato['venta']    # Sell rate (USD to CRC)
                    
                    # Convert string date to date object
                    fecha_date = datetime.strptime(fecha_str, '%Y-%m-%d').date()
                    
                    # For Tipo_Cambio table, you might want to store both buy and sell rates
                    # or decide which one to use. Here I'll store both as separate records.
                    
                    # Store buy rate (USD to CRC) - typically used for purchases
                    datos.append((
                        fecha_date,
                        'USD',          # From USD
                        'CRC',          # To CRC (buy rate)
                        Decimal(str(compra_rate)),
                        'BCCR_COMPRA'   # Source with type
                    ))
                    
                    # Store sell rate (USD to CRC) - typically used for sales
                    datos.append((
                        fecha_date,
                        'CRC',          # From CRC  
                        'USD',          # To USD (inverse of sell rate)
                        Decimal('1') / Decimal(str(venta_rate)),  # Inverse rate
                        'BCCR_VENTA'    # Source with type
                    ))
                    
                    logger.info(f"  - {fecha_date}: Compra ${compra_rate} CRC, Venta ${venta_rate} CRC")
                    
                except (KeyError, ValueError) as e:
                    logger.warning(f"Error processing data point: {dato} - {e}")
                    continue
        
        # Handle single day result (if date range is 1 day)
        elif result.get('tipo') == 'dato_unico':
            try:
                fecha_str = result['fecha']
                compra_rate = result['compra']
                venta_rate = result['venta']
                
                # Convert date from DD/MM/YYYY to date object
                fecha_date = datetime.strptime(fecha_str, '%d/%m/%Y').date()
                
                # Store buy rate
                datos.append((
                    fecha_date,
                    'USD',
                    'CRC',
                    Decimal(str(compra_rate)),
                    'BCCR_COMPRA'
                ))
                
                # Store sell rate inverse
                datos.append((
                    fecha_date,
                    'CRC',
                    'USD',
                    Decimal('1') / Decimal(str(venta_rate)),
                    'BCCR_VENTA'
                ))
                
                logger.info(f"  - {fecha_date}: Compra ${compra_rate} CRC, Venta ${venta_rate} CRC")
                
            except (KeyError, ValueError) as e:
                logger.error(f"Error processing single day data: {e}")
        
        return datos
        
    except Exception as e:
        logger.error(f"Error obteniendo datos BCCR: {e}")
        return []

def cargar_stg_tipo_cambio(datos: List[Tuple]) -> int:
    """
    Load data into stg.Tipo_Cambio table
    Returns: Number of records inserted
    """
    if not datos:
        logger.warning("No hay datos para cargar")
        return 0
    
    try:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Optional: Clear staging table first
        cursor.execute("TRUNCATE TABLE stg.Tipo_Cambio")
        logger.info("Tabla stg.Tipo_Cambio truncada")
        
        # Insert data
        insert_query = """
            INSERT INTO stg.Tipo_Cambio (Fecha, De, A, Tasa, Fuente)
            VALUES (?, ?, ?, ?, ?)
        """
        
        cursor.executemany(insert_query, datos)
        conn.commit()
        
        num_registros = len(datos)
        logger.info(f"Insertados {num_registros} registros en stg.Tipo_Cambio")
        
        cursor.close()
        conn.close()
        
        return num_registros
        
    except Exception as e:
        logger.error(f"Error cargando datos en stg.Tipo_Cambio: {e}")
        if 'conn' in locals():
            conn.close()
        return 0

def run_bccr_etl():
    """
    Main ETL function to load exchange rates into stg.Tipo_Cambio
    """
    logger.info("\n=== ETL BCCR → stg.Tipo_Cambio ===")
    
    # Calculate date range (last 3 years)
    fecha_fin = datetime.now().strftime('%Y-%m-%d')
    fecha_inicio = (datetime.now() - timedelta(days=3*365)).strftime('%Y-%m-%d')
    
    logger.info(f"Rango de fechas: {fecha_inicio} a {fecha_fin}")
    
    # Get data from BCCR
    datos = obtener_datos_bccr(fecha_inicio, fecha_fin)
    
    if datos:
        # Load data into staging table
        registros_insertados = cargar_stg_tipo_cambio(datos)
        
        logger.info(f"ETL completado. Total registros procesados: {registros_insertados}")
        return registros_insertados
    else:
        logger.error("No se obtuvieron datos del BCCR")
        return 0

def actualizar_datos_recientes(dias_historial: int = 1):
    """
    Update recent data (useful for incremental updates)
    """
    logger.info(f"\n=== Actualización incremental ({dias_historial} días) ===")
    
    fecha_fin = datetime.now().strftime('%Y-%m-%d')
    fecha_inicio = (datetime.now() - timedelta(days=dias_historial)).strftime('%Y-%m-%d')
    
    logger.info(f"Rango: {fecha_inicio} a {fecha_fin}")
    
    datos = obtener_datos_bccr(fecha_inicio, fecha_fin)
    
    if datos:
        # Instead of truncating, you might want to upsert
        conn = get_conn()
        cursor = conn.cursor()
        
        for dato in datos:
            fecha, de_moneda, a_moneda, tasa, fuente = dato
            
            # Check if record exists
            cursor.execute("""
                SELECT 1 FROM stg.Tipo_Cambio 
                WHERE Fecha = ? AND De = ? AND A = ? AND Fuente = ?
            """, (fecha, de_moneda, a_moneda, fuente))
            
            if cursor.fetchone():
                # Update existing
                cursor.execute("""
                    UPDATE stg.Tipo_Cambio 
                    SET Tasa = ?
                    WHERE Fecha = ? AND De = ? AND A = ? AND Fuente = ?
                """, (tasa, fecha, de_moneda, a_moneda, fuente))
            else:
                # Insert new
                cursor.execute("""
                    INSERT INTO stg.Tipo_Cambio (Fecha, De, A, Tasa, Fuente)
                    VALUES (?, ?, ?, ?, ?)
                """, (fecha, de_moneda, a_moneda, tasa, fuente))
        
        conn.commit()
        cursor.close()
        conn.close()
        
        logger.info(f"Actualizados/Insertados {len(datos)} registros")
        
        return len(datos)
    else:
        logger.warning("No hay datos nuevos para actualizar")
        return 0

if __name__ == "__main__":
    run_bccr_etl()