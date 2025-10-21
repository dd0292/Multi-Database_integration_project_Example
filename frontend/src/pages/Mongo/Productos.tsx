import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Package } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { ProductoFormModal } from "../../components/Sales/ProductoFormModal";
import { toast } from "sonner";
import api from "../../services/api";
import type { MongoProducto } from "../../types/databases";

const MongoProductos = () => {
  const [page] = useState(1);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const limit = 20;
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["mongo-productos", page],
    queryFn: async () => {
      const response = await api.get<{ data: MongoProducto[]; total: number }>(
        `/mongo/productos?page=${page}&limit=${limit}`
      );
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      return api.post("/mongo/productos", {
        codigo_mongo: data.codigo,
        nombre: data.nombre,
        categoria: data.categoria,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mongo-productos"] });
      toast.success("Producto creado exitosamente");
      setIsFormOpen(false);
    },
    onError: () => {
      toast.error("Error al crear producto");
    },
  });

  if (error) {
    toast.error("Error loading products");
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-mongo">MongoDB Productos</h1>
          <p className="text-muted-foreground mt-1">Manage product catalog in MongoDB</p>
        </div>
        <Button className="bg-mongo hover:bg-mongo-dark" onClick={() => setIsFormOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Product
        </Button>
      </div>

      <ProductoFormModal
        open={isFormOpen}
        onOpenChange={setIsFormOpen}
        onSubmit={(data) => createMutation.mutate(data)}
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
                <Card key={producto._id} className="p-4 hover:shadow-md transition-shadow">
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
