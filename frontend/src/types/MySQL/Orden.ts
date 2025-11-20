export interface MySQLOrden {
  id?: number;
  cliente_id: number;
  fecha: string; // YYYY-MM-DD HH:MM:SS
  canal: string;
  moneda: "CRC" | "USD";
  total: string;  // VARCHAR en MySQL
}



