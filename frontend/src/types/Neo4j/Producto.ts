import type { ProductoFormData } from "../iProducto";

export interface Neo4jProducto {
  id: string;
  nombre: string;
  categoria: string;
  sku: string;
  codigo_alt: string;
  codigo_mongo: string;
}

export const productoFormToPayload = (data: ProductoFormData) => ({
  nombre: data.nombre,
  codigo: data.codigo,
  categoria: data.categoria,
  equivalencias: data.categoriasAdicionales
});