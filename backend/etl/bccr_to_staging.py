import requests
import pyodbc
import xml.etree.ElementTree as ET
from datetime import datetime, timedelta
from decimal import Decimal
import os
from dotenv import load_dotenv

load_dotenv()

def get_conn():
    return pyodbc.connect(
        f"DRIVER={os.getenv('SQLSERVER_DRIVER')};"
        f"SERVER={os.getenv('SQLSERVER_HOST')},{os.getenv('SQLSERVER_PORT')};"
        f"DATABASE={os.getenv('SQLSERVER_DB_DW')};"
        f"UID={os.getenv('SQLSERVER_USER')};"
        f"PWD={os.getenv('SQLSERVER_PASSWORD')};"
        "Encrypt=no;TrustServerCertificate=yes;"
    )

def obtener_tipo_cambio_bccr(fecha_inicio, fecha_fin):
    try:
        # El BCCR requiere formato dd/mm/yyyy
        fecha_inicio_fmt = datetime.strptime(fecha_inicio, '%Y-%m-%d').strftime('%d/%m/%Y')
        fecha_fin_fmt = datetime.strptime(fecha_fin, '%Y-%m-%d').strftime('%d/%m/%Y')
        
        params = {
            'tcIndicador': 317,  # 317 = Compra USD
            'tcFechaInicio': fecha_inicio_fmt,
            'tcFechaFinal': fecha_fin_fmt,
            'tcNombre': 'none',
            'tnSubNiveles': 'N'
        }
        
        url = os.getenv('BCCR_API_URL')
        
        print(f"Consultando BCCR: {fecha_inicio} a {fecha_fin}")
        print(f"URL: {url}")
        
        response = requests.get(url, params=params, timeout=30)
        response.raise_for_status()
        
        # Parsear respuesta XML
        root = ET.fromstring(response.content)
        datos = []
        
        for elem in root.findall('.//Datos_de_INGC011_CAT_INDICADORECONOMIC'):
            fecha = elem.find('DES_FECHA').text
            valor = elem.find('NUM_VALOR').text
            
            if fecha and valor:
                fecha_date = datetime.strptime(fecha.split('T')[0], '%Y-%m-%d').date()
                tasa = Decimal(valor)
                datos.append((fecha_date, 'CRC', 'USD', tasa, 'BCCR'))
                print(f"  - {fecha_date}: ₡{tasa} por $1")
        
        return datos
        
    except Exception as e:
        print(f"Error obteniendo datos BCCR: {e}")
        return []

def run_bccr_etl():
    """Llena stg.Tipo_Cambio con datos del BCCR"""
    print("\n=== ETL BCCR → stg.Tipo_Cambio ===")
    
    # Últimos 3 años 
    fecha_fin = datetime.now().strftime('%Y-%m-%d')
    fecha_inicio = (datetime.now() - timedelta(days=3*365)).strftime('%Y-%m-%d')
    
    print(f"Rango de fechas: {fecha_inicio} a {fecha_fin}")
    
    datos = obtener_tipo_cambio_bccr(fecha_inicio, fecha_fin)
    
    if datos:
        conn = get_conn()
        cursor = conn.cursor()
        
        # Limpiar tabla staging 
        cursor.execute("TRUNCATE TABLE stg.Tipo_Cambio")
        
        # Insertar datos
        cursor.executemany("""
            INSERT INTO stg.Tipo_Cambio (Fecha, De, A, Tasa, Fuente)
            VALUES (?, ?, ?, ?, ?)
        """, datos)
        
        conn.commit()
        cursor.close()
        conn.close()
        
        print(f"stg.Tipo_Cambio llenada con {len(datos)} registros")
    else:
        print("No se obtuvieron datos del BCCR")

if __name__ == "__main__":
    run_bccr_etl()