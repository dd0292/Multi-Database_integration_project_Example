export interface SupabaseOrdenItem {
  producto_id: string;
  cantidad: number;
  precio_unit: number;
}

export interface SupabaseOrden {
  id?: string;
  cliente_id: string;
  fecha: string;
  canal: "WEB" | "TIENDA" | "APP";
  moneda: "CRC" | "USD";
  total: number;
  items: SupabaseOrdenItem[];
}