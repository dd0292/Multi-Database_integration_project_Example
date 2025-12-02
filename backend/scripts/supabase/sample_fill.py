"""
Script to populate Supabase tables with sample data using existing services.
Run from the `backend` folder:
    python scripts/supabase/sample_fill.py

Creates ~90 clients, ~70 products, ~200 orders (1-5 items each).
Uses existing `api.services.supabase` service classes and `api.schemas.supabase` models.
"""

from dotenv import load_dotenv
load_dotenv()

import random
import time
from datetime import datetime, timedelta

import sys
import os
import unicodedata
import re

# Ensure the backend package root is on sys.path so `import api` works
# regardless of the current working directory when running this script.
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)

from api.database.supabase_connection import get_supabase_client
from api.services.supabase.clientes_service import ClienteService
from api.services.supabase.productos_service import ProductoService
from api.services.supabase.ordenes_service import OrdenService
from api.schemas.supabase import (
    ClienteFormData,
    ProductoFormData,
    OrdenFormData,
    OrdenItemData,
)

# Configuration
NUM_CLIENTS = 90
NUM_PRODUCTS = 70
NUM_ORDERS = 200
MIN_ITEMS_PER_ORDER = 1
MAX_ITEMS_PER_ORDER = 5

SLEEP_BETWEEN_REQUESTS = 0.01  # small delay to avoid rate limits

FIRST_NAMES = [
    "Ana", "Carlos", "María", "Juan", "Luisa", "Jorge", "Daniel", "Sofía", "Diego", "Lucía",
    "Andrés", "Paula", "Fernando", "Isabella", "Miguel", "Camila", "Pablo", "Valentina", "Ricardo", "Laura"
]
LAST_NAMES = [
    "García", "Rodríguez", "Martínez", "López", "Sánchez", "Pérez", "Gómez", "Hernández", "Ruiz", "Flores",
    "Vargas", "Castillo", "Ramírez", "Ortiz", "Rojas", "Morales", " Díaz", "Torres", "Silva", "Núñez"
]
COUNTRIES =  ["CR", "GT", "SV", "HN", "NI", "PA", "BZ", "US"]
GENDERS = ["M", "F"]
CATEGORIES = ["Electrónica", "Hogar", "Ropa", "Alimentos", "Juguetes", "Herramientas", "Libros"]
CANALS = ["WEB", "APP", "PARTNER"]
CURRENCIES = ["USD", "CRC"]

random.seed(42)


def unique_names(count):
    seen = set()
    names = []
    i = 0
    while len(names) < count:
        fn = random.choice(FIRST_NAMES)
        ln = random.choice(LAST_NAMES).strip()
        name = f"{fn} {ln}"
        # ensure uniqueness by appending a small number when collision
        if name in seen:
            i += 1
            candidate = f"{name} {i}"
        else:
            candidate = name
        if candidate not in seen:
            seen.add(candidate)
            names.append(candidate)
    return names


def make_email(name, idx):
    # Normalize and remove diacritics, collapse whitespace, and produce a safe local part
    # 1) strip and collapse whitespace
    n = " ".join(name.split()).strip()
    # 2) remove accents/diacritics
    n_ascii = unicodedata.normalize('NFKD', n).encode('ascii', 'ignore').decode('ascii')
    # 3) replace any non-alphanumeric with dot
    local = re.sub(r"[^A-Za-z0-9]+", '.', n_ascii.lower())
    # 4) collapse multiple dots
    local = re.sub(r"\.{2,}", '.', local)
    # 5) trim leading/trailing dots
    local = local.strip('.')
    domains = ["example.com", "mail.com", "test.org"]
    return f"{local}.{idx}@{random.choice(domains)}"


def main():
    client = get_supabase_client()

    cliente_service = ClienteService(client)
    producto_service = ProductoService(client)
    orden_service = OrdenService(client)

    print("Generating clients...")
    names = unique_names(NUM_CLIENTS)
    created_clients = []
    for i, name in enumerate(names, start=1):
        email = make_email(name, i)
        genero = random.choice(GENDERS)
        pais = random.choice(COUNTRIES)
        payload = ClienteFormData(nombre=name, email=email, genero=genero, pais=pais)
        try:
            created = cliente_service.create_cliente(payload)
            created_clients.append(created)
        except Exception as e:
            print("Failed to create client:", e)
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    print(f"Created {len(created_clients)} clients")

    print("Generating products...")
    created_products = []
    for i in range(1, NUM_PRODUCTS + 1):
        nombre = f"Producto {i:03d}"
        categoria = random.choice(CATEGORIES)
        sku = f"SKU{i:05d}"
        payload = ProductoFormData(nombre=nombre, categoria=categoria, sku=sku)
        try:
            created = producto_service.create_producto(payload)
            created_products.append(created)
        except Exception as e:
            print("Failed to create product:", e)
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    print(f"Created {len(created_products)} products")

    if not created_clients or not created_products:
        print("Need at least one client and one product to create orders. Exiting.")
        return

    print("Generating orders...")
    created_orders = []

    product_ids = [p["producto_id"] for p in created_products if "producto_id" in p]
    client_ids = [c["cliente_id"] for c in created_clients if "cliente_id" in c]

    for oi in range(1, NUM_ORDERS + 1):
        cliente_id = random.choice(client_ids)
        canal = random.choice(CANALS)
        moneda = random.choice(CURRENCIES)
        # pick a date within last 90 days
        fecha = datetime.utcnow() - timedelta(days=random.randint(0, 90), hours=random.randint(0,23), minutes=random.randint(0,59))
        # items
        n_items = random.randint(MIN_ITEMS_PER_ORDER, MAX_ITEMS_PER_ORDER)
        items = []
        total = 0.0
        for _ in range(n_items):
            producto_id = random.choice(product_ids)
            cantidad = random.randint(1, 5)
            precio_unit = round(random.uniform(5.0, 200.0), 2)
            total += precio_unit * cantidad
            items.append(OrdenItemData(producto_id=producto_id, cantidad=cantidad, precio_unit=precio_unit))

        total = round(total, 2)
        orden_payload = OrdenFormData(
            cliente_id=cliente_id,
            canal=canal,
            moneda=moneda,
            total=total,
            fecha=fecha.isoformat(),
            items=items
        )
        try:
            created = orden_service.create_orden(orden_payload)
            created_orders.append(created)
        except Exception as e:
            print(f"Failed to create order {oi}:", e)
        time.sleep(SLEEP_BETWEEN_REQUESTS)

    print(f"Created {len(created_orders)} orders")


if __name__ == '__main__':
    main()
