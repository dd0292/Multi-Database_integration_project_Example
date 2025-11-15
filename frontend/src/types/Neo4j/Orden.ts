import type { OrdenFormData } from "../iOrden";

export interface Neo4jOrdenItem {
  producto_id: string;
  cantidad: number;
  precio_unit: number;
}

export interface Neo4jOrden {
  id: string;
  cliente_id: string;
  fecha: string;
  canal: "WEB" | "TIENDA" | "APP";
  moneda: "CRC" | "USD";
  total: number;
  items: Neo4jOrdenItem[];
}

export const ordenFormToPayload = (data: OrdenFormData) => ({
  cliente_id: data.cliente_id,
  fecha: data.fecha,
  canal: data.canal,
  moneda: data.moneda,
  total: data.total,
  items: data.items
});