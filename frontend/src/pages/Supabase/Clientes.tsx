import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { DataTable } from "../../components/common/DataTable";
import api from "../../services/api";
import type { SupabaseCliente } from "../../types/Supabase/Cliente";
import { ClienteFormModal } from "../../components/Sales/ClienteFormModal";

const SupabaseClientes = () => {
  const [page, setPage] = useState(1);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const limit = 20;

  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["supabase-clientes", page],
    queryFn: async () => {
      const response = await api.get<{ data: SupabaseCliente[]; total: number }>(
        `/supabase/clientes?page=${page}&limit=${limit}`
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
          onOpenChange={setIsFormOpen}
          onSubmit={(data) =>
            createMutation.mutate({
              ...data,
              genero: data.genero as "M" | "F",
            })
          }
          dbType="supabase"
          generos={["M", "F"]}
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
            page={page}
            totalPages={Math.ceil((data?.total || 0) / limit)}
            onPageChange={setPage}
            emptyMessage="No clients found. Create your first client!"
          />
        </CardContent>
      </Card>
    </div>
  );
};

export default SupabaseClientes;
