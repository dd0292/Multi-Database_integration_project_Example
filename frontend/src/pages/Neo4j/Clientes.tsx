import { ClienteFormModal } from "../../components/Sales/ClienteFormModal";
import { toast } from "sonner";
import { Plus, Network, Edit, Trash2 } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { useCrudOperations } from "../../hooks/useCrudOperations";
import { clienteFormToPayload, type Neo4jCliente } from "../../types/Neo4j/Cliente";
import type { ClienteFormData } from "../../types/iCliente";
import { useFormHandler } from "../../hooks/useFormHandler";

const Neo4jClientes = () => {
  const {
    data,
    isLoading,
    error,
    page,
    setPage,
    totalPages,
    createMutation,
    updateMutation,
    deleteMutation,
  } = useCrudOperations<Neo4jCliente, ClienteFormData>({
    endpoint: "/neo4j/clientes",
    queryKey: "neo4j-clientes",
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
  } = useFormHandler<Neo4jCliente>();

  const onFormSubmit = (data: ClienteFormData) => {
    handleFormSubmit(
      data,
      editingClient,
      createMutation.mutate,
      (id, data) => updateMutation.mutate({ id, data })
    );
  };
  const onDelete = (cliente: Neo4jCliente) => {
    handleDelete(cliente, deleteMutation.mutate);
  };

  if (error) {
    toast.error("Error loading clients");
  }

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neo4j">Neo4j Clientes</h1>
          <p className="text-muted-foreground mt-1">Manage client nodes in Neo4j graph database</p>
        </div>
        <Button className="bg-neo4j hover:bg-neo4j-dark" onClick={() => handleFormOpenChange(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Client
        </Button>
      </div>
      <ClienteFormModal
        key={editingClient?.id ?? "new"} 
        open={isFormOpen}
        onOpenChange={handleFormOpenChange}
        onSubmit={onFormSubmit}
        dbType="neo4j"
        generos={['M','F','Otro','Masculino','Femenino']}
        addPreferencias={false}
        initialData={editingClient ? {
          nombre: editingClient.nombre,
          email: editingClient.email,
          genero: editingClient.genero,
          pais: editingClient.pais
        } : undefined}
      />

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
              No clients found. Create your first client node!
            </div>
          )}
        </CardContent>

        {data?.data && data.data.length > 0 && (
          <div className="border-t border-gray-200 dark:border-gray-700 pt-6 pb-4 px-6 bg-gray-50/50 dark:bg-gray-900/50 rounded-b-lg">
            <div className="flex flex-col sm:flex-row justify-between items-center gap-4">
              <div className="flex items-center gap-2 order-2 sm:order-1">
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page <= 1}
                  onClick={() => setPage(page - 1)}
                  className="min-w-[100px]"
                >
                  Previous
                </Button>
                
                <Button
                  variant="outline"
                  size="sm"
                  disabled={page >= totalPages}
                  onClick={() => setPage(page + 1)}
                  className="min-w-[100px]"
                >
                  Next
                </Button>
              </div>
              
              <div className="order-1 sm:order-2">
                <span className="text-sm font-medium text-gray-700 dark:text-gray-300 bg-white dark:bg-gray-800 px-3 py-1 rounded-md border shadow-sm">
                  Page {page} of {totalPages}
                </span>
              </div>
            </div>
          </div>
        )}

      </Card>
    </div>
  );
};

export default Neo4jClientes;
