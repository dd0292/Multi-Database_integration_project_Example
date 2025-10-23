import { useForm } from "react-hook-form";
import { FormModal } from "../../components/common/FormModal";
import { Button } from "../../components/ui/button";
import { Input } from "../../components/ui/input";
import { Label } from "../../components/ui/label";
import type { ProductoFormData, ProductoFormModalProps } from "../../types/iProducto";

export function ProductoFormModal({
  open,
  onOpenChange,
  onSubmit,
  dbType,
  initialData,
  codeNeeded = true,
  extraCodes: extraInfo = false,
  tiposCategorias = [],
}: ProductoFormModalProps) {
  const { register, handleSubmit, reset, formState: { errors } } = useForm<ProductoFormData>({
    defaultValues: initialData || {
      nombre: "",
      categoria: "",
      codigo: "",
      categoriasAdicionales: {},
    },
  });

  const onFormSubmit = (data: ProductoFormData) => {
    onSubmit(data);
    reset();
  };

  const getCodigoLabel = () => {
    switch (dbType) {
      case "mssql":
        return "SKU";
      case "mysql":
        return "Código Alt";
      case "mongo":
        return "Código Mongo";
      default:
        return "Código";
    }
  };

  return (
    <FormModal
      open={open}
      onOpenChange={(isOpen) => {
        onOpenChange(isOpen);
        if (!isOpen) reset();
      }}
      title={initialData ? "Editar Producto" : "Nuevo Producto"}
      description={`Crear un nuevo producto en ${dbType.toUpperCase()}`}
    >
      <form onSubmit={handleSubmit(onFormSubmit)} className="space-y-4">
        <div className="space-y-2">
          <Label htmlFor="nombre">Nombre</Label>
          <Input
            id="nombre"
            {...register("nombre", { required: "Nombre es requerido" })}
            placeholder="Ej: Tomate grande"
          />
          {errors.nombre && <p className="text-sm text-destructive">{errors.nombre.message}</p>}
        </div>

        <div className="space-y-2">
          <Label htmlFor="categoria">Categoría</Label>
          <Input
            id="categoria"
            {...register("categoria", { required: "Categoría es requerida" })}
            placeholder="Ej: Alimentos"
          />
          {errors.categoria && <p className="text-sm text-destructive">{errors.categoria.message}</p>}
        </div>

        {codeNeeded && (
          <div className="space-y-2">
            <Label htmlFor="codigo">{getCodigoLabel()}</Label>
            <Input
              id="codigo"
              {...register("codigo", { required: "Codigo es requerida" })}
              placeholder={`Ej: ${dbType === "mssql" ? "SKU-1001" : "ALT-AB12"}`}
            />
          {errors.categoria && <p className="text-sm text-destructive">{errors.codigo?.message}</p>}
          </div>
        )}

        {/* Fixed Additional Categories Section */}
        {extraInfo && tiposCategorias.length > 0 && (
          <div className="space-y-4 border-t pt-4">
            <Label className="text-base">Categorías Adicionales</Label>
            <div className="space-y-3">
              {tiposCategorias.map((tipo) => (
                <div key={tipo} className="space-y-1">
                  <Label htmlFor={`categoriasAdicionales.${tipo}`} className="text-sm">
                    {tipo}
                  </Label>
                  <Input
                    id={`categoriasAdicionales.${tipo}`}
                    {...register(`categoriasAdicionales.${tipo}` as const)}
                    placeholder={`Valor para ${tipo}`}
                  />
                </div>
              ))}
            </div>
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