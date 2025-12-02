import { Plus, Network, ShoppingCart, Edit, Trash2 } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import { ordenFormToPayload, type Neo4jOrden } from "../../types/Neo4j/Orden";
import { useCrudOperations } from "../../hooks/useCrudOperations";
import type { OrdenFormData } from "../../types/iOrden";
import { useFormHandler } from "../../hooks/useFormHandler";
import { toast } from "sonner";
import { OrdenFormModal } from "../../components/Sales/OrdenFormModal";

const Neo4jOrdenes = () => {

  const {
    data,
    isLoading,
    error,
    page,
    setPage,
    totalPages,
    createMutation,
    updateMutation,
    deleteMutation,
  } = useCrudOperations<Neo4jOrden, OrdenFormData>({
    endpoint: "/neo4j/ordenes",
    queryKey: "neo4j-ordenes",
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
  } = useFormHandler<Neo4jOrden>();

  const onFormSubmit = (data: OrdenFormData) => {
    handleFormSubmit(
      data,
      editingClient,
      createMutation.mutate,
      (id, data) => updateMutation.mutate({ id, data })
    );
  };
  const onDelete = (cliente: Neo4jOrden) => {
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
      case "WEB": return "bg-blue-100 text-blue-800";
      case "TIENDA": return "bg-green-100 text-green-800";
      case "APP": return "bg-purple-100 text-purple-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neo4j">Neo4j Órdenes</h1>
          <p className="text-muted-foreground mt-1">Manage order relationships in Neo4j graph</p>
        </div>
        <Button className="bg-neo4j hover:bg-neo4j-dark" onClick={() => handleFormOpenChange(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Order
        </Button>
      </div>

      <OrdenFormModal
        key={editingClient?.id ?? "new"} 
        open={isFormOpen}
        onOpenChange={handleFormOpenChange}
        onSubmit={onFormSubmit}
        dbType="neo4j"
        canales={["WEB", "TIENDA", "APP"]}
        monedas={["CRC", "USD"]}
        addRecomendations = {true}
        initialData={editingClient!}
      />

      <Card className="border-l-4 border-neo4j">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5" />
            Order Graph
          </CardTitle>
          <CardDescription>{data?.total || 0} total orders</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading orders...</div>
          ) : data?.data && data.data.length > 0 ? (
            <div className="space-y-4">
              {data.data.map((orden: any) => (
                <Card key={orden.id} className="p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <ShoppingCart className="h-5 w-5 text-neo4j" />
                        <h3 className="font-semibold text-lg">Order {orden.id}</h3>

                        <Badge className={getChannelColor(orden.canal)}>
                          {orden.canal}
                        </Badge>
                      </div>

                      <p className="text-sm text-muted-foreground">
                        {orden.fechan || "N/A"}
                      </p>
                    </div>

                    <div className="text-right">
                      <div className="text-2xl font-bold text-neo4j">
                        {formatCurrency(orden.total || 0, orden.moneda)}
                      </div>
                      <div className="text-xs text-muted-foreground">
                        {orden.moneda}
                      </div>
                    </div>
                  </div>

                  <div className="border-t pt-3 flex items-center gap-2 text-sm text-muted-foreground">
                    <Network className="h-4 w-4" />
                    <span>{orden.items.length} product relationships</span>
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
              No orders found. Create your first order relationship!
            </div>
          )}
        </CardContent>
        {data?.data && data.data.length > 0 && (
          <div className="border-t border-gray-200 dark:border-gray-700 pt-6 pb-4 px-6 bg-gray-50/50 dark:bg-gray-900/50 rounded-b-lg">
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
              <div className="flex items-center gap-2 order-2 sm:order-1">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                  className="min-w-[100px]"
                >
                  Previous
                </Button>
                
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage(page + 1)}
                  className="min-w-[100px]"
                >
                  Next
                </Button>
              </div>
              
              <div className="order-1 sm:order-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 px-3 py-1 rounded-md border shadow-sm">
                  Page {page} of {totalPages}
                </span>
              </div>
            </div>
          </div>
        )}

      </Card>
    </div>
  );
};

export default Neo4jOrdenes;
