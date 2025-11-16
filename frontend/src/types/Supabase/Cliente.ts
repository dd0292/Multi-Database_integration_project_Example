export interface SupabaseCliente {
  cliente_id: string;
  nombre: string;
  email: string;
  genero: "M" | "F";
  pais: string;
  fecha_registro: string;
}