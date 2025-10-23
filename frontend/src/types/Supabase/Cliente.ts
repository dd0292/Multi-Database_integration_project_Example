export interface SupabaseCliente {
  id: string;
  nombre: string;
  email: string;
  genero: "Masculino" | "Femenino" | "Otro";
  pais: string;
  created: string;
}
