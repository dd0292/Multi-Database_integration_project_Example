import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Trash2, Pencil } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { DataTable } from "../../components/common/DataTable";
import { toast } from "sonner";
import api from "../../services/api";
import type { SupabaseCliente } from "../../types/Supabase/Cliente";
import { ClienteFormModal } from "../../components/Sales/ClienteFormModal";

const SupabaseClientes = () => {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingCliente, setEditingCliente] = useState<SupabaseCliente | null>(null);

  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["supabase-clientes"],
    queryFn: async () => {
      const response = await api.get<{ data: SupabaseCliente[]; total: number }>(
        `/supabase/clientes?page=1&limit=10000`
      );
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (newCliente: Omit<SupabaseCliente, "cliente_id" | "fecha_registro">) => {
      const response = await api.post<SupabaseCliente>("/supabase/clientes", newCliente);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["supabase-clientes"] });
      setIsFormOpen(false);
    },
  });

  const updateMutation = useMutation({
    mutationFn: async (cliente: SupabaseCliente) => {
      const response = await api.patch<SupabaseCliente>(
        `/supabase/clientes/${cliente.cliente_id}`,
        {
          nombre: cliente.nombre,
          email: cliente.email,
          genero: cliente.genero,
          pais: cliente.pais,
        }
      );
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["supabase-clientes"] });
      setEditingCliente(null);
      setIsFormOpen(false);
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (clienteId: string) => {
      await api.delete(`/supabase/clientes/${clienteId}`);
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["supabase-clientes"] });
    },
    onError: (error: any) => {
      // Assume all 500s are FK constraint violations
      if (error.response?.status === 500) {
        toast.error(
          "Cannot delete: This client is referenced by other entities. Please delete those records first."
        );
        return;
      }
      toast.error("Cannot delete: This client is referenced by other entities. Please delete those records first.");
    },
  });

  const handleDelete = (cliente: SupabaseCliente) => {
    if (
      window.confirm(
        `Are you sure you want to delete client "${cliente.nombre}"? This action is permanent.`
      )
    ) {
      deleteMutation.mutate(cliente.cliente_id);
    }
  };

  const columns = [
    {
      header: "ID",
      accessor: (row: SupabaseCliente) => (
        <span className="font-mono text-xs">{row.cliente_id?.slice(0, 8)}...</span>
      ),
    },
    {
      header: "Name",
      accessor: (row: SupabaseCliente) => <span className="font-medium">{row.nombre}</span>,
    },
    {
      header: "Email",
      accessor: (row: SupabaseCliente) => row.email,
    },
    {
      header: "Gender",
      accessor: (row: SupabaseCliente) => (
        <span className="text-xs px-2 py-1 bg-muted rounded">{row.genero}</span>
      ),
    },
    {
      header: "Country",
      accessor: (row: SupabaseCliente) => row.pais,
    },
    {
      header: "Registered",
      accessor: (row: SupabaseCliente) => row.fecha_registro,
    },
    {
      header: "Actions",
      accessor: (row: SupabaseCliente) => (
        <div className="flex gap-2">
          <button
            onClick={() => {
              setEditingCliente(row);
              setIsFormOpen(true);
            }}
            className="text-muted-foreground hover:text-foreground transition-colors"
            title="Edit"
          >
            <Pencil className="h-4 w-4" />
          </button>
          <button
            onClick={() => handleDelete(row)}
            className="text-muted-foreground hover:text-foreground transition-colors"
            title="Delete"
          >
            <Trash2 className="h-4 w-4" />
          </button>
        </div>
      ),
    },
  ];

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-supabase">Supabase Clientes</h1>
          <p className="text-muted-foreground mt-1">Manage client records in Supabase</p>
        </div>
        <Button className="bg-supabase hover:bg-supabase-dark" onClick={() => setIsFormOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Client
        </Button>
      </div>
      <ClienteFormModal
          open={isFormOpen}
          onOpenChange={(open) => {
            setIsFormOpen(open);
            if (!open) setEditingCliente(null);
          }}
          onSubmit={(data) => {
            if (editingCliente) {
              updateMutation.mutate({
                ...editingCliente,
                ...data,
                genero: data.genero as "M" | "F",
              });
            } else {
              createMutation.mutate({
                ...data,
                genero: data.genero as "M" | "F",
              });
            }
          }}
          dbType="supabase"
          generos={["M", "F"]}
          initialData={editingCliente || undefined}
        />
      <Card className="border-l-4 border-supabase">
        <CardHeader>
          <CardTitle>Client List</CardTitle>
          <CardDescription>{data?.total || 0} total clients</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            data={data?.data || []}
            columns={columns}
            isLoading={isLoading}
            emptyMessage="No clients found. Create your first client!"
          />
        </CardContent>
      </Card>
    </div>
  );
};

export default SupabaseClientes;
