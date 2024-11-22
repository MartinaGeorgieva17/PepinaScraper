import re
import requests
import os
from bs4 import BeautifulSoup
import sqlite3
import logging
from PyQt6 import QtWidgets as qtw
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator

#Създава и управлява SQLite база данни -- > products.db
#Създаваме клас Db и ProductScraper, DataTable, MainWindow
#Графичен интерфейс с PyQt6 -- > DataTable, MainWindow


# Настройки за логване - позволява прихващане на грешки 
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Клас за управление на базата данни
class DB:
    def __init__(self, db_path='products.db'):
        self.db_path = db_path
        self.conn = None
        self.connect()
        self.create_table()

    def connect(self):
        """Свързване с базата данни SQLite."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logging.info(f"Свързано с базата данни: {self.db_path}")
        except sqlite3.Error as e:
            logging.error(f"Неуспешно свързване с базата данни: {e}")

    def create_table(self):
        """Създаване на таблица `products`, ако не съществува."""
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        brand TEXT,
                        price REAL,
                        color TEXT,
                        size REAL
                    )
                ''')
                self.conn.commit()
            except sqlite3.Error as e:
                logging.error(f"Грешка при създаването на таблицата: {e}")

    def insert_row(self, product):
        """Добавяне на данни за продукт в базата данни."""
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute("INSERT INTO products (brand, price, color, size) VALUES (?, ?, ?, ?)",
                               (product['brand'], product['price'], product['color'], product['size']))
                self.conn.commit()
                logging.info(f"Добавен продукт: {product}")
            except sqlite3.Error as e:
                logging.error(f"Грешка при добавяне на продукт: {e}")

    def select_all_data(self, order_by='id'):
        """Извличане на всички данни от таблицата `products`."""
        if self.conn:
            cursor = self.conn.cursor()
            query = f"SELECT * FROM products ORDER BY {order_by}"
            cursor.execute(query)
            return cursor.fetchall()
        return []

    def select_data_by_size(self, size):
        """Извличане на данни по размер на обувките."""
        if self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM products WHERE size = ?", (size,))
            return cursor.fetchall()
        return []

    def close(self):
        """Затваряне на връзката към базата данни."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logging.info("Връзката с базата данни е затворена.")

# Клас за уеб скрейпинг на сайта Pepina
class ProductScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.products = []
        self.output_dir = './data'
        self.filename = 'obuvki.html'
        self.file_path = os.path.join(self.output_dir, self.filename)

    def save_html(self, content):
        """Запазване на HTML съдържанието във файл."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        with open(self.file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def get_html(self):
        """Извличане на HTML съдържание от страницата."""
        headers = {"User-Agent": "Mozilla/5.0"}
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                print("Зареждане на съдържание от локален файл.")
                return f.read()
        else:
            try:
                print(f"Изпращане на заявка до {self.base_url}")
                response = requests.get(self.base_url, headers=headers)
                response.raise_for_status()
                self.save_html(response.text)
                return response.text
            except requests.exceptions.RequestException as e:
                print(f"Грешка при заявката: {e}")
                return None

    def parse_products(self, html):
        """Парсване на данни за продукти от страницата."""
        soup = BeautifulSoup(html, 'html.parser')
        product_containers = soup.find_all("a", class_="product-link")

        for container in product_containers:
            product_data = {}
            product_data["brand"] = container.find("div", class_="brand").text.strip()
            product_data["price"] = float(container.find("div", class_="regular-price").text.strip().replace("лв.", "").strip())
            product_data["color"] = container.find("div", class_="color").text.strip() if container.find("div", class_="color") else "Unknown"
            product_data["size"] = float(container.find("div", class_="size").text.strip()) if container.find("div", class_="size") else 0.0
            self.products.append(product_data)

    def run(self):
        """Изпълнение на скрейпера за извличане и парсване на данни за продукти."""
        html = self.get_html()
        if html:
            self.parse_products(html)

# PyQt6 GUI за показване и взаимодействие с данни
class DataTable(qtw.QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = DB()  
        if not self.db.conn:
            qtw.QMessageBox.critical(None, "Грешка с базата данни", "Неуспешно свързване с базата данни.")
            return
        self.column_names = ["Марка", "Цена", "Цвят"]
        self.setup_table()

    def setup_table(self):
        """Конфигурация на таблицата с данни."""
        self.setColumnCount(len(self.column_names))
        self.setHorizontalHeaderLabels(self.column_names)
        self.resizeColumnsToContents()
        self.setSortingEnabled(True)
        self.update_table(self.db.select_all_data())

    def update_table(self, data):
        """Актуализиране на таблицата с нови данни."""
        self.setRowCount(0)
        for row_num, row_data in enumerate(data):
            self.insertRow(row_num)
            for col_num, value in enumerate(row_data):
                self.setItem(row_num, col_num, qtw.QTableWidgetItem(str(value)))

    def filter_by_size(self, size):
        """Филтриране на данни по размер."""
        try:
            size = float(size)
            data = self.db.select_data_by_size(size)
            self.update_table(data)
        except ValueError:
            qtw.QMessageBox.warning(None, "Невалиден вход", "Моля, въведете валиден размер.")

    def filter_by_price(self, max_price):
        """Филтриране на данни по максимална цена."""
        try:
            max_price = float(max_price)
            data = [product for product in self.db.select_all_data() if product[1] <= max_price]
            self.update_table(data)
        except ValueError:
            qtw.QMessageBox.warning(None, "Невалиден вход", "Моля, въведете валидна цена.")

# Главен прозорец на приложението
class MainWindow(qtw.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Pepina Scraper")
        self.setup_gui()

    def setup_gui(self):
        layout = qtw.QVBoxLayout()
        self.tableView = DataTable()
        layout.addWidget(self.tableView)
        mainWidget = qtw.QWidget()
        mainWidget.setLayout(layout)
        self.setCentralWidget(mainWidget)

if __name__ == '__main__':
    app = qtw.QApplication([])
    window = MainWindow()
    window.show()
    app.exec()
