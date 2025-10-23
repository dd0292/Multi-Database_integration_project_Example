export interface MSSQLCliente {
  id: number;
  Nombre: string;
  Email: string;
  Genero: "Masculino" | "Femenino" | "Otro";
  Pais: string;
  creado: string;
}