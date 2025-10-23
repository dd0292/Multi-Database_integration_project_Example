export interface MySQLOrdenItem {
  producto_codigo_alt: string;
  cantidad: string;
  precio_unit: string;
}

export interface MySQLOrden {
  orden_id?: number;
  cliente_id: number;
  fecha: string;
  canal: "WEB" | "TIENDA" | "APP";
  moneda: "CRC" | "USD";
  total: string;
  items: MySQLOrdenItem[];
}