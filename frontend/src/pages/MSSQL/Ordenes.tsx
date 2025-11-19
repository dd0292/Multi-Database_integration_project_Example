import { useState } from "react";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { Plus, Upload, Download } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { DataTable } from "../../components/common/DataTable";
import { toast } from "sonner";
import api from "../../services/api";
import { Dialog, DialogContent, DialogHeader, DialogTitle } from "../../components/ui/dialog";
import { Alert, AlertDescription } from "../../components/ui/alert";
import { CheckCircle, AlertCircle } from "lucide-react";
import type { MSSQLOrden } from "../../types/MSSQL/Orden";

const MSSQLOrdenes = () => {
  const [page, setPage] = useState(1);
  const [isBulkOpen, setIsBulkOpen] = useState(false);
  const [bulkFile, setBulkFile] = useState<File | null>(null);
  const [bulkResult, setBulkResult] = useState<any>(null);
  const [isUploading, setIsUploading] = useState(false);
  const limit = 20;
  const queryClient = useQueryClient();

  const { data, isLoading } = useQuery({
    queryKey: ["mssql-ordenes", page],
    queryFn: async () => {
      const response = await api.get<{ data: MSSQLOrden[]; total: number }>(
        `/mssql/ordenes?page=${page}&limit=${limit}`
      );
      return response.data;
    },
  });

  const downloadTemplate = () => {
    const template = [
      {
        cliente_id: 1,
        fecha: "2025-01-15",
        canal: "WEB",
        moneda: "USD",
        items: [
          { producto_id: 1, cantidad: 2, precio_unit: 50.0, descuento_pct: 0 },
          { producto_id: 2, cantidad: 1, precio_unit: 100.0, descuento_pct: 10 }
        ]
      },
      {
        cliente_id: 2,
        fecha: "2025-01-16",
        canal: "TIENDA",
        moneda: "USD",
        items: [
          { producto_id: 3, cantidad: 1, precio_unit: 75.0, descuento_pct: 0 }
        ]
      }
    ];

    const jsonString = JSON.stringify(template, null, 2);
    const blob = new Blob([jsonString], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = "ordenes_template.json";
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleBulkFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) {
      setBulkFile(file);
      setBulkResult(null);
    }
  };

  const handleBulkUpload = async () => {
    if (!bulkFile) return;

    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", bulkFile);

    try {
      const response = await api.post("/mssql/ordenes/bulk/upload", formData, {
        headers: { "Content-Type": "multipart/form-data" },
      });
      setBulkResult(response.data);
      queryClient.invalidateQueries({ queryKey: ["mssql-ordenes"] });
      toast.success(`Bulk upload completed: ${response.data.success} success, ${response.data.failed} failed`);
    } catch (error: any) {
      toast.error(error.response?.data?.detail || "Bulk upload failed");
    } finally {
      setIsUploading(false);
    }
  };

  const columns = [
    {
      header: "ID",
      accessor: (row: MSSQLOrden) => <span className="font-mono">{row.OrdenId}</span>,
    },
    {
      header: "Cliente ID",
      accessor: (row: MSSQLOrden) => row.ClienteId,
    },
    {
      header: "Date",
      accessor: (row: MSSQLOrden) => new Date(row.Fecha).toLocaleDateString(),
    },
    {
      header: "Channel",
      accessor: (row: MSSQLOrden) => (
        <span className="text-xs px-2 py-1 bg-muted rounded">{row.Canal}</span>
      ),
    },
    {
      header: "Currency",
      accessor: (row: MSSQLOrden) => row.Moneda,
    },
    {
      header: "Total",
      accessor: (row: MSSQLOrden) => `${row.Moneda} ${row.Total.toFixed(2)}`,
    },
  ];

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-mssql">MS SQL Ordenes</h1>
          <p className="text-muted-foreground mt-1">Manage sales orders in MS SQL Server</p>
        </div>
        <div className="flex gap-2">
          <Button variant="outline" onClick={() => setIsBulkOpen(true)}>
            <Upload className="h-4 w-4 mr-2" />
            Bulk Upload
          </Button>
        </div>
      </div>

      <Dialog open={isBulkOpen} onOpenChange={setIsBulkOpen}>
        <DialogContent className="max-w-md">
          <DialogHeader>
            <DialogTitle>Bulk Upload Ordenes</DialogTitle>
          </DialogHeader>
          <div className="space-y-4">
            <Button variant="outline" onClick={downloadTemplate} className="w-full">
              <Download className="h-4 w-4 mr-2" />
              Download JSON Template
            </Button>

            <div className="border-2 border-dashed rounded p-4">
              <input
                type="file"
                accept=".json"
                onChange={handleBulkFileChange}
                className="w-full"
              />
              {bulkFile && <p className="text-sm mt-2">Selected: {bulkFile.name}</p>}
            </div>

            {bulkResult && (
              <Alert variant={bulkResult.failed > 0 ? "destructive" : "default"}>
                {bulkResult.failed === 0 ? (
                  <>
                    <CheckCircle className="h-4 w-4" />
                    <AlertDescription>
                      {bulkResult.success} orders imported successfully
                    </AlertDescription>
                  </>
                ) : (
                  <>
                    <AlertCircle className="h-4 w-4" />
                    <AlertDescription>
                      {bulkResult.success} success, {bulkResult.failed} failed
                    </AlertDescription>
                  </>
                )}
              </Alert>
            )}

            {bulkResult?.errors && bulkResult.errors.length > 0 && (
              <div className="bg-destructive/10 p-3 rounded max-h-40 overflow-y-auto text-sm">
                {bulkResult.errors.slice(0, 5).map((err: any, i: number) => (
                  <p key={i} className="text-destructive">
                    Row {err.row}: {err.error}
                  </p>
                ))}
                {bulkResult.errors.length > 5 && (
                  <p className="text-muted-foreground">+ {bulkResult.errors.length - 5} more</p>
                )}
              </div>
            )}

            <Button
              className="bg-mssql hover:bg-mssql-dark w-full"
              onClick={handleBulkUpload}
              disabled={!bulkFile || isUploading}
            >
              {isUploading ? "Uploading..." : "Upload"}
            </Button>
          </div>
        </DialogContent>
      </Dialog>

      <Card className="border-l-4 border-mssql">
        <CardHeader>
          <CardTitle>Orders List</CardTitle>
          <CardDescription>{data?.total || 0} total orders</CardDescription>
        </CardHeader>
        <CardContent>
          <DataTable
            data={data?.data || []}
            columns={columns}
            isLoading={isLoading}
            page={page}
            totalPages={Math.ceil((data?.total || 0) / limit)}
            onPageChange={setPage}
            emptyMessage="No orders found. Create or upload orders!"
          />
        </CardContent>
      </Card>
    </div>
  );
};

export default MSSQLOrdenes;
