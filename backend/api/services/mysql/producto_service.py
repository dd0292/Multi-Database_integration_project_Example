from api.database.mysql_connection import get_mysql_connection

class ProductoMySQLService:

    def insert_rows(self, rows: list[dict]):
        connection = get_mysql_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO Producto (codigo_alt, nombre, categoria)
        VALUES (%s, %s, %s)
        """

        data = [
            (
                r["codigo_alt"],
                r["nombre"],
                r["categoria"]
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
