import type { ClienteFormData } from "../iCliente";

export interface Neo4jCliente {
  id: string;
  nombre: string;
  email: string;
  genero: "M" | "F" | "Masculino" | "Femenino" | "Otro";
  pais: string;
  creado: string;
}

export const clienteFormToPayload = (data: ClienteFormData) => ({
  nombre: data.nombre,
  email: data.email,
  genero: data.genero,
  pais: data.pais,
});