# Frontend Documentation

## Technology Stack

### Core Technologies
- [React](https://react.dev/) - UI library for building user interfaces
- [TypeScript](https://www.typescriptlang.org/) - Type-safe JavaScript for better development experience
- [Vite](https://vite.dev/) - Fast build tool and development server
- [Axios](https://axios-http.com/) - HTTP client for API requests

### UI & Styling
- [Tailwind CSS](https://tailwindcss.com/) - Utility-first CSS framework
- [shadcn/ui](https://ui.shadcn.com/) - Reusable component library built on Radix UI
- [Radix UI](https://www.radix-ui.com/) - Unstyled, accessible component primitives
- [Sonner](https://sonner.emilkowal.ski/) - Toast notifications

### Development Tools
- [ESLint](https://eslint.org/) - Code linting and quality
- [PostCSS](https://postcss.org/) - CSS processing

## Project Structure
```bash
frontend/
├── public/                         # Static assets
├── src/
│   ├── assets/                     # Images, icons, etc.
│   ├── components/                 # React components
│   │   ├── common/                 # Reusable components
│   │   ├── Loader/                 # File upload components
│   │   ├── Sales/                  # Business-specific forms
│   │   ├── ui/                     # shadcn/ui components (100+ files)
│   │   │   ├── button.tsx
│   │   │   ├── form.tsx
│   │   │   ├── table.tsx
│   │   │   └── ... (all other UI components)
│   │   ├── AppSidebar.tsx          # Main navigation sidebar
│   │   ├── HomeButton.tsx          # Home navigation
│   │   └── ThemeToggle.tsx         # Dark/light theme switcher
│   ├── hooks/                      # Custom React hooks
│   │   ├── useCrudOperations.ts    # CRUD operations management
│   │   └── useFormHandler.ts       # Form state management
│   ├── pages/                      # Application pages/routes
│   │   ├── <DataBase01>/
│   │   ├── <...>/ 
│   │   ├── <DataBaseN>/           
│   │   ├── Index.tsx               # Home page
│   │   └── NotFound.tsx            # 404 error page
│   ├── services/                   # API services
│   │   └── api.ts                  # Axios instance and API configuration
│   ├── types/                      # TypeScript type definitions
│   │   ├── <DataBase01>/           # DataBase01-specific types
│   │   └── iObjetc.ts              # Base objetc interfaces
│   ├── utils/                      # Utility functions
│   └──  main.tsx                   # Application entry point
├── *.config.*                      # Build configuration
└── README.md                       # Project documentation
```



This template provides a minimal setup to get React working in Vite with HMR and some ESLint rules. Currently, there are two official available:

- [@vitejs/plugin-react](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react) uses [Babel](https://babeljs.io/) (or [oxc](https://oxc.rs) when used in [rolldown-vite](https://vite.dev/guide/rolldown)) for Fast Refresh
- [@vitejs/plugin-react-swc](https://github.com/vitejs/vite-plugin-react/blob/main/packages/plugin-react-swc) uses [SWC](https://swc.rs/) for Fast Refresh

## React Compiler

The React Compiler is enabled on this template. See [this documentation](https://react.dev/learn/react-compiler) for more information. **Note:** This will impact Vite dev & build performances.

## Expanding the ESLint configuration

If you are developing a production application, we recommend updating the configuration to enable type-aware lint rules:

```js
export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...

      // Remove tseslint.configs.recommended and replace with this
      tseslint.configs.recommendedTypeChecked,
      // Alternatively, use this for stricter rules
      tseslint.configs.strictTypeChecked,
      // Optionally, add this for stylistic rules
      tseslint.configs.stylisticTypeChecked,

      // Other configs...
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

You can also install [eslint-plugin-react-x](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-x) and [eslint-plugin-react-dom](https://github.com/Rel1cx/eslint-react/tree/main/packages/plugins/eslint-plugin-react-dom) for React-specific lint rules:

```js
// eslint.config.js
import reactX from 'eslint-plugin-react-x'
import reactDom from 'eslint-plugin-react-dom'

export default defineConfig([
  globalIgnores(['dist']),
  {
    files: ['**/*.{ts,tsx}'],
    extends: [
      // Other configs...
      // Enable lint rules for React
      reactX.configs['recommended-typescript'],
      // Enable lint rules for React DOM
      reactDom.configs.recommended,
    ],
    languageOptions: {
      parserOptions: {
        project: ['./tsconfig.node.json', './tsconfig.app.json'],
        tsconfigRootDir: import.meta.dirname,
      },
      // other options...
    },
  },
])
```

## Custom Hooks

### Form Handler
This hook manages form state and operations for CRUD interfaces. It provides a consistent way to handle form opening/closing, editing, deleting, and submitting across different components, especificly the **Forms**.

```js
import { useState } from "react";

// This handes the input from the UI layer
export function useFormHandler<T extends { id: string }>() {
  const [isFormOpen, setIsFormOpen] = useState(false);
  const [editingItem, setEditingItem] = useState<T | null>(null);

  // Fuctions

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
```

### Use Crud Operations Hooks
This hook provides complete CRUD (Create, Read, Update, Delete) operations with built-in caching, error handling, and user feedback. **Location:** [`frontend/src/hooks/useCrudOperations.ts`](src/hooks/useCrudOperations.ts)

Example
```js
const { data, createMutation, updateMutation, deleteMutation } = useCrudOperations<DataBase_Object, ObjectFormData>({
  endpoint: "/<DataBase>/object",
  queryKey: "<DataBase>-object",
  formToPayload: objectFormToPayload,
  onSuccessMessage: "Coso guardado exitosamente"
});
```

## How to Create New Types

**Step 1:** Create Base Interface
```typescript
// src/types/iObject.ts

// Here you add all the info the user is going to insert into the form to create the object (this is NOT database specific)
export interface _Object_FormData {
  nombre: string;
  precio: number;
  // etc...
}

// Interface to create the Form
export interface ProductoFormModalProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onSubmit: (data: _Object_FormData) => void;
  dbType: "mongo" | "mssql" | "mysql" | "supabase" | "neo4j";
  initialData?: Partial<_Object_FormData>;
  categorias: Array<string>;
}
```

**Step 2:** Create Database-Specific Implementation
```typescript
// src/types/<DataBase>/Object.ts
import type { _Object_FormData } from "../iObject";

// Interface for data received from the <DataBase> API
// (AKA: Info you received from the database)
export interface DB_Object{
  _id: number,
  nombre: string;
  precio: string;
  // etc...
}

// Function that transforms form data to API payload
// (AKA: Info you give to the database)
export const _FormToPayload = (data: _Object_FormData) => ({
  _id: 0000,
  nombre: data.nombre,
  precio: data.precio.toString(),
  // etc...
});
```

**Step 3:** Use in Components

```typescript
const DataBase_Object = () => {

  const {
    createMutation,
    updateMutation
  } = useCrudOperations<DB_Object, _Object_FormData>({
    endpoint: "/<DataBase>/object",
    queryKey: "<DataBase>-object",
    formToPayload: _FormToPayload,
    onSuccessMessage: "Obj Procesado exitosamente"
  });

  const {
    editingItem: objetcToEdit,
    handleFormSubmit,
  } = useFormHandler<DB_Object>();

  const onFormSubmit = (data: _Object_FormData) => {
    handleFormSubmit(
      data,
      objetcToEdit,
      createMutation.mutate,
      (id, data) => updateMutation.mutate({ id, data })
    );
  };

  return (
    // Your component
  )

```