db.createCollection("clientes", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["nombre", "pais", "genero", "creado"],
      properties: {
        nombre: { bsonType: "string" },
        email: { bsonType: "string" },
        genero: { enum: ["Masculino", "Femenino", "Otro"], description: "gender" },
        pais: { bsonType: "string" },
        preferencias: {
          bsonType: "object",
          properties: {
            canal: { bsonType: "array", items: { bsonType: "string" } }
          }
        },
        creado: { bsonType: "date" }
      }
    }
  }
});
db.createCollection("productos", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["codigo_mongo", "nombre", "categoria"],
      properties: {
        codigo_mongo: { bsonType: "string" },
        nombre: { bsonType: "string" },
        categoria: { bsonType: "string" },
        equivalencias: {
          bsonType: "object",
          properties: {
            sku: { bsonType: ["string", "null"] },
            codigo_alt: { bsonType: ["string", "null"] }
          }
        }
      }
    }
  }
});
db.createCollection("ordenes", {
  validator: {
    $jsonSchema: {
      bsonType: "object",
      required: ["cliente_id", "fecha", "moneda", "total", "items"],
      properties: {
        cliente_id: { bsonType: "objectId" },
        fecha: { bsonType: "date" },
        canal: { bsonType: "string" },
        moneda: { bsonType: "string" },
        total: { bsonType: "int" },
        total_usd: { bsonType: ["double", "null"] },
        items: {
          bsonType: "array",
          items: {
            bsonType: "object",
            required: ["producto_id", "cantidad", "precio_unit"],
            properties: {
              producto_id: { bsonType: "objectId" },
              cantidad: { bsonType: "int" },
              precio_unit: { bsonType: "int" }
            }
          }
        },
        metadatos: { bsonType: "object" }
      }
    }
  }
});


//Planned heterogeneities
//• Amounts in CRC integers (no decimals).
//• Equivalents field for linking to other sources (sometimes incomplete).
//• Gender with a third value of 'Other'.
//• Nested structure (arrays of items).