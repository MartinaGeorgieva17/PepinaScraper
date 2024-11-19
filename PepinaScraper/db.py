import json

from PyQt6.QtSql import QSqlDatabase
import mysql.connector as mc

from PepinaScraper.read_config import read_db_config
from .read_config import read_db_config



# Свързване с базата данни
class DB():
    def __init__(self):
        mysql_config = read_db_config('config.ini', 'mysql')
        try:
            self.conn = mc.connect(**mysql_config)
            print("Успешно свързване към базата с данни!")
        except mc.Error as e:
            print(f"Грешка при свързване с Mysql: {e}")
            raise Exception("Неуспешно свързване с базата данни!")

        # Register QSqlDatabase connection to be used with QSqlTableModel
        self.qsql_conn = self._setup_qt_database(mysql_config)


    def _setup_qt_database(self, config):
        """
        Creates and registers a QSqlDatabase connection
        """
        db = QSqlDatabase.addDatabase("QMYSQL", "qt_connection")
        db.setHostName(config['host'])
        db.setDatabaseName(config['database'])
        db.setUserName(config['user'])
        db.setPassword(config['password'])
        if not db.open():
            print(f"Грешка при отваряне на QSqlDatabase: {db.lastError().text()}")
            raise Exception("QSqlDatabase не можа да се свърже.")
        print("Успешно свързване към базата чрез QSqlDatabase!")
        return db


    # Проверява и възстановява връзката към базата данни
    def check_connection(self):
        if not self.conn.is_connected():
            try:
                self.conn.reconnect(attempts=3, delay=2)
                print("Възстановна връзка към базата данни")
            except mc.Error as e:
                print(f"Неуспешно възстановяване на връзката: {e}")
                raise  # Генерираме грешка, която можем да хванем

    # Създаваме таблица "shoes", ако не съществува
    def create_shoes_table(self):
        sql = """
            CREATE TABLE IF NOT EXISTS shoes(
                id INT AUTO_INCREMENT PRIMARY KEY,
                brand VARCHAR(100) NOT NULL,
                price DECIMAL(10,2) NOT NULL,
                color VARCHAR(50) NOT NULL,
                sizes VARCHAR(255) NOT NULL,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
                CONSTRAINT brand_color_size UNIQUE (brand, color, sizes)
            );
        """
        self.check_connection()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
                self.conn.commit()
                print(f'Таблицата с обувки е създадена!')
        except mc.Error as e:
            print(f"Грешка при създаване на таблица: {e}")
            self.conn.rollback()

    # Изтриваме таблицата "shoes", ако съществува
    def drop_shoes_table(self):
        sql = "DROP TABLE IF EXISTS shoes;"
        self.check_connection()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
                self.conn.commit()
                print(f"Таблицата 'shoes' е изтрита успешно!")
        except mc.Error as e:
            print(f"Грешка при изтриване на таблицата: {e}")
            self.conn.rollback()

    def insert_rows(self, rows_data):
        '''# Добавя множество редове в таблицата'''
        sql = """
            INSERT INTO shoes
            (brand, price, color, sizes)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE price=VALUES(price), sizes=VALUES(sizes)
        """
        self.check_connection()
        try:
            with self.conn.cursor() as cursor:
                # Подготвяме данните за вмъкване, като преобразуваме 'sizes' списъка в CSV стринг
                data = [
                    (row['brand'], row['price'], row['color'], ",".join(map(str, row['sizes'])))
                    for row in rows_data
                ]
                cursor.executemany(sql, data)  # Вмъкваме всички редове с една заявка
            self.conn.commit()
            print(f"Добавени са {len(rows_data)} редове!")
        except mc.Error as e:
            print(f"Грешка при вмъкване на редове: {e}!")
            self.conn.rollback()


    # Добавя един ред след валидиране
    def insert_row(self, row_data):
        if not row_data.get('brand') or not row_data.get('color'):
            print("Липсва информация за бранда или цвета")
            return

        if row_data.get('price', 0) >= 1000:
            print("Цена над 1000 лева не може да бъде добавена!")
            return

        sql = """
            INSERT IGNORE INTO shoes
            (brand, price, color, sizes)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE price=VALUES(price), sizes=VALUES(sizes)
        """
        self.check_connection()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, tuple(row_data.values()))
                self.conn.commit()
                print(f"Добавен ред: {row_data}!")
        except mc.Error as e:
            print(f"Грешка при вмъкване на редове: {e}!")
            self.conn.rollback()

    # Извлича всички данни от таблицата
    def select_all_data(self):
        sql = "SELECT id, brand, price, color FROM shoes"
        self.check_connection()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                return result if result else []
        except mc.Error as e:
            print(f"Грешка при извличане на данни: {e}")
            return []

    # Извлича данни от таблицата със сортиране
    def select_all_data_sorted(self, column="price", ascending=True):
        valid_columns = {"price", "brand", "color", "sizes"}  # Разрешение за сортиране
        if column not in valid_columns:
            raise ValueError(f"Невалидна колона за сортиране: {column}")

        order = 'ASC' if ascending else 'DESC'
        sql = f"SELECT id, brand, price, color, sizes FROM shoes ORDER BY {column} {order}"
        self.check_connection()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchall()
                return result if result else []
        except mc.Error as e:
            print(f"Грешка при сортиране: {e}")
            return []

    # Филтрира данни по размер
    def select_data_by_size(self, size):
        sql = "SELECT id, brand, price, color, sizes FROM shoes WHERE FIND_IN_SET(%s, sizes) > 0;"
        self.check_connection()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql, (size,))
                result = cursor.fetchall()
                return result if result else []
        except mc.Error as e:
            print(f"Грешка при извличане на данни по размер: {e}")
            return []

    # Извлича последната дата на обновяване
    def get_last_updated_date(self):
        sql = 'SELECT MAX(updated_at) FROM shoes;'
        self.check_connection()
        try:
            with self.conn.cursor() as cursor:
                cursor.execute(sql)
                result = cursor.fetchone()
                return result[0] if result else None
        except mc.Error as e:
            print(f"Грешка при извличане на последната дата на обновяване: {e}.")
            return None

if __name__ == '__main__':
    db = DB()
    db.create_shoes_table()

    # db.get_column_names()
    res = db.get_last_updated_date()
    print(res)