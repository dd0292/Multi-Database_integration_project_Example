
export interface SupabaseOrdenItem {
  producto_id: string;
  cantidad: number;
  precio_unit: number;
}

export interface SupabaseOrden {
  orden_id?: string;
  cliente_id: string;
  fecha: string;
  canal: "WEB" | "APP" | "PARTNER";
  moneda: "CRC" | "USD";
  total: number;
  items?: SupabaseOrdenItem[];
}