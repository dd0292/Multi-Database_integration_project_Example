import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { ClienteFormModal } from "../../components/Sales/ClienteFormModal";
import { toast } from "sonner";
import { Plus, Network } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import api from "../../services/api";

const Neo4jClientes = () => {
  const [page] = useState(1);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const limit = 20;
  const queryClient = useQueryClient();
  const createMutation = useMutation({ mutationFn: async (data: any) => api.post("/neo4j/clientes", data), onSuccess: () => { queryClient.invalidateQueries({ queryKey: ["neo4j-clientes"] }); toast.success("Cliente creado"); setIsFormOpen(false); } });

  const { data, isLoading } = useQuery({
    queryKey: ["neo4j-clientes", page],
    queryFn: async () => {
      const response = await api.get<{ data: any[]; total: number }>(
        `/neo4j/clientes?page=${page}&limit=${limit}`
      );
      return response.data;
    },
  });

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neo4j">Neo4j Clientes</h1>
          <p className="text-muted-foreground mt-1">Manage client nodes in Neo4j graph database</p>
        </div>
        <Button className="bg-neo4j hover:bg-neo4j-dark" onClick={() => setIsFormOpen(true)}><Plus className="h-4 w-4 mr-2" />New Client</Button>
      </div>
      <ClienteFormModal open={isFormOpen} onOpenChange={setIsFormOpen} onSubmit={(data) => createMutation.mutate(data)} dbType="neo4j" generos={['M','F','Otro','Masculino','Femenino']} />

      <Card className="border-l-4 border-neo4j">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5" />
            Client Nodes
          </CardTitle>
          <CardDescription>{data?.total || 0} total clients</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading clients...</div>
          ) : data?.data && data.data.length > 0 ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {data.data.map((cliente: any) => (
                <Card key={cliente.id} className="p-4 hover:shadow-md transition-shadow">
                  <div className="flex items-start gap-3">
                    <Network className="h-10 w-10 text-neo4j" />
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg mb-1">{cliente.nombre}</h3>
                      {cliente.email && (
                        <p className="text-sm text-muted-foreground">{cliente.email}</p>
                      )}
                      <div className="mt-2 flex gap-2">
                        <span className="text-xs px-2 py-1 bg-neo4j-light text-neo4j-dark rounded font-mono">
                          {cliente.id}
                        </span>
                      </div>
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No clients found. Create your first client node!
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Neo4jClientes;
