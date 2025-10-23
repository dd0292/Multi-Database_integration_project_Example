import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { ClienteFormModal, } from "../../components/Sales/ClienteFormModal";
import { Button } from "../../components/ui/button";
import { Plus, Trash2, Edit } from "lucide-react";
import { toast } from "sonner";
import { useCrudOperations } from "../../hooks/useCrudOperations";
import { useFormHandler } from "../../hooks/useFormHandler";
import { clienteFormToPayload, type MongoCliente } from "../../types/Mongo/Cliente";
import type { ClienteFormData } from "../../types/iCliente";

const MongoClientes = () => {

  const {
    data,
    isLoading,
    error,
    createMutation,
    updateMutation,
    deleteMutation,
  } = useCrudOperations<MongoCliente, ClienteFormData>({
    endpoint: "/mongo/clientes",
    queryKey: "mongo-clientes",
    formToPayload: clienteFormToPayload,
    onSuccessMessage: "Cliente procesado exitosamente"
  });

  const {
    isFormOpen,
    editingItem: editingClient,
    handleEdit,
    handleDelete,
    handleFormOpenChange,
    handleFormSubmit,
  } = useFormHandler<MongoCliente>();

  const onFormSubmit = (data: ClienteFormData) => {
    handleFormSubmit(
      data,
      editingClient,
      createMutation.mutate,
      (id, data) => updateMutation.mutate({ id, data })
    );
  };
  const onDelete = (cliente: MongoCliente) => {
    handleDelete(cliente, deleteMutation.mutate);
  };

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
        <Button className="bg-mongo hover:bg-mongo-dark" onClick={() => handleFormOpenChange(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Client
        </Button>
      </div>

      <ClienteFormModal
        key={editingClient?.id ?? "new"} 
        open={isFormOpen}
        onOpenChange={handleFormOpenChange}
        onSubmit={onFormSubmit}
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
                        onClick={() => onDelete(cliente)}
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