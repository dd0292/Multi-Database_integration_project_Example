// Planned heterogeneities
// • Multiple codes per product (sku properties, altcode, mongocode)
// • Multiple currencies per order
// • Gender in mixed formats

CREATE CONSTRAINT cliente_id IF NOT EXISTS
FOR (c:Cliente) REQUIRE c.id IS UNIQUE;
CREATE CONSTRAINT producto_id IF NOT EXISTS
FOR (p:Producto) REQUIRE p.id IS UNIQUE;
CREATE INDEX orden_fecha IF NOT EXISTS FOR (o:Orden) ON (o.fecha);