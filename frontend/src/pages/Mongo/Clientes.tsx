import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { ClienteFormModal, type ClienteFormData } from "../../components/Sales/ClienteFormModal";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { MongoCliente } from "../../types/databases";
import { Button } from "../../components/ui/button";
import api from "../../services/api";
import { Plus } from "lucide-react";
import { AxiosError } from "axios";
import { useState } from "react";
import { toast } from "sonner";

const MongoClientes = () => {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const queryClient = useQueryClient();
  const [page] = useState(1);
  const limit = 20;

  const { data, isLoading, error } = useQuery({
    queryKey: ["mongo-clientes", page],
    queryFn: async () => {
      const response = await api.get<{ data: MongoCliente[]; total: number }>(
        `/mongo/clientes?page=${page}&limit=${limit}`
      );
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: ClienteFormData) => {
      const response = await api.post("/mongo/clientes", {
        nombre: data.nombre,
        email: data.email,
        genero: data.genero,
        pais: data.pais,
        creado: new Date().toISOString(),
      });
      console.log(data);
      return response.data;
    },
    onSuccess: (data) => {
      queryClient.invalidateQueries({ queryKey: ["mongo-clientes"] });
      toast.success("Cliente creado exitosamente");
      setIsFormOpen(false);
      console.log("Created cliente:", data);
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      const errorMessage = error.response?.data?.detail || "Error al crear cliente";
      toast.error(errorMessage);
    },
  });

  if (error) {
    toast.error("Error loading clients");
  }
  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-mongo">MongoDB Clientes</h1>
          <p className="text-muted-foreground mt-1">Manage client records in MongoDB</p>
        </div>
        <Button className="bg-mongo hover:bg-mongo-dark" onClick={() => setIsFormOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Client
        </Button>
      </div>

      <ClienteFormModal
        open={isFormOpen}
        onOpenChange={setIsFormOpen}
        onSubmit={(data) => createMutation.mutate(data)}
        dbType="mongo"
        generos={["Masculino", "Femenino", "Otro"]} 
        extraInfo={true}      
      />

      <Card className="border-l-4 border-mongo">
        <CardHeader>
          <CardTitle>Client List</CardTitle>
          <CardDescription>
            {data?.total || 0} total clients
          </CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading clients...</div>
          ) : data?.data && data.data.length > 0 ? (
            <div className="space-y-4">
              {data.data.map((cliente) => (
                <Card key={cliente._id} className="p-4">
                  <div className="flex items-start justify-between">
                    <div>
                      <h3 className="font-semibold text-lg">{cliente.nombre}</h3>
                      <p className="text-sm text-muted-foreground">{cliente.email}</p>
                      <div className="mt-2 flex gap-2">
                        <span className="text-xs px-2 py-1 bg-muted rounded">{cliente.genero}</span>
                        <span className="text-xs px-2 py-1 bg-muted rounded">{cliente.pais}</span>
                      </div>
                    </div>
                    <div className="text-sm text-muted-foreground">
                      {new Date(cliente.creado).toLocaleDateString()}
                    </div>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No clients found. Create your first client!
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default MongoClientes;
