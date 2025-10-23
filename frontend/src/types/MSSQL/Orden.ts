export interface MSSQLOrdenItem {
  ProductoId: number;
  Cantidad: number;
  PrecioUnit: number;
  DescuentoPct?: number;
}

export interface MSSQLOrden {
  OrdenId?: number;
  ClienteId: number;
  Fecha: string;
  Canal: "WEB" | "TIENDA" | "APP";
  Moneda: "USD";
  Total: number;
  Items: MSSQLOrdenItem[];
}