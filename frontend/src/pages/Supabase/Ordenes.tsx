import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, ShoppingCart } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import api from "../../services/api";
import type { SupabaseOrden } from "../../types/Supabase/Orden";
import { OrdenFormModal } from "../../components/Sales/OrdenFormModal";
import { toast } from "sonner";

const SupabaseOrdenes = () => {
  const [page] = useState(1);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const limit = 20;
  const queryClient = useQueryClient();
  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      // Send order header and items to the backend so orden_detalle is populated
      const payload: any = {
        cliente_id: data.cliente_id,
        canal: data.canal,
        moneda: data.moneda,
        total: data.total,
        items: data.items || [],
      } as const;
      if (data.fecha) payload.fecha = data.fecha;
      return api.post("/supabase/ordenes", payload);
    },
    onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["supabase-ordenes"] }); toast.success("Orden creada"); setIsFormOpen(false); },
  });

  const { data, isLoading } = useQuery({
    queryKey: ["supabase-ordenes", page],
    queryFn: async () => {
      const response = await api.get<{ data: SupabaseOrden[]; total: number }>(
        `/supabase/ordenes?page=${page}&limit=${limit}`
      );
      return response.data;
    },
  });

  const getChannelColor = (canal: string) => {
    switch (canal) {
      case "WEB": return "bg-blue-100 text-blue-800";
      case "APP": return "bg-purple-100 text-purple-800";
      case "PARTNER": return "bg-green-100 text-green-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-supabase">Supabase Órdenes</h1>
          <p className="text-muted-foreground mt-1">Manage sales orders in Supabase</p>
        </div>
        <Button className="bg-supabase hover:bg-supabase-dark" onClick={() => setIsFormOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Order
        </Button>
      </div>
  <OrdenFormModal 
    open={isFormOpen} 
    onOpenChange={setIsFormOpen} 
    onSubmit={(data) => createMutation.mutate(data)} 
    dbType="supabase" 
    monedas={["USD","CRC"]} 
    canales={["WEB","APP","PARTNER"]}
    addRecomendations = {true}
  />

      <Card className="border-l-4 border-supabase">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShoppingCart className="h-5 w-5" />
            Order History
          </CardTitle>
          <CardDescription>{data?.total || 0} total orders</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading orders...</div>
          ) : data?.data && data.data.length > 0 ? (
            <div className="space-y-4">
              {data.data.map((orden) => (
                <Card key={orden.orden_id} className="p-5">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold text-lg">Order #{orden.orden_id?.slice(0, 8)}</h3>
                        <Badge className={getChannelColor(orden.canal)}>{orden.canal}</Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {orden.fecha ? new Date(orden.fecha).toLocaleString() : ""} • {orden.items?.length ?? 0} items
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-supabase">
                        ${orden.total.toFixed(2)}
                      </div>
                      <div className="text-xs text-muted-foreground">{orden.moneda}</div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No orders found. Create your first order!
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default SupabaseOrdenes;
