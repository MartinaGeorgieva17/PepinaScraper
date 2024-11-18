import mysql.connector as mc
from PepinaScraper.read_config import read_db_config



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
                link VARCHAR(255) UNIQUE NOT NULL,
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

    # Добавя множество редове в таблицата
    def insert_rows(self, rows_data):
        sql = """
            INSERT IGNORE INTO shoes 
            (brand, price, color, sizes)
            VALUES (%s, %s, %s, %s)
            ON DUPLICATE KEY UPDATE price=VALUES(price), sizes=VALUES(sizes)
        """
        data = [(row['brand'], row['price'], row['color'], ",".join(row['sizes'])) for row in rows_data]
        self.check_connection()
        try:
            with self.conn.cursor() as cursor:
                cursor.executemany(sql, rows_data)
                self.conn.commit()
                print(f"Добавени са {cursor.rowcount} редове!")
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
        
        if not row_data.get('sizes'):
            print('Липсват размери за обувката, ще се добави "N/A"')
            row_data['sizes'] = ['N/A']  # Добавяме 'N/A' ако липсват размери

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