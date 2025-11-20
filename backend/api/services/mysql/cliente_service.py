from api.database.mysql_connection import get_mysql_connection

class ClienteMySQLService:

    def insert_rows(self, rows: list[dict]):
        connection = get_mysql_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO Cliente (nombre, correo, genero, pais, created_at)
        VALUES (%s, %s, %s, %s, %s)
        """

        data = [
            (
                r.get("nombre"),
                r.get("correo"),
                r.get("genero", "M"),
                r.get("pais"),
                r.get("created_at")  # 'YYYY-MM-DD'
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
