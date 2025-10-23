export interface ClienteFormData {
  nombre: string;
  email: string;
  genero: string;
  pais: string;
  preferencias?: Array<{
    categoria: string;
    texto: string;
  }>;
}

export interface ClienteFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: ClienteFormData) => void;
  dbType: "mongo" | "mssql" | "mysql" | "supabase" | "neo4j";
  initialData?: Partial<ClienteFormData>;
  generos: Array<string>;
  addPreferencias?: boolean;
}