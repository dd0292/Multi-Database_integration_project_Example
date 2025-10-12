import { Database } from "lucide-react";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../components/ui/card";
import { useNavigate } from "react-router-dom";

const databases = [
  {
    name: "MongoDB",
    description: "Document-based NoSQL database",
    color: "mongo",
    path: "/mongo/clientes",
    icon: "🟡",
  },
  {
    name: "MS SQL Server",
    description: "Relational database with bulk loader",
    color: "mssql",
    path: "/mssql/clientes",
    icon: "🟣",
  },
  {
    name: "MySQL",
    description: "Open-source relational database",
    color: "mysql",
    path: "/mysql/clientes",
    icon: "🔵",
  },
  {
    name: "Supabase",
    description: "PostgreSQL with real-time subscriptions",
    color: "supabase",
    path: "/supabase/clientes",
    icon: "🟢",
  },
  {
    name: "Neo4j",
    description: "Graph database for connected data",
    color: "neo4j",
    path: "/neo4j/clientes",
    icon: "🔴",
  },
];

const Index = () => {
  const navigate = useNavigate();
  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-8">
        <h1 className="text-4xl font-bold mb-2">Multi-Database Sales Manager</h1>
        <p className="text-muted-foreground text-lg">
          Manage sales, clients, and products across multiple database systems
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {databases.map((db) => (
          <Card
            key={db.name}
            className={`cursor-pointer transition-all hover:shadow-lg border-l-4 border-${db.color}`}
            onClick={() => navigate(db.path)}
          >
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <span className="text-2xl">{db.icon}</span>
                <span className={`text-${db.color}`}>{db.name}</span>
              </CardTitle>
              <CardDescription>{db.description}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Database className="h-4 w-4" />
                <span>View clients, products & orders</span>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Card className="mt-8">
        <CardHeader>
          <CardTitle>Getting Started</CardTitle>
          <CardDescription>Quick tips for using this application</CardDescription>
        </CardHeader>
        <CardContent className="space-y-3">
          <p className="text-sm">
            • Each database has its own section with CRUD operations for clients, products, and orders
          </p>
          <p className="text-sm">
            • MS SQL and MySQL include bulk loader functionality for importing CSV/Excel files
          </p>
          <p className="text-sm">
            • Use the sidebar navigation to switch between databases
          </p>
        </CardContent>
      </Card>
    </div>
  );
};

export default Index;
