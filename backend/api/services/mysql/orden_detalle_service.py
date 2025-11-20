from api.database.mysql_connection import get_mysql_connection

class OrdenDetalleMySQLService:

    def insert_rows(self, rows: list[dict]):
        connection = get_mysql_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO OrdenDetalle (orden_id, producto_id, cantidad, precio_unit)
        VALUES (%s, %s, %s, %s)
        """

        data = [
            (
                r["orden_id"],
                r["producto_id"],
                r["cantidad"],
                r["precio_unit"]  # string, comas y puntos permitidos
            )
            for r in rows
        ]

        try:
            cursor.executemany(query, data)
            connection.commit()
            return cursor.rowcount
        except Exception as e:
            connection.rollback()
            raise e
        finally:
            cursor.close()
            connection.close()
