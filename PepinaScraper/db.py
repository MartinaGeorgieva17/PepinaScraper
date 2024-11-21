import re
import requests
import os
from bs4 import BeautifulSoup
import sqlite3
import logging
from PyQt6 import QtWidgets as qtw
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QDoubleValidator

# Logging setup
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

# Database Handling Class
class DB:
    def __init__(self, db_path='products.db'):
        self.db_path = db_path
        self.conn = None
        self.connect()
        self.create_table()

    def connect(self):
        """Connect to the SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            logging.info(f"Connected to database: {self.db_path}")
        except sqlite3.Error as e:
            logging.error(f"Database connection failed: {e}")

    def create_table(self):
        """Create products table if it doesn't exist."""
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
                logging.error(f"Error creating table: {e}")

    def insert_row(self, product):
        """Insert product data into the database."""
        if self.conn:
            try:
                cursor = self.conn.cursor()
                cursor.execute("INSERT INTO products (brand, price, color, size) VALUES (?, ?, ?, ?)",
                               (product['brand'], product['price'], product['color'], product['size']))
                self.conn.commit()
                logging.info(f"Inserted product: {product}")
            except sqlite3.Error as e:
                logging.error(f"Error inserting product: {e}")

    def select_all_data(self, order_by='id'):
        """Select all data from products."""
        if self.conn:
            cursor = self.conn.cursor()
            query = f"SELECT * FROM products ORDER BY {order_by}"
            cursor.execute(query)
            return cursor.fetchall()
        return []

    def select_data_by_size(self, size):
        """Select data by shoe size."""
        if self.conn:
            cursor = self.conn.cursor()
            cursor.execute("SELECT * FROM products WHERE size = ?", (size,))
            return cursor.fetchall()
        return []

    def close(self):
        """Close the database connection."""
        if self.conn:
            self.conn.close()
            self.conn = None
            logging.info("Database connection closed.")

# Web Scraper Class for Pepina
class ProductScraper:
    def __init__(self, base_url):
        self.base_url = base_url
        self.products = []
        self.output_dir = './data'
        self.filename = 'obuvki.html'
        self.file_path = os.path.join(self.output_dir, self.filename)

    def save_html(self, content):
        """Save the HTML content to a file."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
        with open(self.file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def get_html(self):
        """Fetch HTML content of the page."""
        headers = {"User-Agent": "Mozilla/5.0"}
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                print("Loading content from local file.")
                return f.read()
        else:
            try:
                print(f"Sending request to {self.base_url}")
                response = requests.get(self.base_url, headers=headers)
                response.raise_for_status()
                self.save_html(response.text)
                return response.text
            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
                return None

    def parse_products(self, html):
        """Parse product data from the page."""
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
        """Run the scraper to fetch and parse products."""
        html = self.get_html()
        if html:
            self.parse_products(html)

# PyQt6 GUI for Displaying and Interacting with Data
class DataTable(qtw.QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = DB()  
        if not self.db.conn:
            qtw.QMessageBox.critical(None, "Database Error", "Failed to connect to the database.")
            return
        self.column_names = ["Brand", "Price", "Color"]
        self.setup_table()

    def setup_table(self):
        """Setup the table with data."""
        self.setColumnCount(len(self.column_names))
        self.setHorizontalHeaderLabels(self.column_names)
        self.resizeColumnsToContents()
        self.setSortingEnabled(True)
        self.update_table(self.db.select_all_data())

    def update_table(self, data):
        """Update the table with new data."""
        self.setRowCount(0)
        for row_num, row_data in enumerate(data):
            self.insertRow(row_num)
            for col_num, value in enumerate(row_data):
                self.setItem(row_num, col_num, qtw.QTableWidgetItem(str(value)))

    def filter_by_size(self, size):
        """Filter data by size."""
        try:
            size = float(size)
            data = self.db.select_data_by_size(size)
            self.update_table(data)
        except ValueError:
            qtw.QMessageBox.warning(None, "Invalid Input", "Please enter a valid size.")

    def filter_by_price(self, max_price):
        """Filter data by maximum price."""
        try:
            max_price = float(max_price)
            data = [product for product in self.db.select_all_data() if product[1] <= max_price]
            self.update_table(data)
        except ValueError:
            qtw.QMessageBox.warning(None, "Invalid Input", "Please enter a valid price.")

# Main Window for the Application
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
