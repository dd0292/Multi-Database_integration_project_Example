// MongoDB Types
export interface MongoCliente {
  id: string;
  nombre: string;
  email: string;
  genero: "Masculino" | "Femenino" | "Otro";
  pais: string;
  preferencias?: Array<{
    categoria: string;
    texto: string;
  }>;
  creado: string;
}

export interface MongoProducto {
  _id?: string;
  codigo_mongo: string;
  nombre: string;
  categoria: string;
  equivalencias?: {
    sku?: string;
    codigo_alt?: string;
  };
}

export interface MongoOrdenItem {
  producto_id: string;
  cantidad: number;
  precio_unit: number;
}

export interface MongoOrden {
  _id?: string;
  cliente_id: string;
  fecha: string;
  canal: "WEB" | "TIENDA" | "APP";
  moneda: "CRC" | "USD";
  total?: number;
  items: MongoOrdenItem[];
  metadatos?: Record<string, unknown>;
}

// MS SQL Types
export interface MSSQLCliente {
  ClienteId?: number;
  Nombre: string;
  Email: string;
  Genero: "Masculino" | "Femenino" | "Otro";
  Pais: string;
}

export interface MSSQLProducto {
  ProductoId?: number;
  SKU: string;
  Nombre: string;
  Categoria: string;
}

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

// MySQL Types
export interface MySQLCliente {
  cliente_id?: number;
  nombre: string;
  email: string;
  genero: "Masculino" | "Femenino" | "Otro";
  pais: string;
}

export interface MySQLProducto {
  producto_id?: number;
  codigo_alt: string;
  nombre: string;
  categoria: string;
}

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

// Supabase Types
export interface SupabaseCliente {
  id?: string;
  nombre: string;
  email: string;
  genero: "Masculino" | "Femenino" | "Otro";
  pais: string;
  created_at?: string;
}

export interface SupabaseProducto {
  id?: string;
  sku: string;
  nombre: string;
  categoria: string;
}

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

// Neo4j Types
export interface Neo4jCliente {
  id: string;
  nombre: string;
  email?: string;
}

export interface Neo4jProducto {
  id: string;
  nombre: string;
  categoria?: string;
}

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

export type DatabaseType = "mongo" | "mssql" | "mysql" | "supabase" | "neo4j";
