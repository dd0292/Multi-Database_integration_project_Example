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
    page,
    setPage,
    totalPages,
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
          codigo: editingClient.sku,
          categoriasAdicionales: {
            codigo_alt: editingClient.codigo_alt,
            codigo_mongo: editingClient.codigo_mongo
          }
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

export default Neo4jProductos;
