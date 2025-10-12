import { useForm, useFieldArray } from "react-hook-form";
import { useQuery } from "@tanstack/react-query";
import { FormModal } from "../../components/common/FormModal";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Plus, Trash2 } from "lucide-react";
import api from "../../services/api";

interface OrdenItem {
  producto_id: string;
  cantidad: number;
  precio_unit: number;
}

interface OrdenFormData {
  cliente_id: string;
  fecha: string;
  canal: string;
  moneda: string;
  items: OrdenItem[];
}

interface OrdenFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: OrdenFormData) => void;
  dbType: "mongo" | "mssql" | "mysql" | "supabase" | "neo4j";
}

const CANALES = ["WEB", "TIENDA", "APP"];
const MONEDAS = ["CRC", "USD"];

export function OrdenFormModal({
  open,
  onOpenChange,
  onSubmit,
  dbType,
}: OrdenFormModalProps) {
  const { register, handleSubmit, setValue, watch, control, reset, formState: { errors } } = useForm<OrdenFormData>({
    defaultValues: {
      cliente_id: "",
      fecha: new Date().toISOString().split("T")[0],
      canal: "WEB",
      moneda: "CRC",
      items: [{ producto_id: "", cantidad: 1, precio_unit: 0 }],
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "items",
  });

  const { data: clientes } = useQuery({
    queryKey: [`${dbType}-clientes`],
    queryFn: async () => {
      const response = await api.get(`/${dbType}/clientes?limit=100`);
      return response.data.data || [];
    },
    enabled: open,
  });

  const { data: productos } = useQuery({
    queryKey: [`${dbType}-productos`],
    queryFn: async () => {
      const response = await api.get(`/${dbType}/productos?limit=100`);
      return response.data.data || [];
    },
    enabled: open,
  });

  const calculateTotal = () => {
    const items = watch("items");
    return items.reduce((sum, item) => sum + (item.cantidad * item.precio_unit), 0);
  };

  const onFormSubmit = (data: OrdenFormData) => {
    onSubmit(data);
    reset();
  };

  return (
    <FormModal
      open={open}
      onOpenChange={(isOpen) => {
        onOpenChange(isOpen);
        if (!isOpen) reset();
      }}
      title="Nueva Orden"
      description={`Crear una nueva orden en ${dbType.toUpperCase()}`}
    >
      <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="cliente_id">Cliente</Label>
          <Select
            value={watch("cliente_id")}
            onValueChange={(value) => setValue("cliente_id", value)}
          >
            <SelectTrigger>
              <SelectValue placeholder="Seleccionar cliente" />
            </SelectTrigger>
            <SelectContent>
              {clientes?.map((cliente: any) => (
                <SelectItem key={cliente._id || cliente.id || cliente.ClienteId || cliente.cliente_id} value={String(cliente._id || cliente.id || cliente.ClienteId || cliente.cliente_id)}>
                  {cliente.nombre || cliente.Nombre}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
          {errors.cliente_id && <p className="text-sm text-destructive">Cliente es requerido</p>}
        </div>

        <div className="grid grid-cols-2 gap-4">
          <div className="space-y-2">
            <Label htmlFor="fecha">Fecha</Label>
            <Input
              id="fecha"
              type="date"
              {...register("fecha", { required: true })}
            />
          </div>

          <div className="space-y-2">
            <Label htmlFor="canal">Canal</Label>
            <Select
              value={watch("canal")}
              onValueChange={(value) => setValue("canal", value)}
            >
              <SelectTrigger>
                <SelectValue />
              </SelectTrigger>
              <SelectContent>
                {CANALES.map((c) => (
                  <SelectItem key={c} value={c}>
                    {c}
                  </SelectItem>
                ))}
              </SelectContent>
            </Select>
          </div>
        </div>

        <div className="space-y-2">
          <Label htmlFor="moneda">Moneda</Label>
          <Select
            value={watch("moneda")}
            onValueChange={(value) => setValue("moneda", value)}
          >
            <SelectTrigger>
              <SelectValue />
            </SelectTrigger>
            <SelectContent>
              {MONEDAS.map((m) => (
                <SelectItem key={m} value={m}>
                  {m}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>Items</Label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={() => append({ producto_id: "", cantidad: 1, precio_unit: 0 })}
            >
              <Plus className="h-4 w-4 mr-1" />
              Agregar
            </Button>
          </div>

          <div className="space-y-2 max-h-60 overflow-y-auto">
            {fields.map((field, index) => (
              <div key={field.id} className="flex gap-2 items-start p-2 border rounded">
                <div className="flex-1 space-y-2">
                  <Select
                    value={watch(`items.${index}.producto_id`)}
                    onValueChange={(value) => setValue(`items.${index}.producto_id`, value)}
                  >
                    <SelectTrigger className="text-xs">
                      <SelectValue placeholder="Producto" />
                    </SelectTrigger>
                    <SelectContent>
                      {productos?.map((producto: any) => (
                        <SelectItem key={producto._id || producto.id || producto.ProductoId || producto.producto_id} value={String(producto._id || producto.id || producto.ProductoId || producto.producto_id)}>
                          {producto.nombre || producto.Nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <div className="grid grid-cols-2 gap-2">
                    <Input
                      type="number"
                      placeholder="Cantidad"
                      {...register(`items.${index}.cantidad`, { valueAsNumber: true, min: 1 })}
                      className="text-xs"
                    />
                    <Input
                      type="number"
                      placeholder="Precio Unit"
                      {...register(`items.${index}.precio_unit`, { valueAsNumber: true, min: 0 })}
                      className="text-xs"
                    />
                  </div>
                </div>

                {fields.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => remove(index)}
                    className="h-8 w-8"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        </div>

        <div className="pt-2 border-t">
          <div className="flex justify-between items-center text-lg font-semibold">
            <span>Total:</span>
            <span>{watch("moneda")} {calculateTotal().toFixed(2)}</span>
          </div>
        </div>

        <div className="flex justify-end gap-2 pt-4">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button type="submit">
            Crear Orden
          </Button>
        </div>
      </form>
    </FormModal>
  );
}
