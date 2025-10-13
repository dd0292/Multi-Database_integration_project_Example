import { useEffect } from "react";
import { useForm, useFieldArray } from "react-hook-form";
import { FormModal } from "../../components/common/FormModal";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "../../components/ui/select";
import { Plus, Trash2 } from "lucide-react";
import { Controller } from "react-hook-form";


export interface ClienteFormData {
  nombre: string;
  email: string;
  genero: string;
  pais: string;
  preferencias?: Array<{
    categoria: string;
    texto: string;
  }>;
}

interface ClienteFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: ClienteFormData) => void;
  dbType: "mongo" | "mssql" | "mysql" | "supabase" | "neo4j";
  initialData?: Partial<ClienteFormData>;
  generos: Array<string>;
  extraInfo?: boolean;
}

const PAISES = ["CR", "GT", "SV", "HN", "NI", "PA", "BZ", "US"];

export function ClienteFormModal({
  open,
  onOpenChange,
  onSubmit,
  dbType,
  initialData,
  generos,
  extraInfo = false,
}: ClienteFormModalProps) {
  const {
    register,
    handleSubmit,
    reset,
    control,
    formState: { errors },
  } = useForm<ClienteFormData>({
    defaultValues: {
      nombre: "",
      email: "",
      genero: generos[0],
      pais: PAISES[0],
      preferencias: [],
      ...initialData, 
    },
  });

  const { fields, append, remove } = useFieldArray({
    control,
    name: "preferencias",
  });

  useEffect(() => {
    if (initialData) {
      reset({
        nombre: initialData.nombre || "",
        email: initialData.email || "",
        genero: initialData.genero || generos[0],
        pais: initialData.pais || "CR",
        preferencias: initialData.preferencias || [],
      });
    } else {
      reset({
        nombre: "",
        email: "",
        genero: generos[0],
        pais: "CR",
        preferencias: [],
      });
    }
  }, [initialData, reset, generos]);

  const onFormSubmit = (data: ClienteFormData) => {
    onSubmit(data);
    reset();
  };

  const addPreference = () => {
    append({ categoria: "", texto: "" });
  };

  return (
    <FormModal
      open={open}
      onOpenChange={(isOpen) => {
        onOpenChange(isOpen);
        if (!isOpen) reset();
      }}
      title={initialData ? "Editar Cliente" : "Nuevo Cliente"}
      description={`Crear un nuevo cliente en ${dbType.toUpperCase()}`}
    >
      <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="nombre">Nombre</Label>
          <Input
            id="nombre"
            {...register("nombre", { required: "Nombre es requerido" })}
            placeholder="Ej: Ana Rojas"
          />
          {errors.nombre && <p className="text-sm text-destructive">{errors.nombre.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="email">Email</Label>
          <Input
            id="email"
            type="email"
            {...register("email", {
              required: "Email es requerido",
              pattern: { value: /^[^\s@]+@[^\s@]+\.[^\s@]+$/, message: "Email inválido" },
            })}
            placeholder="ejemplo@correo.com"
          />
          {errors.email && <p className="text-sm text-destructive">{errors.email.message}</p>}
        </div>

        <Controller
          control={control}
          name="genero"
          defaultValue={generos[0]}
          render={({ field }) => (
            <div className="space-y-2">
              <Label htmlFor="genero">Género</Label>
              <Select
                value={field.value}
                onValueChange={(val) => field.onChange(val)}
              >
                <SelectTrigger>
                  <SelectValue placeholder={initialData?.genero || generos[0]} />
                </SelectTrigger>
                <SelectContent>
                  {generos.map((g) => (
                    <SelectItem key={g} value={g}>
                      {g}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        />
        <Controller
          control={control}
          name="pais"
          defaultValue={PAISES[0]}
          render={({ field }) => (
            <div className="space-y-2">
              <Label htmlFor="pais">País</Label>
              <Select
                value={field.value}
                onValueChange={(val) => field.onChange(val)}
              >
                <SelectTrigger>
                  <SelectValue placeholder= {initialData?.pais || PAISES[0]} />
                </SelectTrigger>
                <SelectContent>
                  {PAISES.map((p) => (
                    <SelectItem key={p} value={p}>
                      {p}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>
          )}
        />        
        {extraInfo && (
          <div className="space-y-4 border-t pt-4">
            <div className="flex items-center justify-between">
              <Label className="text-base">Preferencias</Label>
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={addPreference}
                className="flex items-center gap-2"
              >
                <Plus className="h-4 w-4" />
                Agregar Preferencia
              </Button>
            </div>

            {fields.length === 0 ? (
              <div className="text-center py-4 text-muted-foreground border rounded-lg">
                No hay preferencias agregadas
              </div>
            ) : (
              <div className="space-y-3">
                {fields.map((field, index) => (
                  <div key={field.id} className="flex gap-2 items-start p-3 border rounded-lg">
                    <div className="flex-1 grid grid-cols-2 gap-2">
                      <div className="space-y-1">
                        <Label htmlFor={`preferencias.${index}.categoria`} className="text-xs">
                          Categoría
                        </Label>
                        <Input
                          id={`preferencias.${index}.categoria`}
                          {...register(`preferencias.${index}.categoria` as const)}
                          placeholder="Ej: Canal, Producto, etc."
                        />
                      </div>
                      <div className="space-y-1">
                        <Label htmlFor={`preferencias.${index}.texto`} className="text-xs">
                          Texto
                        </Label>
                        <Input
                          id={`preferencias.${index}.texto`}
                          {...register(`preferencias.${index}.texto` as const)}
                          placeholder="Ej: Email, WhatsApp, etc."
                        />
                      </div>
                    </div>
                    <Button
                      type="button"
                      variant="ghost"
                      size="icon"
                      onClick={() => remove(index)}
                      className="mt-5 text-destructive hover:text-destructive"
                    >
                      <Trash2 className="h-4 w-4" />
                    </Button>
                  </div>
                ))}
              </div>
            )}
          </div>
        )}

        <div className="flex justify-end gap-2 pt-4">
          <Button type="button" variant="outline" onClick={() => onOpenChange(false)}>
            Cancelar
          </Button>
          <Button type="submit">
            {initialData ? "Actualizar" : "Crear"}
          </Button>
        </div>
      </form>
    </FormModal>
  );
}