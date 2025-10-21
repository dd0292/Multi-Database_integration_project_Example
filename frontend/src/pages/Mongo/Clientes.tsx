import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { ClienteFormModal, type ClienteFormData } from "../../components/Sales/ClienteFormModal";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import type { MongoCliente } from "../../types/databases";
import { Button } from "../../components/ui/button";
import { convertPreferenciasToDict } from "../../utils/preferenciasConverter";
import { Plus, Trash2, Edit } from "lucide-react";
import api from "../../services/api";
import { AxiosError } from "axios";
import { useState } from "react";
import { toast } from "sonner";

const MongoClientes = () => {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingClient, setEditingClient] = useState<MongoCliente | null>(null);
  const queryClient = useQueryClient();
  const [page] = useState(1);
  const limit = 20;

  // ---------------------------------------------------------------------------------
  // GET
  // ---------------------------------------------------------------------------------

  const { data, isLoading, error } = useQuery({
    queryKey: ["mongo-clientes", page],
    queryFn: async () => {
      const response = await api.get<{ data: MongoCliente[]; total: number }>(
        `/mongo/clientes?page=${page}&limit=${limit}`
      );
      console.log(response)
      return response.data;
    },
  });

  // ---------------------------------------------------------------------------------
  // POST
  // ---------------------------------------------------------------------------------

  const createMutation = useMutation({
    mutationFn: async (data: ClienteFormData) => {  
    const preferenciasDict = convertPreferenciasToDict(data.preferencias);
    
    const response = await api.post("/mongo/clientes", {
      nombre: data.nombre,
      email: data.email,
      genero: data.genero,
      pais: data.pais,
      creado: new Date().toISOString(),
      preferencias: preferenciasDict
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mongo-clientes"] });
      toast.success("Cliente creado exitosamente");
      setIsFormOpen(false);
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      const errorMessage = error.response?.data?.detail || "Error al crear cliente";
      toast.error(errorMessage);
    },
  });

  // ---------------------------------------------------------------------------------
  // PATCH
  // ---------------------------------------------------------------------------------

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: ClienteFormData }) => {

    const preferenciasDict = convertPreferenciasToDict(data.preferencias);

      const response = await api.patch(`/mongo/clientes/${id}`, {
        nombre: data.nombre,
        email: data.email,
        genero: data.genero,
        pais: data.pais,
        preferencias: preferenciasDict,
      });
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mongo-clientes"] });
      toast.success("Cliente actualizado exitosamente");
      setIsFormOpen(false);
      setEditingClient(null);
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      const errorMessage = error.response?.data?.detail || "Error al actualizar cliente";
      toast.error(errorMessage);
    },
  });

  // ---------------------------------------------------------------------------------
  // DELETE
  // ---------------------------------------------------------------------------------

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await api.delete(`/mongo/clientes/${id}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mongo-clientes"] });
      toast.success("Cliente eliminado exitosamente");
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      const errorMessage = error.response?.data?.detail || "Error al eliminar cliente";
      toast.error(errorMessage);
    },
  });

  // ---------------------------------------------------------------------------------
  // Mini-fuctions
  // ---------------------------------------------------------------------------------

  const handleEdit = (cliente: MongoCliente) => {
    setEditingClient(cliente);
    setIsFormOpen(true);
  };

  const handleDelete = (cliente: MongoCliente) => {
    if (confirm("¿Estás seguro de que quieres eliminar este cliente?")) {
      deleteMutation.mutate(cliente.id);
    }
  };

  const handleFormSubmit = (data: ClienteFormData) => {
    if (editingClient) {
      updateMutation.mutate({ id: editingClient.id, data});
    } else {
      createMutation.mutate(data);
    }
  };

  const handleFormOpenChange = (open: boolean) => {
    setIsFormOpen(open);
    if (!open) {
      setEditingClient(null);
    }
  };

  if (error) {
    toast.error("Error loading clients");
  }

  // ---------------------------------------------------------------------------------
  // Screen
  // ---------------------------------------------------------------------------------

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
        key={editingClient?.id ?? "new"} 
        open={isFormOpen}
        onOpenChange={handleFormOpenChange}
        onSubmit={handleFormSubmit}
        dbType="mongo"
        generos={["Masculino", "Femenino", "Otro"]}
        addPreferencias={true}
        initialData={editingClient ? {
          nombre: editingClient.nombre,
          email: editingClient.email,
          genero: editingClient.genero,
          pais: editingClient.pais,
          preferencias: editingClient.preferencias
        } : undefined}
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
                <Card key={cliente.id} className="p-4">
                  <div className="flex items-start justify-between">
                    <div className="flex-1">
                      <h3 className="font-semibold text-lg">{cliente.nombre}</h3>
                      <p className="text-sm text-muted-foreground">{cliente.email}</p>
                      <div className="mt-2 flex gap-2">
                        <span className="text-xs px-2 py-1 bg-muted rounded">{cliente.genero}</span>
                        <span className="text-xs px-2 py-1 bg-muted rounded">{cliente.pais}</span>
                      </div>
                    </div>
                    <div className="flex items-center gap-2 ml-4">
                      <div className="text-sm text-muted-foreground mr-4">
                        {new Date(cliente.creado).toLocaleDateString()}
                      </div>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => handleEdit(cliente)}
                        disabled={updateMutation.isPending}
                      >
                        <Edit className="h-4 w-4" />
                      </Button>
                      <Button
                        variant="destructive"
                        size="sm"
                        onClick={() => handleDelete(cliente)}
                        disabled={deleteMutation.isPending}
                      >
                        <Trash2 className="h-4 w-4" />
                      </Button>
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