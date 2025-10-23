export interface OrdenItem {
  producto_id: string;
  cantidad: number;
  precio_unit: number;
  descuento_pct?: number;
}

export interface OrdenFormData {
  cliente_id: string;
  fecha: string;
  canal: string;
  moneda: string;
  items: OrdenItem[];
  total: number;
  descripcion?: string;
}

export interface OrdenFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: OrdenFormData) => void;
  dbType: "mongo" | "mssql" | "mysql" | "supabase" | "neo4j";
  monedas: Array<string>;
  canales: Array<string>;
  addDescuentoPct?: boolean;
  extraInfo?: boolean;
}
