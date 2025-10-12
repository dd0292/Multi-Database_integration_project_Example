import { Database, Package, ShoppingCart, Users, Upload } from "lucide-react";
import { NavLink, useLocation } from "react-router-dom";
import {
  Sidebar,
  SidebarContent,
  SidebarGroup,
  SidebarGroupContent,
  SidebarGroupLabel,
  SidebarMenu,
  SidebarMenuButton,
  SidebarMenuItem,
  useSidebar,
} from "../components/ui/sidebar";

const databases = [
  {
    name: "MongoDB",
    path: "/mongo",
    color: "mongo",
    icon: Database,
    items: [
      { title: "Clientes", path: "/mongo/clientes", icon: Users },
      { title: "Productos", path: "/mongo/productos", icon: Package },
      { title: "Órdenes", path: "/mongo/ordenes", icon: ShoppingCart },
    ],
  },
  {
    name: "MS SQL",
    path: "/mssql",
    color: "mssql",
    icon: Database,
    items: [
      { title: "Clientes", path: "/mssql/clientes", icon: Users },
      { title: "Productos", path: "/mssql/productos", icon: Package },
      { title: "Órdenes", path: "/mssql/ordenes", icon: ShoppingCart },
      { title: "Carga Masiva", path: "/mssql/loader", icon: Upload },
    ],
  },
  {
    name: "MySQL",
    path: "/mysql",
    color: "mysql",
    icon: Database,
    items: [
      { title: "Clientes", path: "/mysql/clientes", icon: Users },
      { title: "Productos", path: "/mysql/productos", icon: Package },
      { title: "Órdenes", path: "/mysql/ordenes", icon: ShoppingCart },
      { title: "Carga Masiva", path: "/mysql/loader", icon: Upload },
    ],
  },
  {
    name: "Supabase",
    path: "/supabase",
    color: "supabase",
    icon: Database,
    items: [
      { title: "Clientes", path: "/supabase/clientes", icon: Users },
      { title: "Productos", path: "/supabase/productos", icon: Package },
      { title: "Órdenes", path: "/supabase/ordenes", icon: ShoppingCart },
    ],
  },
  {
    name: "Neo4j",
    path: "/neo4j",
    color: "neo4j",
    icon: Database,
    items: [
      { title: "Clientes", path: "/neo4j/clientes", icon: Users },
      { title: "Productos", path: "/neo4j/productos", icon: Package },
      { title: "Órdenes", path: "/neo4j/ordenes", icon: ShoppingCart },
    ],
  },
];

export function AppSidebar() {
  const { state } = useSidebar();
  const location = useLocation();
  const isCollapsed = state === "collapsed";

  const isActive = (path: string) => location.pathname === path;

  // Show only the current database items when collapsed
  const getCurrentDb = () => {
    return databases.find(db => 
      db.items.some(() => location.pathname.startsWith(db.path))
    );
  };

  const displayDatabases = (isCollapsed 
    ? [(getCurrentDb() || databases[0])]
    : databases).filter((db): db is NonNullable<typeof db> => db !== undefined);

  return (
    <Sidebar collapsible="icon">
      <SidebarContent>
        {displayDatabases.map((db) => (
          <SidebarGroup key={db.name}>
            <SidebarGroupLabel className={`text-${db.color} font-semibold`}>
              {db.name}
            </SidebarGroupLabel>
            <SidebarGroupContent>
              <SidebarMenu>
                {db.items.map((item) => (
                  <SidebarMenuItem key={item.path}>
                    <SidebarMenuButton asChild isActive={isActive(item.path)}>
                      <NavLink to={item.path}>
                        <item.icon className="h-4 w-4" />
                        <span>{item.title}</span>
                      </NavLink>
                    </SidebarMenuButton>
                  </SidebarMenuItem>
                ))}
              </SidebarMenu>
            </SidebarGroupContent>
          </SidebarGroup>
        ))}
      </SidebarContent>
    </Sidebar>
  );
}
