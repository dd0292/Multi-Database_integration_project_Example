export interface MySQLCliente {
  id?: number;
  nombre: string;
  correo: string;
  genero: "M" | "F" | "X";
  pais: string;
  created_at: string; // YYYY-MM-DD
}
