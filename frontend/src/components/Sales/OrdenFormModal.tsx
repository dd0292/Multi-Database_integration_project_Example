/* eslint-disable @typescript-eslint/no-explicit-any */
import { useForm, useFieldArray } from "react-hook-form";
import { useQuery } from "@tanstack/react-query";
import { FormModal } from "../../components/common/FormModal";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Textarea } from "../../components/ui/textarea";
import { Plus, Trash2 } from "lucide-react";
import api from "../../services/api";

interface OrdenItem {
  producto_id: string;
  cantidad: number;
  precio_unit: number;
  descuento_pct?: number;
}

interface OrdenFormData {
  cliente_id: string;
  fecha: string;
  canal: string;
  moneda: string;
  items: OrdenItem[];
  descripcion?: string;
}

interface OrdenFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: OrdenFormData) => void;
  dbType: "mongo" | "mssql" | "mysql" | "supabase" | "neo4j";
  monedas: Array<string>;
  canales: Array<string>;
  addDescuentoPct?: boolean;
  extraInfo?: boolean;
}

export function OrdenFormModal({
  open,
  onOpenChange,
  onSubmit,
  dbType,
  monedas,
  canales,
  addDescuentoPct = false,
  extraInfo = false
}: OrdenFormModalProps) {
  const { register, handleSubmit, setValue, watch, control, reset, formState: { errors } } = useForm<OrdenFormData>({
    defaultValues: {
      cliente_id: "",
      fecha: new Date().toISOString().split("T")[0],
      canal: canales[0],
      moneda: monedas[0],
      items: [{ producto_id: "", cantidad: 1, precio_unit: 0, descuento_pct: 0 }],
      descripcion: "",
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

  const calculateItemTotal = (item: OrdenItem) => {
    const subtotal = item.cantidad * item.precio_unit;
    const descuento = subtotal * ((item.descuento_pct || 0) / 100);
    return subtotal - descuento;
  };

  const calculateItemSubtotal = (item: OrdenItem) => {
    return item.cantidad * item.precio_unit;
  };

  const calculateItemDescuento = (item: OrdenItem) => {
    const subtotal = item.cantidad * item.precio_unit;
    return subtotal * ((item.descuento_pct || 0) / 100);
  };

  const calculateSubtotal = () => {
    const items = watch("items");
    return items.reduce((sum, item) => sum + calculateItemSubtotal(item), 0);
  };

  const calculateTotalDescuento = () => {
    const items = watch("items");
    return items.reduce((sum, item) => sum + calculateItemDescuento(item), 0);
  };

  const calculateTotal = () => {
    const items = watch("items");
    return items.reduce((sum, item) => sum + calculateItemTotal(item), 0);
  };

  const onFormSubmit = (data: OrdenFormData) => {
    onSubmit(data);
    reset();
  };

  const addItem = () => {
    append({ producto_id: "", cantidad: 1, precio_unit: 0, descuento_pct: 0 });
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
                {canales.map((c) => (
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
              {monedas.map((m) => (
                <SelectItem key={m} value={m}>
                  {m}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Extra Info - Description */}
        {extraInfo && (
          <div className="space-y-2">
            <Label htmlFor="descripcion">Descripción (Opcional)</Label>
            <Textarea
              id="descripcion"
              {...register("descripcion")}
              placeholder="Descripción adicional de la orden..."
              rows={3}
            />
          </div>
        )}

        <div className="space-y-2">
          <div className="flex items-center justify-between">
            <Label>Items</Label>
            <Button
              type="button"
              variant="outline"
              size="sm"
              onClick={addItem}
            >
              <Plus className="h-4 w-4 mr-1" />
              Agregar
            </Button>
          </div>

          <div className="space-y-2 max-h-60 overflow-y-auto">
            {fields.map((field, index) => (
              <div key={field.id} className="flex gap-2 items-start p-3 border rounded-lg">
                <div className="flex-1 space-y-2">
                  <Select
                    value={watch(`items.${index}.producto_id`)}
                    onValueChange={(value) => setValue(`items.${index}.producto_id`, value)}
                  >
                    <SelectTrigger className="text-xs">
                      <SelectValue placeholder="Seleccionar producto" />
                    </SelectTrigger>
                    <SelectContent>
                      {productos?.map((producto: any) => (
                        <SelectItem key={producto._id || producto.id || producto.ProductoId || producto.producto_id} value={String(producto._id || producto.id || producto.ProductoId || producto.producto_id)}>
                          {producto.nombre || producto.Nombre}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>

                  <div className={`grid gap-2 ${addDescuentoPct ? 'grid-cols-3' : 'grid-cols-2'}`}>
                    <div className="space-y-1">
                      <Label className="text-xs">Cantidad</Label>
                      <Input
                        type="number"
                        min="1"
                        {...register(`items.${index}.cantidad`, { valueAsNumber: true, min: 1 })}
                        className="text-xs"
                      />
                    </div>
                    <div className="space-y-1">
                      <Label className="text-xs">Precio Unit.</Label>
                      <Input
                        type="number"
                        min="0"
                        step="0.01"
                        {...register(`items.${index}.precio_unit`, { valueAsNumber: true, min: 0 })}
                        className="text-xs"
                      />
                    </div>
                    {addDescuentoPct && (
                      <div className="space-y-1">
                        <Label className="text-xs">Desc. (%)</Label>
                        <Input
                          type="number"
                          min="0"
                          max="100"
                          step="0.01"
                          {...register(`items.${index}.descuento_pct`, { 
                            valueAsNumber: true,
                            min: 0,
                            max: 100
                          })}
                          className="text-xs"
                          placeholder="0"
                        />
                      </div>
                    )}
                  </div>

                  {/* Item Summary */}
                  <div className="text-xs text-muted-foreground grid grid-cols-3 gap-1 pt-1">
                    <div>
                      <span>Subtotal: </span>
                      <span>{watch("moneda")} {calculateItemSubtotal(watch(`items.${index}`)).toFixed(2)}</span>
                    </div>
                    {addDescuentoPct && (
                      <div className="text-destructive">
                        <span>Desc: </span>
                        <span>-{watch("moneda")} {calculateItemDescuento(watch(`items.${index}`)).toFixed(2)}</span>
                      </div>
                    )}
                    <div className="font-medium">
                      <span>Total: </span>
                      <span>{watch("moneda")} {calculateItemTotal(watch(`items.${index}`)).toFixed(2)}</span>
                    </div>
                  </div>
                </div>

                {fields.length > 1 && (
                  <Button
                    type="button"
                    variant="ghost"
                    size="icon"
                    onClick={() => remove(index)}
                    className="h-8 w-8 text-destructive hover:text-destructive"
                  >
                    <Trash2 className="h-4 w-4" />
                  </Button>
                )}
              </div>
            ))}
          </div>
        </div>

        {/* Order Summary */}
        <div className="pt-2 border-t space-y-2">
          <div className="flex justify-between items-center">
            <span>Subtotal:</span>
            <span>{watch("moneda")} {calculateSubtotal().toFixed(2)}</span>
          </div>
          
          {addDescuentoPct && (
            <div className="flex justify-between items-center text-destructive">
              <span>Descuento Total:</span>
              <span>-{watch("moneda")} {calculateTotalDescuento().toFixed(2)}</span>
            </div>
          )}
          
          <div className="flex justify-between items-center text-lg font-semibold border-t pt-2">
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