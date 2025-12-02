import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, ShoppingCart, Trash2, Pencil, Eye } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { DataTable } from "../../components/common/DataTable";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "../../components/ui/dialog";
import api from "../../services/api";
import type { SupabaseOrden } from "../../types/Supabase/Orden";
import { OrdenFormModal } from "../../components/Sales/OrdenFormModal";
import { toast } from "sonner";

const SupabaseOrdenes = () => {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingOrden, setEditingOrden] = useState<SupabaseOrden | null>(null);
  const [detailsOrden, setDetailsOrden] = useState<SupabaseOrden | null>(null);
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

  const updateMutation = useMutation({
    mutationFn: async (data: any) => {
      const payload = {
        cliente_id: data.cliente_id,
        canal: data.canal,
        moneda: data.moneda,
        total: data.total,
      };
      return api.patch(`/supabase/ordenes/${data.orden_id}`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["supabase-ordenes"] });
      toast.success("Orden actualizada");
      setEditingOrden(null);
      setIsFormOpen(false);
    },
    onError: () => {
      toast.error("Error al actualizar orden");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (orden_id: string) => {
      await api.delete(`/supabase/ordenes/${orden_id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["supabase-ordenes"] });
      toast.success("Orden eliminada");
    },
    onError: (error: any) => {
      // Assume all 500s are FK constraint violations
      if (error.response?.status === 500) {
        toast.error(
          "Cannot delete: This order is referenced by other entities. Please delete those records first."
        );
        return;
      }
      toast.error("Cannot delete: This order is referenced by other entities. Please delete those records first.");
    },
  });

  const handleDelete = (orden: SupabaseOrden) => {
    if (window.confirm(`¿Eliminar orden #${orden.orden_id?.slice(0, 8)}? Esta acción es permanente.`)) {
      deleteMutation.mutate(orden.orden_id!);
    }
  };

  const { data, isLoading } = useQuery({
    queryKey: ["supabase-ordenes"],
    queryFn: async () => {
      const response = await api.get<{ data: SupabaseOrden[]; total: number }>(
        `/supabase/ordenes?page=1&limit=10000`
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
        <Button className="bg-supabase hover:bg-supabase-dark" onClick={() => {
          setEditingOrden(null);
          setIsFormOpen(true);
        }}>
          <Plus className="h-4 w-4 mr-2" />
          New Order
        </Button>
      </div>
  <OrdenFormModal 
    open={isFormOpen} 
    onOpenChange={(open) => {
      setIsFormOpen(open);
      if (!open) {
        setEditingOrden(null);
      }
    }}
    onSubmit={(data) => {
      if (editingOrden) {
        updateMutation.mutate({ ...data, orden_id: editingOrden.orden_id });
      } else {
        createMutation.mutate(data);
      }
    }}
    initialData={editingOrden || undefined}
    dbType="supabase" 
    monedas={["USD","CRC"]} 
    canales={["WEB","APP","PARTNER"]} 
    addRecomendations={true}
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
            <DataTable
              data={data.data}
              columns={[
                {
                  header: "Order ID",
                  accessor: (row: SupabaseOrden) => `#${row.orden_id?.slice(0, 8)}`,
                },
                {
                  header: "Channel",
                  accessor: (row: SupabaseOrden) => (
                    <Badge className={getChannelColor(row.canal)}>{row.canal}</Badge>
                  ),
                },
                {
                  header: "Date",
                  accessor: (row: SupabaseOrden) =>
                    row.fecha ? new Date(row.fecha).toLocaleString() : "—",
                },
                {
                  header: "Items",
                  accessor: (row: SupabaseOrden) => row.items?.length ?? 0,
                },
                {
                  header: "Total",
                  accessor: (row: SupabaseOrden) => (
                    <div>
                      <div className="font-bold text-supabase">
                        ${row.total.toFixed(2)}
                      </div>
                      <div className="text-xs text-muted-foreground">{row.moneda}</div>
                    </div>
                  ),
                },
                {
                  header: "Actions",
                  accessor: (row: SupabaseOrden) => (
                    <div className="flex gap-2">
                      <button
                        onClick={() => setDetailsOrden(row)}
                        className="text-muted-foreground hover:text-foreground transition-colors"
                        title="View Details"
                      >
                        <Eye className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => {
                          setEditingOrden(row);
                          setIsFormOpen(true);
                        }}
                        className="text-muted-foreground hover:text-foreground transition-colors"
                        title="Edit"
                      >
                        <Pencil className="h-4 w-4" />
                      </button>
                      <button
                        onClick={() => handleDelete(row)}
                        className="text-muted-foreground hover:text-destructive transition-colors"
                        title="Delete"
                      >
                        <Trash2 className="h-4 w-4" />
                      </button>
                    </div>
                  ),
                },
              ]}
            />
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No orders found. Create your first order!
            </div>
          )}
        </CardContent>
      </Card>

      {/* Order Details Dialog */}
      {detailsOrden && (
        <Dialog open={!!detailsOrden} onOpenChange={(open) => !open && setDetailsOrden(null)}>
          <DialogContent className="max-w-2xl max-h-[90vh] overflow-y-auto">
            <DialogHeader>
              <DialogTitle>Order Details - #{detailsOrden.orden_id?.slice(0, 8)}</DialogTitle>
              <DialogDescription>
                {detailsOrden.fecha && new Date(detailsOrden.fecha).toLocaleString()}
              </DialogDescription>
            </DialogHeader>

            <div className="space-y-4">
              {/* Order Header Info */}
              <Card>
                <CardContent className="pt-6">
                  <div className="grid grid-cols-2 gap-4">
                    <div>
                      <p className="text-xs text-muted-foreground">Channel</p>
                      <p className="font-semibold">
                        <Badge className={getChannelColor(detailsOrden.canal)}>
                          {detailsOrden.canal}
                        </Badge>
                      </p>
                    </div>
                    <div>
                      <p className="text-xs text-muted-foreground">Currency</p>
                      <p className="font-semibold">{detailsOrden.moneda}</p>
                    </div>
                  </div>
                </CardContent>
              </Card>

              {/* Order Items */}
              <Card>
                <CardHeader>
                  <CardTitle className="text-lg">Invoice Lines</CardTitle>
                </CardHeader>
                <CardContent>
                  {detailsOrden.items && detailsOrden.items.length > 0 ? (
                    <div className="space-y-2">
                      <div className="rounded-lg border overflow-hidden">
                        <table className="w-full text-sm">
                          <thead className="bg-muted">
                            <tr>
                              <th className="text-left p-3">Product ID</th>
                              <th className="text-right p-3">Qty</th>
                              <th className="text-right p-3">Unit Price</th>
                              <th className="text-right p-3">Subtotal</th>
                            </tr>
                          </thead>
                          <tbody>
                            {detailsOrden.items.map((item: any, idx: number) => (
                              <tr key={idx} className="border-t hover:bg-muted/50">
                                <td className="p-3">{item.producto_id?.slice(0, 8)}</td>
                                <td className="text-right p-3 font-medium">{item.cantidad}</td>
                                <td className="text-right p-3">
                                  ${item.precio_unit?.toFixed(2) || "0.00"}
                                </td>
                                <td className="text-right p-3 font-semibold">
                                  ${(item.cantidad * item.precio_unit)?.toFixed(2) || "0.00"}
                                </td>
                              </tr>
                            ))}
                          </tbody>
                        </table>
                      </div>

                      {/* Totals */}
                      <div className="flex justify-end gap-8 pt-4 border-t mt-4">
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Subtotal</p>
                          <p className="text-lg font-semibold">
                            ${(detailsOrden.items.reduce(
                              (sum: number, item: any) =>
                                sum + item.cantidad * item.precio_unit,
                              0
                            ))?.toFixed(2) || "0.00"}
                          </p>
                        </div>
                        <div>
                          <p className="text-xs text-muted-foreground mb-1">Grand Total</p>
                          <p className="text-lg font-bold text-supabase">
                            {detailsOrden.moneda} ${detailsOrden.total?.toFixed(2) || "0.00"}
                          </p>
                        </div>
                      </div>
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center py-4">No items in this order</p>
                  )}
                </CardContent>
              </Card>
            </div>
          </DialogContent>
        </Dialog>
      )}
    </div>
  );
};

export default SupabaseOrdenes;
