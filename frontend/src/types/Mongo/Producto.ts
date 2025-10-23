import type { ProductoFormData } from "../iProducto";

export interface MongoProducto {
  id: string;
  codigo_mongo: string;
  nombre: string;
  categoria: string;
  equivalencias?: {
    sku?: string;
    codigo_alt?: string;
  };
}

export const productoFormToPayload = (data: ProductoFormData) => ({
  nombre: data.nombre,
  codigo_mongo: data.codigo,
  categoria: data.categoria,
  equivalencias: data.categoriasAdicionales
});