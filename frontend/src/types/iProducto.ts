export interface ProductoFormData {
  nombre: string;
  categoria: string;
  codigo: string;
  categoriasAdicionales?: Record<string, string>;
}

export interface ProductoFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: ProductoFormData) => void;
  dbType: "mongo" | "mssql" | "mysql" | "supabase" | "neo4j";
  initialData?: Partial<ProductoFormData>;
  codeNeeded?: boolean;
  extraCodes?: boolean;
  tiposCategorias?: string[];
}
