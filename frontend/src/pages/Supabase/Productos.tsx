import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Package, Trash2, Pencil } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { DataTable } from "../../components/common/DataTable";
import api from "../../services/api";
import type { SupabaseProducto } from "../../types/Supabase/Producto";
import { ProductoFormModal } from "../../components/Sales/ProductoFormModal";
import { toast } from "sonner";

const SupabaseProductos = () => {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingProducto, setEditingProducto] = useState<SupabaseProducto | null>(null);
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["supabase-productos"],
    queryFn: async () => {
      const response = await api.get<{ data: SupabaseProducto[]; total: number }>(
        `/supabase/productos?page=1&limit=10000`
      );
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      // Map frontend form fields to Supabase table columns
      const payload = {
        nombre: data.nombre,
        categoria: data.categoria,
        sku: data.codigo ?? data.sku ?? null,
      };
      return api.post("/supabase/productos", payload);
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

  const updateMutation = useMutation({
    mutationFn: async (data: any) => {
      const payload = {
        nombre: data.nombre,
        categoria: data.categoria,
        sku: data.codigo ?? data.sku ?? null,
      };
      return api.patch(`/supabase/productos/${data.producto_id}`, payload);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["supabase-productos"] });
      toast.success("Producto actualizado exitosamente");
      setEditingProducto(null);
      setIsFormOpen(false);
    },
    onError: () => {
      toast.error("Error al actualizar producto");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (producto_id: string) => {
      await api.delete(`/supabase/productos/${producto_id}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["supabase-productos"] });
      toast.success("Producto eliminado exitosamente");
    },
    onError: (error: any) => {
      // Assume all 500s are FK constraint violations
      if (error.response?.status === 500) {
        toast.error(
          "Cannot delete: This product is referenced by other entities. Please delete those records first."
        );
        return;
      }
      toast.error("Cannot delete: This product is referenced by other entities. Please delete those records first.");
    },
  });

  const handleDelete = (producto: SupabaseProducto) => {
    if (window.confirm(`¿Eliminar "${producto.nombre}"? Esta acción es permanente.`)) {
      deleteMutation.mutate(producto.producto_id);
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-supabase">Supabase Productos</h1>
          <p className="text-muted-foreground mt-1">Manage product catalog in Supabase</p>
        </div>
        <Button className="bg-supabase hover:bg-supabase-dark" onClick={() => {
          setEditingProducto(null);
          setIsFormOpen(true);
        }}>
          <Plus className="h-4 w-4 mr-2" />
          New Product
        </Button>
      </div>

      <ProductoFormModal
        open={isFormOpen}
        onOpenChange={(open) => {
          setIsFormOpen(open);
          if (!open) {
            setEditingProducto(null);
          }
        }}
        onSubmit={(data) => {
          if (editingProducto) {
            updateMutation.mutate({ ...data, producto_id: editingProducto.producto_id });
          } else {
            createMutation.mutate(data);
          }
        }}
        initialData={editingProducto || undefined}
        dbType="supabase"
        codeNeeded={true}
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
            <DataTable
              data={data.data}
              columns={[
                {
                  header: "SKU",
                  accessor: (row: SupabaseProducto) => (
                    <span className="font-mono text-xs bg-muted px-2 py-1 rounded">
                      {row.sku || "—"}
                    </span>
                  ),
                },
                {
                  header: "Nombre",
                  accessor: (row: SupabaseProducto) => row.nombre,
                },
                {
                  header: "Categoría",
                  accessor: (row: SupabaseProducto) => row.categoria,
                },
                {
                  header: "Actions",
                  accessor: (row: SupabaseProducto) => (
                    <div className="flex gap-2">
                      <button
                        onClick={() => {
                          setEditingProducto(row);
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
              No products found. Create your first product!
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default SupabaseProductos;
