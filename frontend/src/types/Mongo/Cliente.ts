import { convertPreferenciasToDict } from "../../utils/preferenciasConverter";
import type { ClienteFormData } from "../iCliente";

export interface MongoCliente {
  id: string;
  nombre: string;
  email: string;
  genero: "Masculino" | "Femenino" | "Otro";
  pais: string;
  preferencias?: Array<{
    categoria: string;
    texto: string;
  }>;
  creado: string;
}

export const clienteFormToPayload = (data: ClienteFormData) => ({
  nombre: data.nombre,
  email: data.email,
  genero: data.genero,
  pais: data.pais,
  preferencias: convertPreferenciasToDict(data.preferencias)
});