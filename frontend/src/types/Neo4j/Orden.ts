import type { Neo4jCliente, Neo4jProducto } from "../databases";

export interface Neo4jOrdenItem {
  producto: Neo4jProducto;
  cantidad: number;
  precio_unit: number;
}

export interface Neo4jOrden {
  cliente: Neo4jCliente;
  orden: {
    id: string;
    fecha: string;
    canal: "WEB" | "TIENDA" | "APP";
    moneda: "CRC" | "USD";
    total: number;
  };
  items: Neo4jOrdenItem[];
}