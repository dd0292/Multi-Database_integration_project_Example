import { useState } from "react";

export function useFormHandler<T extends { id: string }>() {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<T | null>(null);

  const handleEdit = (item: T) => {
    setEditingItem(item);
    setIsFormOpen(true);
  };

  const handleDelete = (item: T, onDelete: (id: string) => void) => {
    if (confirm("¿Estás seguro de que quieres eliminar este item?")) {
      onDelete(item.id);
    }
  };

  const handleFormOpenChange = (open: boolean) => {
    setIsFormOpen(open);
    if (!open) {
      setEditingItem(null);
    }
  };

  const handleFormSubmit = <TForm,>(
    data: TForm,
    editingItem: T | null,
    onCreate: (data: TForm) => void,
    onUpdate: (id: string, data: TForm) => void
  ) => {
    if (editingItem) {
      onUpdate(editingItem.id, data);
    } else {
      onCreate(data);
    }
    setIsFormOpen(false);
  };

  return {
    isFormOpen,
    setIsFormOpen,
    editingItem,
    setEditingItem,
    handleEdit,
    handleDelete,
    handleFormOpenChange,
    handleFormSubmit,
  };
}