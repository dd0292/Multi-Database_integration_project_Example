import { Plus, Network, Package, Edit, Trash2 } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { ProductoFormModal } from "../../components/Sales/ProductoFormModal";
import { toast } from "sonner";
import { productoFormToPayload, type Neo4jProducto } from "../../types/Neo4j/Producto";
import { useCrudOperations } from "../../hooks/useCrudOperations";
import type { ProductoFormData } from "../../types/iProducto";
import { useFormHandler } from "../../hooks/useFormHandler";

const Neo4jProductos = () => {

  const {
    data,
    isLoading,
    error,
    createMutation,
    updateMutation,
    deleteMutation,
  } = useCrudOperations<Neo4jProducto, ProductoFormData>({
    endpoint: "/neo4j/productos",
    queryKey: "neo4j-productos",
    formToPayload: productoFormToPayload,
    onSuccessMessage: "Producto procesado exitosamente"
  });

  const {
    isFormOpen,
    editingItem: editingClient,
    handleEdit,
    handleDelete,
    handleFormOpenChange,
    handleFormSubmit,
  } = useFormHandler<Neo4jProducto>();

  const onFormSubmit = (data: ProductoFormData) => {
    handleFormSubmit(
      data,
      editingClient,
      createMutation.mutate,
      (id, data) => updateMutation.mutate({ id, data })
    );
  };
  const onDelete = (cliente: Neo4jProducto) => {
    handleDelete(cliente, deleteMutation.mutate);
  };

  if (error) {
    toast.error("Error loading clients");
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neo4j">Neo4j Productos</h1>
          <p className="text-muted-foreground mt-1">Manage product nodes in Neo4j graph database</p>
        </div>
        <Button className="bg-neo4j hover:bg-neo4j-dark" onClick={() => handleFormOpenChange(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Product
        </Button>
      </div>

      <ProductoFormModal
        key={editingClient?.id ?? "new"} 
        open={isFormOpen}
        onOpenChange={handleFormOpenChange}
        onSubmit={onFormSubmit}
        dbType="neo4j"
        extraCodes={true}
        tiposCategorias={["codigo_alt","codigo_mongo"]}
        initialData={editingClient ? {
          nombre: editingClient.nombre,
          categoria: editingClient.categoria,
          codigo: editingClient.sku
        } : undefined}
      />

      <Card className="border-l-4 border-neo4j">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5" />
            Product Nodes
          </CardTitle>
          <CardDescription>{data?.total || 0} total products</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading products...</div>
          ) : data?.data && data.data.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.data.map((producto: any) => (
                <Card key={producto.id} className="p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-2">
                    <Package className="h-8 w-8 text-neo4j" />
                    <span className="text-xs px-2 py-1 bg-neo4j-light text-neo4j-dark rounded font-mono">
                      {producto.id}
                    </span>
                  </div>
                  <h3 className="font-semibold text-lg mb-1">{producto.nombre}</h3>
                  {producto.categoria && (
                    <p className="text-sm text-muted-foreground">{producto.categoria}</p>
                  )}
                  <Button
                    variant="outline"
                    size="sm"
                    onClick={() => handleEdit(producto)}
                    disabled={updateMutation.isPending}
                  >
                    <Edit className="h-4 w-4" />
                  </Button>
                  <Button
                    variant="destructive"
                    size="sm"
                    onClick={() => onDelete(producto)}
                    disabled={deleteMutation.isPending}
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No products found. Create your first product node!
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Neo4jProductos;
