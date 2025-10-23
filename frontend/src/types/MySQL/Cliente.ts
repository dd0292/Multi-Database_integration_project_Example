export interface MySQLCliente {
  id: number;
  nombre: string;
  email: string;
  genero: "Masculino" | "Femenino" | "Otro";
  pais: string;
}
