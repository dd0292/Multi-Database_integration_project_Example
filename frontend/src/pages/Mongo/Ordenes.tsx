import { Edit, Plus, ShoppingCart, Trash2 } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { OrdenFormModal } from "../../components/Sales/OrdenFormModal";
import { toast } from "sonner";
import { useCrudOperations } from "../../hooks/useCrudOperations";
import { useFormHandler } from "../../hooks/useFormHandler";
import type { OrdenFormData } from "../../types/iOrden";
import { ordenFormToPayload, type MongoOrden } from "../../types/Mongo/Orden";

const MongoOrdenes = () => {

  const {
    data,
    isLoading,
    error,
    createMutation,
    updateMutation,
    deleteMutation,
  } = useCrudOperations<MongoOrden, OrdenFormData>({
    endpoint: "/mongo/ordenes",
    queryKey: "mongo-ordenes",
    formToPayload: ordenFormToPayload,
    onSuccessMessage: "Orden procesado exitosamente"
  });

  const {
    isFormOpen,
    editingItem: editingClient,
    handleEdit,
    handleDelete,
    handleFormOpenChange,
    handleFormSubmit,
  } = useFormHandler<MongoOrden>();

  const onFormSubmit = (data: OrdenFormData) => {
    handleFormSubmit(
      data,
      editingClient,
      createMutation.mutate,
      (id, data) => updateMutation.mutate({ id, data })
    );
  };
  const onDelete = (cliente: MongoOrden) => {
    handleDelete(cliente, deleteMutation.mutate);
  };

  if (error) {
    toast.error("Error loading orders");
  }

  const formatCurrency = (amount: number, currency: string) => {
    return new Intl.NumberFormat("es-CR", {
      style: "currency",
      currency: currency === "CRC" ? "CRC" : "USD",
      minimumFractionDigits: 0,
    }).format(amount);
  };

  const getChannelColor = (canal: string) => {
    switch (canal) {
      case "WEB":
        return "bg-blue-100 text-blue-800";
      case "TIENDA":
        return "bg-green-100 text-green-800";
      case "APP":
        return "bg-purple-100 text-purple-800";
      default:
        return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-mongo">MongoDB Órdenes</h1>
          <p className="text-muted-foreground mt-1">Manage sales orders in MongoDB</p>
        </div>
        <Button className="bg-mongo hover:bg-mongo-dark" onClick={() => handleFormOpenChange(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Order
        </Button>
      </div>

      <OrdenFormModal
        key={editingClient?.id ?? "new"} 
        open={isFormOpen}
        onOpenChange={handleFormOpenChange}
        onSubmit={onFormSubmit}
        dbType="mongo"
        canales={["WEB", "TIENDA", "APP"]}
        monedas={["CRC"]}
        addDescuentoPct = {true}
        extraInfo = {true}
        initialData={editingClient!}
      />

      <Card className="border-l-4 border-mongo">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <ShoppingCart className="h-5 w-5" />
            Order History
          </CardTitle>
          <CardDescription>
            {data?.total || 0} total orders
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading orders...</div>
          ) : data?.data && data.data.length > 0 ? (
            <div className="space-y-4">
              {data.data.map((orden) => (
                <Card key={orden.id} className="p-5 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <h3 className="font-semibold text-lg">Order #{orden.id?.slice(-8)}</h3>
                        <Badge className={getChannelColor(orden.canal)}>
                          {orden.canal}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground">
                        {new Date(orden.fecha).toLocaleString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-mongo">
                        {formatCurrency(orden.total || 0, orden.moneda)}
                      </div>
                      <div className="text-xs text-muted-foreground">{orden.moneda}</div>
                    </div>
                  </div>
                  
                  <div className="border-t pt-3 mt-3">
                    <div className="text-sm font-medium mb-2">
                      Items ({orden.items.length})
                    </div>
                    <div className="space-y-1">
                      {orden.items.map((item, idx) => (
                        <div key={idx} className="flex justify-between text-sm">
                          <span className="text-muted-foreground">
                            {item.cantidad}x Product {item.producto_id.slice(-8)}
                          </span>
                          <span className="font-medium">
                            {formatCurrency(item.precio_unit * item.cantidad, orden.moneda)}
                          </span>
                        </div>
                      ))}
                    </div>
                  </div>
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(orden)}
                    disabled={updateMutation.isPending}
                  >
                  <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => onDelete(orden)}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
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

export default MongoOrdenes;
