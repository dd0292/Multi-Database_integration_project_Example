import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Package } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import api from "../../services/api";
import type { SupabaseProducto } from "../../types/databases";
import { ProductoFormModal } from "../../components/Sales/ProductoFormModal";
import { toast } from "sonner";

const SupabaseProductos = () => {
  const [page] = useState(1);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const limit = 20;
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["supabase-productos", page],
    queryFn: async () => {
      const response = await api.get<{ data: SupabaseProducto[]; total: number }>(
        `/supabase/productos?page=${page}&limit=${limit}`
      );
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      return api.post("/supabase/productos", {
        Nombre: data.nombre,
        Categoria: data.categoria,
        SKU: data.codigo,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["supabase-productos"] });
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
          <h1 className="text-3xl font-bold text-supabase">Supabase Productos</h1>
          <p className="text-muted-foreground mt-1">Manage product catalog in Supabase</p>
        </div>
        <Button className="bg-supabase hover:bg-supabase-dark" onClick={() => setIsFormOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Product
        </Button>
      </div>

      <ProductoFormModal
        open={isFormOpen}
        onOpenChange={setIsFormOpen}
        onSubmit={(data) => createMutation.mutate(data)}
        dbType="supabase"
        codeNeeded={false}
      />

      <Card className="border-l-4 border-supabase">
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
                <Card key={producto.id} className="p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start justify-between mb-2">
                    <Package className="h-8 w-8 text-supabase" />
                    <span className="text-xs px-2 py-1 bg-supabase-light text-supabase-dark rounded font-mono">
                      {producto.sku}
                    </span>
                  </div>
                  <h3 className="font-semibold text-lg mb-1">{producto.nombre}</h3>
                  <p className="text-sm text-muted-foreground">{producto.categoria}</p>
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

export default SupabaseProductos;
