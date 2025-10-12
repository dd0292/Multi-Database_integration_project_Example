import { useState } from "react";
import { useQuery } from "@tanstack/react-query";
import { Plus, Network, ShoppingCart } from "lucide-react";
import { Button } from "../../components/ui/button";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "../../components/ui/card";
import { Badge } from "../../components/ui/badge";
import api from "../../services/api";

const Neo4jOrdenes = () => {
  const [page] = useState(1);
  const limit = 20;

  const { data, isLoading } = useQuery({
    queryKey: ["neo4j-ordenes", page],
    queryFn: async () => {
      const response = await api.get<{ data: any[]; total: number }>(
        `/neo4j/ordenes?page=${page}&limit=${limit}`
      );
      return response.data;
    },
  });

  const getChannelColor = (canal: string) => {
    switch (canal) {
      case "WEB": return "bg-blue-100 text-blue-800";
      case "TIENDA": return "bg-green-100 text-green-800";
      case "APP": return "bg-purple-100 text-purple-800";
      default: return "bg-gray-100 text-gray-800";
    }
  };

  return (
    <div className="max-w-7xl mx-auto">
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-neo4j">Neo4j Órdenes</h1>
          <p className="text-muted-foreground mt-1">Manage order relationships in Neo4j graph</p>
        </div>
        <Button className="bg-neo4j hover:bg-neo4j-dark">
          <Plus className="h-4 w-4 mr-2" />
          New Order
        </Button>
      </div>

      <Card className="border-l-4 border-neo4j">
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Network className="h-5 w-5" />
            Order Graph
          </CardTitle>
          <CardDescription>{data?.total || 0} total orders</CardDescription>
        </CardHeader>
        <CardContent>
          {isLoading ? (
            <div className="text-center py-8 text-muted-foreground">Loading orders...</div>
          ) : data?.data && data.data.length > 0 ? (
            <div className="space-y-4">
              {data.data.map((orden: any) => (
                <Card key={orden.orden.id} className="p-5">
                  <div className="flex items-start justify-between mb-4">
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-2">
                        <ShoppingCart className="h-5 w-5 text-neo4j" />
                        <h3 className="font-semibold text-lg">Order {orden.orden.id}</h3>
                        <Badge className={getChannelColor(orden.orden.canal)}>
                          {orden.orden.canal}
                        </Badge>
                      </div>
                      <p className="text-sm text-muted-foreground mb-2">
                        Cliente: {orden.cliente.nombre}
                      </p>
                      <p className="text-sm text-muted-foreground">
                        {new Date(orden.orden.fecha).toLocaleString()}
                      </p>
                    </div>
                    <div className="text-right">
                      <div className="text-2xl font-bold text-neo4j">
                        ${orden.orden.total.toFixed(2)}
                      </div>
                      <div className="text-xs text-muted-foreground">{orden.orden.moneda}</div>
                    </div>
                  </div>
                  
                  <div className="border-t pt-3 flex items-center gap-2 text-sm text-muted-foreground">
                    <Network className="h-4 w-4" />
                    <span>{orden.items.length} product relationships</span>
                  </div>
                </Card>
              ))}
            </div>
          ) : (
            <div className="text-center py-8 text-muted-foreground">
              No orders found. Create your first order relationship!
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
};

export default Neo4jOrdenes;
