from datetime import datetime

def parse_mysql_date(date_str: str) -> datetime:
    if not date_str:
        raise ValueError("Fecha vacía")
    date_str = date_str.strip()
    for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%d"):
        try:
            return datetime.strptime(date_str, fmt)
        except ValueError:
            continue
    raise ValueError(f"Formato no soportado: {date_str}")
