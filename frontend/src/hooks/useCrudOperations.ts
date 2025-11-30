// hooks/useCrudOperations.ts
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import api from "../services/api";
import { AxiosError } from "axios";

interface UseCrudOperationsProps<TForm> {
  endpoint: string;
  queryKey: string;
  formToPayload?: (data: TForm) => unknown;
  onSuccessMessage?: string;
}

export function useCrudOperations<T extends { id: string }, TForm>({
  endpoint,
  queryKey,
  formToPayload,
  onSuccessMessage = "Operación exitosa"
}: UseCrudOperationsProps<TForm>) {

  const queryClient = useQueryClient();
  const [page, setPage] = useState(1);
  const limit = 20;

  // GET with pagination
  const { data, isLoading, error } = useQuery({
    queryKey: [queryKey, page],
    queryFn: async () => {
      const response = await api.get<{ data: T[]; total: number }>(
        `${endpoint}?page=${page}&limit=${limit}`
      );
      return response.data;
    },
  });

  const totalPages =
    data && data.total ? Math.ceil(data.total / limit) : 1;

  // MUTATIONS (POST – PATCH – DELETE)
  const createMutation = useMutation({
    mutationFn: async (formData: TForm) => {
      const payload = formToPayload ? formToPayload(formData) : formData;
      const response = await api.post(endpoint, payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [queryKey] });
      toast.success(onSuccessMessage);
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      toast.error(error.response?.data?.detail || "Error al crear");
    },
  });

  const updateMutation = useMutation({
    mutationFn: async ({ id, data }: { id: string; data: TForm }) => {
      const payload = formToPayload ? formToPayload(data) : data;
      const response = await api.patch(`${endpoint}/${id}`, payload);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [queryKey] });
      toast.success(onSuccessMessage.replace("crear", "actualizar"));
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      toast.error(error.response?.data?.detail || "Error al actualizar");
    },
  });

  const deleteMutation = useMutation({
    mutationFn: async (id: string) => {
      const response = await api.delete(`${endpoint}/${id}`);
      return response.data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: [queryKey] });
      toast.success(onSuccessMessage.replace("crear", "eliminar"));
    },
    onError: (error: AxiosError<{ detail?: string }>) => {
      toast.error(error.response?.data?.detail || "Error al eliminar");
    },
  });

  return {
    data,
    isLoading,
    error,
    page,
    setPage,
    totalPages,
    createMutation,
    updateMutation,
    deleteMutation,
  };
}
