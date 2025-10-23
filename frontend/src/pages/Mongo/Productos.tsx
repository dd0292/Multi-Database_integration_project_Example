import { Plus, Package, Trash2, Edit } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { ProductoFormModal, } from "../../components/Sales/ProductoFormModal";
import { toast } from "sonner";
import { useCrudOperations } from "../../hooks/useCrudOperations";
import type { ProductoFormData } from "../../types/iProducto";
import { useFormHandler } from "../../hooks/useFormHandler";
import { productoFormToPayload, type MongoProducto } from "../../types/Mongo/Producto";

const MongoProductos = () => {

  const {
    data,
    isLoading,
    error,
    createMutation,
    updateMutation,
    deleteMutation,
  } = useCrudOperations<MongoProducto, ProductoFormData>({
    endpoint: "/mongo/productos",
    queryKey: "mongo-productos",
    formToPayload: productoFormToPayload,
    onSuccessMessage: "Cliente procesado exitosamente"
  });

  const {
    isFormOpen,
    editingItem: editingClient,
    handleEdit,
    handleDelete,
    handleFormOpenChange,
    handleFormSubmit,
  } = useFormHandler<MongoProducto>();

  const onFormSubmit = (data: ProductoFormData) => {
    handleFormSubmit(
      data,
      editingClient,
      createMutation.mutate,
      (id, data) => updateMutation.mutate({ id, data })
    );
  };
  const onDelete = (cliente: MongoProducto) => {
    handleDelete(cliente, deleteMutation.mutate);
  };

  if (error) {
    toast.error("Error loading clients");
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-mongo">MongoDB Productos</h1>
          <p className="text-muted-foreground mt-1">Manage product catalog in MongoDB</p>
        </div>
        <Button className="bg-mongo hover:bg-mongo-dark" onClick={() => handleFormOpenChange(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Product
        </Button>
      </div>

      <ProductoFormModal
        open={isFormOpen}
        onOpenChange={handleFormOpenChange}
        onSubmit={onFormSubmit}
        dbType="mongo"
        extraCodes={true}
        tiposCategorias={["SKU","Codigo Alt"]}
      />

      <Card className="border-l-4 border-mongo">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Product Catalog
          </CardTitle>
          <CardDescription>
            {data?.total || 0} total products
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading products...</div>
          ) : data?.data && data.data.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.data.map((producto) => (
                <Card key={producto.id} className="p-4 hover:shadow-md transition-shadow">
                  <div>
                    <div className="flex items-start justify-between mb-2">
                      <Package className="h-8 w-8 text-mongo" />
                      <span className="text-xs px-2 py-1 bg-mongo-light text-mongo-dark rounded font-mono">
                        {producto.codigo_mongo}
                      </span>
                    </div>
                    <h3 className="font-semibold text-lg mb-1">{producto.nombre}</h3>
                    <p className="text-sm text-muted-foreground mb-3">{producto.categoria}</p>
                    {producto.equivalencias && (
                      <div className="text-xs space-y-1">
                        {producto.equivalencias.sku && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">SKU:</span>
                            <span className="font-mono">{producto.equivalencias.sku}</span>
                          </div>
                        )}
                        {producto.equivalencias.codigo_alt && (
                          <div className="flex justify-between">
                            <span className="text-muted-foreground">Alt:</span>
                            <span className="font-mono">{producto.equivalencias.codigo_alt}</span>
                          </div>
                        )}
                      </div>
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
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No products found. Create your first product!
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default MongoProductos;
