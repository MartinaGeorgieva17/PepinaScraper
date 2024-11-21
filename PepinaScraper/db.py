#Код предназначен за управление на базата данни и свързване към нея. 
# В него има два различни подхода - с MySQL и SQLite.

import mysql.connector
import logging
import configparser
from PyQt6 import QtWidgets as qtw
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator

# Настройка на логер
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


class DB:
    def __init__(self, config_file='config.ini'):
        self.conn = None
        try:
            self.config = self.load_config(config_file)
            self.connect()
            self.create_table()
        except Exception as e:
            logging.error(f"Error initializing DB: {e}")

    def load_config(self, config_file):
        """Зарежда конфигурацията от INI файл."""
        config = configparser.ConfigParser()
        config.read(config_file)
        
        if not config.sections():
            logging.critical(f"Config file '{config_file}' is empty or unreadable.")
            raise FileNotFoundError(f"Config file '{config_file}' could not be read or is empty.")
        
        if 'mysql' not in config:
            logging.critical(f"Missing 'mysql' section in config file: {config_file}")
            raise KeyError("'mysql' section is missing in the config file.")
        
        logging.info(f"Config loaded from {config_file}")
        return config['mysql']

    def connect(self):
        """Свързване с MySQL базата данни"""
        try:
            self.conn = mysql.connector.connect(
                host=self.config['HOST'],
                user=self.config['USER'],
                password=self.config['PASSWORD'],
                database=self.config['DATABASE'],
                port=int(self.config.get('PORT', 3306))  # По подразбиране 3306
            )
            logging.info(f"Successfully connected to MySQL database: {self.config['DATABASE']}")
        except mysql.connector.Error as e:
            logging.error(f"Error connecting to MySQL database: {e}")
            self.conn = None

    def create_table(self):
        """Създаване на таблицата `products`, ако не съществува"""
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS products (
                        id INT AUTO_INCREMENT PRIMARY KEY,
                        brand VARCHAR(255),
                        price DECIMAL(10, 2),
                        color VARCHAR(50),
                        size DECIMAL(5, 2)
                    )
                ''')
                self.conn.commit()
                logging.info("Table 'products' is ready.")
            except mysql.connector.Error as e:
                logging.error(f"Error creating table: {e}")

    def insert_row(self, product):
        """Метод за вмъкване на продукт в базата данни"""
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute(
                    "INSERT INTO products (brand, price, color, size) VALUES (%s, %s, %s, %s)",
                    (product['brand'], product['price'], product['color'], product['size'])
                )
                self.conn.commit()
                logging.info(f"Inserted product: {product}")
            except mysql.connector.Error as e:
                logging.error(f"Error inserting product: {e}")

    def select_all_data(self, order_by='id'):
        """Извличане на всички данни от базата данни"""
        if self.conn:
            try:
                cursor = self.conn.cursor()
                query = f"SELECT * FROM products ORDER BY {order_by}"
                cursor.execute(query)
                return cursor.fetchall()
            except mysql.connector.Error as e:
                logging.error(f"Error fetching all data: {e}")
                return []
        return []

    def close(self):
        """Затваряне на връзката с базата данни"""
        if self.conn:
            self.conn.close()
            self.conn = None
            logging.info("Database connection closed.")

    def is_connected(self):
        """Проверка на състоянието на връзката с базата"""
        return self.conn is not None


# GUI част за добавяне на продукт
class DataTable(qtw.QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        try:
            self.db = DB()  # Връзка с базата данни
            if not self.db.is_connected():
                raise ConnectionError("Провалена връзка с базата данни.")
        except Exception as e:
            qtw.QMessageBox.critical(None, "Грешка на базата данни!", str(e))
            self.db = None
            return

        self.column_names = ["ID", "Brand", "Price", "Color", "Size"]
        self.setup_table()

    def setup_table(self):
        """Настройване на таблицата."""
        self.setColumnCount(len(self.column_names))
        self.setHorizontalHeaderLabels(self.column_names)
        self.resizeColumnsToContents()
        self.setSortingEnabled(True)
        if self.db:
            self.update_table(self.db.select_all_data())

    def update_table(self, data):
        """Обновяване на таблицата с нови данни."""
        self.setRowCount(0)
        for row_num, row_data in enumerate(data):
            self.insertRow(row_num)
            for col_num, value in enumerate(row_data):
                self.setItem(row_num, col_num, qtw.QTableWidgetItem(str(value)))

    def add_product(self, brand, price, color, size):
        """Добавяне на продукт в базата данни"""
        if self.db:
            product = {
                'brand': brand,
                'price': price,
                'color': color,
                'size': size
            }
            self.db.insert_row(product)
            self.update_table(self.db.select_all_data())

# Главен прозорец на приложението
class MainWindow(qtw.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Pepina Crawler')
        self.setup_gui()

    def setup_gui(self):
        layout = qtw.QVBoxLayout()

        self.data_table = DataTable()
        layout.addWidget(self.data_table)

        self.add_button = qtw.QPushButton('Добави продукт')
        self.add_button.clicked.connect(self.on_add_product)
        layout.addWidget(self.add_button)

        self.setLayout(layout)

    def on_add_product(self):
        """Тестово добавяне на продукт"""
        brand = 'Nike'
        price = 99.99
        color = 'Red'
        size = 42.5
        self.data_table.add_product(brand, price, color, size)


if __name__ == '__main__':
    app = qtw.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()



#Вариант 2 с sqlite: Зарежда нов прозорец с бутони и опция за филтриране, зарежда нов файл products.db

# import sqlite3
# import logging
# from PyQt6 import QtWidgets as qtw
# from PyQt6.QtCore import Qt
# from PyQt6.QtGui import QDoubleValidator

# # Настройка на логер
# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')


# class DB:
#     def __init__(self, db_path='products.db'):
#         self.db_path = db_path  # Път към базата данни
#         self.conn = None
#         self.connect()
#         self.create_table()

#     def __enter__(self):
#         self.connect()
#         return self

#     def __exit__(self, exc_type, exc_value, traceback):
#         self.close()

#     def connect(self):
#         """Свързване с базата данни"""
#         try:
#             self.conn = sqlite3.connect(self.db_path)
#             logging.info(f"Successfully connected to {self.db_path}")
#         except sqlite3.Error as e:
#             logging.error(f"Error connecting to database: {e}")
#             self.conn = None

#     def create_table(self):
#         """Създаване на таблицата `products`, ако не съществува"""
#         if self.conn:
#             try:
#                 cursor = self.conn.cursor()
#                 cursor.execute('''
#                     CREATE TABLE IF NOT EXISTS products (
#                         id INTEGER PRIMARY KEY AUTOINCREMENT,
#                         brand TEXT,
#                         price REAL,
#                         color TEXT,
#                         size REAL
#                     )
#                 ''')
#                 self.conn.commit()
#                 logging.info("Table 'products' is ready.")
#             except sqlite3.Error as e:
#                 logging.error(f"Error creating table: {e}")

#     def insert_row(self, product):
#         """Метод за вмъкване на продукт в базата данни"""
#         if self.conn:
#             try:
#                 cursor = self.conn.cursor()
#                 cursor.execute(
#                     "INSERT INTO products (brand, price, color, size) VALUES (?, ?, ?, ?)",
#                     (product['brand'], product['price'], product['color'], product['size'])
#                 )
#                 self.conn.commit()
#                 logging.info(f"Inserted product: {product}")
#             except sqlite3.Error as e:
#                 logging.error(f"Error inserting product: {e}")

#     def select_all_data(self, order_by='id'):
#         """Извличане на всички данни от базата данни"""
#         if self.conn:
#             try:
#                 cursor = self.conn.cursor()
#                 query = f"SELECT * FROM products ORDER BY {order_by}"
#                 cursor.execute(query)
#                 return cursor.fetchall()
#             except sqlite3.Error as e:
#                 logging.error(f"Error fetching all data: {e}")
#                 return []
#         return []

#     def select_data_by_size(self, size):
#         """Извличане на данни по размер (например за обувки)"""
#         if self.conn:
#             try:
#                 cursor = self.conn.cursor()
#                 cursor.execute("SELECT * FROM products WHERE size = ?", (size,))
#                 return cursor.fetchall()
#             except sqlite3.Error as e:
#                 logging.error(f"Error fetching data by size: {e}")
#                 return []
#         return []

#     def close(self):
#         """Затваряне на връзката с базата данни"""
#         if self.conn:
#             self.conn.close()
#             self.conn = None
#             logging.info("Database connection closed.")

#     def is_connected(self):
#         """Проверка на състоянието на връзката с базата"""
#         return self.conn is not None


# # Примерен GUI компонент за филтриране по размер
# class DataTable(qtw.QTableWidget):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.db = DB()  # Връзка с базата данни
#         if not self.db.is_connected():
#             qtw.QMessageBox.critical(None, "Грешка на базата данни!", "Провалена връзка с базата данни.")
#             return

#         self.column_names = ["ID", "Brand", "Price", "Color", "Size"]
#         self.setup_table()

#     def setup_table(self):
#         """Настройване на таблицата."""
#         self.setColumnCount(len(self.column_names))
#         self.setHorizontalHeaderLabels(self.column_names)
#         self.resizeColumnsToContents()
#         self.setSortingEnabled(True)
#         self.update_table(self.db.select_all_data())

#     def update_table(self, data):
#         """Обновяване на таблицата с нови данни."""
#         self.setRowCount(0)
#         for row_num, row_data in enumerate(data):
#             self.insertRow(row_num)
#             for col_num, value in enumerate(row_data):
#                 self.setItem(row_num, col_num, qtw.QTableWidgetItem(str(value)))

#     def filter_by_size(self, size):
#         """Филтриране на данните по размер."""
#         try:
#             size = float(size)  # Преобразуване на стойността в число
#             data = self.db.select_data_by_size(size)
#             if data:
#                 self.update_table(data)
#             else:
#                 qtw.QMessageBox.warning(None, "Няма резултати", f"Няма продукти за размер {size}.")
#         except ValueError:
#             qtw.QMessageBox.warning(None, "Грешка", "Моля, въведете валиден размер.")


# # Главен клас за работа с филтриране
# class TableViewWidget(qtw.QWidget):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.setup_gui()

#     def setup_gui(self):
#         layout = qtw.QVBoxLayout()

#         self.tableView = DataTable()
#         layout.addWidget(self.tableView)

#         self.filter_size_input = qtw.QLineEdit(self)
#         self.filter_size_input.setPlaceholderText('Въведете размера на обувките (напр., "38")')
#         validator = QDoubleValidator(0.0, 50.0, 2)  # Валидация за валиден размер
#         self.filter_size_input.setValidator(validator)
#         self.filter_size_input.textChanged.connect(self.on_filter_size_changed)
#         layout.addWidget(self.filter_size_input)

#         self.setLayout(layout)

#     def on_filter_size_changed(self, text):
#         """Обработване на промени в текстовото поле за размер."""
#         self.tableView.filter_by_size(text)


# # Главен прозорец на приложението
# class MainWindow(qtw.QMainWindow):
#     def __init__(self, *args, **kwargs):
#         super().__init__(*args, **kwargs)
#         self.setWindowTitle('Pepina Crawler')
#         self.setup_gui()

#     def setup_gui(self):
#         layout = qtw.QVBoxLayout()

#         self.tableViewWidget = TableViewWidget()
#         layout.addWidget(self.tableViewWidget)

#         mainWidget = qtw.QWidget()
#         mainWidget.setLayout(layout)
#         self.setCentralWidget(mainWidget)


# if __name__ == '__main__':
#     app = qtw.QApplication([])
#     window = MainWindow()
#     window.show()
#     app.exec()
