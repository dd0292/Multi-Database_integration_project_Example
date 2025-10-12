import { Toaster } from "./components/ui/toaster";
import { Toaster as Sonner } from "./components/ui/sonner";
import { TooltipProvider } from "./components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route } from "react-router-dom";
import { SidebarProvider, SidebarTrigger } from "./components/ui/sidebar";
import { ThemeProvider } from "next-themes";
import { AppSidebar } from "./components/AppSidebar";
import { ThemeToggle } from "./components/ThemeToggle";
import Index from "./pages/Index";
import MongoClientes from "./pages/Mongo/Clientes";
import MongoProductos from "./pages/Mongo/Productos";
import MongoOrdenes from "./pages/Mongo/Ordenes";
import MSSQLClientes from "./pages/MSSQL/Clientes";
import MSSQLProductos from "./pages/MSSQL/Productos";
import MSSQLOrdenes from "./pages/MSSQL/Ordenes";
import MSSQLLoader from "./pages/MSSQL/Loader";
import MySQLClientes from "./pages/MySQL/Clientes";
import MySQLProductos from "./pages/MySQL/Productos";
import MySQLOrdenes from "./pages/MySQL/Ordenes";
import MySQLLoader from "./pages/MySQL/Loader";
import SupabaseClientes from "./pages/Supabase/Clientes";
import SupabaseProductos from "./pages/Supabase/Productos";
import SupabaseOrdenes from "./pages/Supabase/Ordenes";
import Neo4jClientes from "./pages/Neo4j/Clientes";
import Neo4jProductos from "./pages/Neo4j/Productos";
import Neo4jOrdenes from "./pages/Neo4j/Ordenes";
import NotFound from "./pages/NotFound";
import { HomeButton } from "./components/HomeButton";

const queryClient = new QueryClient();

const App = () => (
  <QueryClientProvider client={queryClient}>
    <ThemeProvider attribute="class" defaultTheme="system" enableSystem>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
        <SidebarProvider>
          <div className="flex min-h-screen w-full">
            <AppSidebar />
            <main className="flex-1 flex flex-col">
              <header className="h-14 border-b flex items-center justify-between px-4 bg-background sticky top-0 z-10">
                <div className="flex items-center">
                  <SidebarTrigger />
                  <h1 className="ml-4 text-lg font-semibold">Multi-Database Sales Manager</h1>
                </div>
                <div className="flex items-center">
                  <ThemeToggle />
                  < HomeButton />
                </div>
              </header>
              <div className="flex-1 p-6">
                <Routes>
                  <Route path="/" element={<Index />} />
                  <Route path="/mongo/clientes" element={<MongoClientes />} />
                  <Route path="/mongo/productos" element={<MongoProductos />} />
                  <Route path="/mongo/ordenes" element={<MongoOrdenes />} />
                  <Route path="/mssql/clientes" element={<MSSQLClientes />} />
                  <Route path="/mssql/productos" element={<MSSQLProductos />} />
                  <Route path="/mssql/ordenes" element={<MSSQLOrdenes />} />
                  <Route path="/mssql/loader" element={<MSSQLLoader />} />
                  <Route path="/mysql/clientes" element={<MySQLClientes />} />
                  <Route path="/mysql/productos" element={<MySQLProductos />} />
                  <Route path="/mysql/ordenes" element={<MySQLOrdenes />} />
                  <Route path="/mysql/loader" element={<MySQLLoader />} />
                  <Route path="/supabase/clientes" element={<SupabaseClientes />} />
                  <Route path="/supabase/productos" element={<SupabaseProductos />} />
                  <Route path="/supabase/ordenes" element={<SupabaseOrdenes />} />
                  <Route path="/neo4j/clientes" element={<Neo4jClientes />} />
                  <Route path="/neo4j/productos" element={<Neo4jProductos />} />
                  <Route path="/neo4j/ordenes" element={<Neo4jOrdenes />} />
                  <Route path="*" element={<NotFound />} />
                </Routes>
              </div>
            </main>
          </div>
        </SidebarProvider>
      </BrowserRouter>
    </TooltipProvider>
    </ThemeProvider>
  </QueryClientProvider>
);

export default App;
