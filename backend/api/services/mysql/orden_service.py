from api.database.mysql_connection import get_mysql_connection

class OrdenMySQLService:

    def insert_rows(self, rows: list[dict]):
        connection = get_mysql_connection()
        cursor = connection.cursor()

        query = """
        INSERT INTO Orden (cliente_id, fecha, canal, moneda, total)
        VALUES (%s, %s, %s, %s, %s)
        """

        data = [
            (
                r["cliente_id"],
                r["fecha"],     # 'YYYY-MM-DD HH:MM:SS' (string)
                r["canal"],
                r["moneda"],
                r["total"]      # string, puede tener comas
            )
            for r in rows
        ]

        try:
            cursor.executemany(query, data)
            connection.commit()
            return cursor.rowcount
        except Exception as e:
            print("Error inserting Orden rows:", e)
            connection.rollback()
            raise e
        finally:
            cursor.close()
            connection.close()
