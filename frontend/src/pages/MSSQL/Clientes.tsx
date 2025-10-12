import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { DataTable } from "../../components/common/DataTable";
import { ClienteFormModal } from "../../components/Sales/ClienteFormModal";
import { toast } from "sonner";
import api from "../../services/api";
import type { MSSQLCliente } from "../../types/databases";

const MSSQLClientes = () => {
  const [page, setPage] = useState(1);
  const [isFormOpen, setIsFormOpen] = useState(false);
  const limit = 20;
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["mssql-clientes", page],
    queryFn: async () => {
      const response = await api.get<{ data: MSSQLCliente[]; total: number }>(
        `/mssql/clientes?page=${page}&limit=${limit}`
      );
      return response.data;
    },
  });

  const createMutation = useMutation({
    mutationFn: async (data: any) => {
      return api.post("/mssql/clientes", {
        Nombre: data.nombre,
        Email: data.email,
        Genero: data.genero,
        Pais: data.pais,
      });
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["mssql-clientes"] });
      toast.success("Cliente creado exitosamente");
      setIsFormOpen(false);
    },
    onError: () => {
      toast.error("Error al crear cliente");
    },
  });

  const columns = [
    {
      header: "ID",
      accessor: (row: MSSQLCliente) => <span className="font-mono">{row.ClienteId}</span>,
    },
    {
      header: "Name",
      accessor: (row: MSSQLCliente) => <span className="font-medium">{row.Nombre}</span>,
    },
    {
      header: "Email",
      accessor: (row: MSSQLCliente) => row.Email,
    },
    {
      header: "Gender",
      accessor: (row: MSSQLCliente) => (
        <span className="text-xs px-2 py-1 bg-muted rounded">{row.Genero}</span>
      ),
    },
    {
      header: "Country",
      accessor: (row: MSSQLCliente) => row.Pais,
    },
  ];

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-mssql">MS SQL Clientes</h1>
          <p className="text-muted-foreground mt-1">Manage client records in MS SQL Server</p>
        </div>
        <Button className="bg-mssql hover:bg-mssql-dark" onClick={() => setIsFormOpen(true)}>
          <Plus className="h-4 w-4 mr-2" />
          New Client
        </Button>
      </div>

      <ClienteFormModal
        open={isFormOpen}
        onOpenChange={setIsFormOpen}
        onSubmit={(data) => createMutation.mutate(data)}
        dbType="mssql"
        generos={["Masculino", "Femenino"]} 
      />

      <Card className="border-l-4 border-mssql">
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

export default MSSQLClientes;
