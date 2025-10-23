import type { OrdenFormData } from "../iOrden";

export interface MongoOrdenItem {
  producto_id: string;
  cantidad: number;
  precio_unit: number;
}

export interface MongoOrden {
  id: string;
  cliente_id: string;
  fecha: string;
  canal: "WEB" | "TIENDA" | "APP";
  moneda: "CRC" | "USD";
  total: number;
  items: MongoOrdenItem[];
  metadatos?: Record<string, unknown>;
}

export const ordenFormToPayload = (data: OrdenFormData) => ({
  cliente_id: data.cliente_id,
  fecha: data.fecha,
  canal: data.canal,
  moneda: data.moneda,
  total: data.total,
  items: data.items,
  metadatos: data.descripcion
});