import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Package } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { ProductoFormModal } from "../../components/Sales/ProductoFormModal";
import { toast } from "sonner";
import api from "../../services/api";
import type { MSSQLProducto } from "../../types/databases";

const MSSQLProductos = () => {
  const [page] = useState(1);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const limit = 20;
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["mssql-productos", page],
    queryFn: async () => {
      const response = await api.get<{ data: MSSQLProducto[]; total: number }>(
        `/mssql/productos?page=${page}&limit=${limit}`
      );
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      return api.post("/mssql/productos", {
        Nombre: data.nombre,
        Categoria: data.categoria,
        SKU: data.codigo,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mssql-productos"] });
      toast.success("Producto creado exitosamente");
      setIsFormOpen(false);
    },
    onError: () => {
      toast.error("Error al crear producto");
    },
  });

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-mssql">MS SQL Productos</h1>
          <p className="text-muted-foreground mt-1">Manage product catalog in MS SQL Server</p>
        </div>
        <Button className="bg-mssql hover:bg-mssql-dark" onClick={() => setIsFormOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Product
        </Button>
      </div>

      <ProductoFormModal
        open={isFormOpen}
        onOpenChange={setIsFormOpen}
        onSubmit={(data) => createMutation.mutate(data)}
        dbType="mssql"
      />

      <Card className="border-l-4 border-mssql">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Package className="h-5 w-5" />
            Product Catalog
          </CardTitle>
          <CardDescription>{data?.total || 0} total products</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading products...</div>
          ) : data?.data && data.data.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {data.data.map((producto) => (
                <Card key={producto.ProductoId} className="p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-2">
                    <Package className="h-8 w-8 text-mssql" />
                    <span className="text-xs px-2 py-1 bg-mssql-light text-mssql-dark rounded font-mono">
                      {producto.SKU}
                    </span>
                  </div>
                  <h3 className="font-semibold text-lg mb-1">{producto.Nombre}</h3>
                  <p className="text-sm text-muted-foreground">{producto.Categoria}</p>
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

export default MSSQLProductos;
