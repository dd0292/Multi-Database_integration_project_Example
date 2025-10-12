import { useState } from "react";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { Plus, Network, Package } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import api from "../../services/api";
import { ProductoFormModal } from "../../components/Sales/ProductoFormModal";
import { toast } from "sonner";

const Neo4jProductos = () => {
  const [page] = useState(1);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const limit = 20;
  const queryClient = useQueryClient();

  const { data, isLoading, error } = useQuery({
    queryKey: ["neo4j-productos", page],
    queryFn: async () => {
      const response = await api.get<{ data: any[]; total: number }>(
        `/neo4j/productos?page=${page}&limit=${limit}`
      );
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      return api.post("/neo4j/productos", {
        codigo_mongo: data.codigo,
        nombre: data.nombre,
        categoria: data.categoria,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["neo4j-productos"] });
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
          <h1 className="text-3xl font-bold text-neo4j">Neo4j Productos</h1>
          <p className="text-muted-foreground mt-1">Manage product nodes in Neo4j graph database</p>
        </div>
        <Button className="bg-neo4j hover:bg-neo4j-dark" onClick={() => setIsFormOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Product
        </Button>
      </div>

      <ProductoFormModal
        open={isFormOpen}
        onOpenChange={setIsFormOpen}
        onSubmit={(data) => createMutation.mutate(data)}
        dbType="neo4j"
        extraInfo={true}
        tiposCategorias={["Codigo Alt", "Codigo Mongo"]}
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
