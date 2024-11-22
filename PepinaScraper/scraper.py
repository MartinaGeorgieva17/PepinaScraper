import sqlite3
import os
import requests
from bs4 import BeautifulSoup


#Scraper - събира информацията за продукти
# инициализира създаването на обект ProductScraper 
#Изтегля Html --> анализира продуктите (линкове, марка, цена, размер)
#Записване в база данни SQL--> Създава таблица "products" -->записва данните по колони
#Отпечатва резултатите 


class ProductScraper:
    def __init__(self, base_url, search_term):
        # Инициализация на основния URL и термина за търсене
        # Инициализира създаването на обект ProductScraper 
        self.base_url = base_url
        self.search_term = search_term
        self.products = []  # Списък за съхранение на намерените продукти
        self.output_dir = './data'  # Директория за съхранение на HTML файлове
        self.filename = f'{search_term}.html'  # Име на файла за кеширане
        self.file_path = os.path.join(self.output_dir, self.filename)  # Пълен път до файла

    def save_html(self, content):
        """Записва HTML съдържание в локален файл."""
        if not os.path.exists(self.output_dir):  # Проверява дали директорията съществува
            os.makedirs(self.output_dir)

        with open(self.file_path, 'w', encoding='utf-8') as file:
            file.write(content)  # Записва HTML съдържанието

    def get_html(self, url):
        """Изтегля HTML от уебсайта или зарежда кеширан файл."""
        headers = {"User-Agent": "Mozilla/5.0"}  # Заглавия за заявката
        if os.path.exists(self.file_path):  # Проверява дали файлът вече съществува
            with open(self.file_path, "r", encoding="utf-8") as f:
                print("Зареждане на съдържание от локалния файл.")
                return f.read()  # Връща съдържанието от файла
        else:
            try:
                print(f"Изпращане на заявка към {url}")
                response = requests.get(url, headers=headers)
                response.raise_for_status()  # Проверява за грешки в заявката
                self.save_html(response.text)  # Запазва HTML съдържанието
                return response.text
            except requests.exceptions.RequestException as e:
                print(f"Грешка при заявката: {e}")
                return None

    def parse_products(self, html):
        """Парсира продуктите от HTML съдържанието."""
        soup = BeautifulSoup(html, 'html.parser')

        # Намира всички контейнери за продукти
        product_containers = soup.find_all("a", class_="product-link")
        if not product_containers:
            print("Няма намерени продукти на тази страница.")
            return

        for container in product_containers:
            product_data = {}

            # Извлича линк към продукта
            link = container.get('href', '')
            product_data["link"] = f"https://pepina.bg{link}" if link else None

            # Извлича марката на продукта
            brand_tag = container.find("div", class_="brand")
            product_data["brand"] = brand_tag.text.strip() if brand_tag else "Неизвестна марка"

            # Извлича заглавието на продукта
            title_tag = container.find("div", class_="title")
            product_data["title"] = title_tag.text.strip() if title_tag else "Без заглавие"

            # Извлича цената на продукта
            price_tag = container.find("div", class_="regular-price")
            if price_tag:
                price_text = price_tag.text.strip()
                try:
                    price = float(price_text.replace("лв.", "").strip())
                    product_data["price"] = price
                except ValueError:
                    product_data["price"] = None
            else:
                product_data["price"] = None

            # Извлича наличните размери
            size_container = container.find("div", class_="available-configurations")
            if size_container:
                sizes = [size.text.strip() for size in size_container.find_all("div", class_="value")]
                product_data["sizes"] = sizes
            else:
                product_data["sizes"] = []

            # Принтира информацията за продукта за проверка
            print("Данни за продукта:", product_data)

            # Добавя продукта в списъка
            self.products.append(product_data)

    def save_product_to_db(self, product_data):
        """Запазва данни за продукта в база данни."""
        conn = sqlite3.connect('products.db')  # Свързване към SQLite база данни
        cursor = conn.cursor()

        # Изтрива съществуващата таблица (ако има такава)
        cursor.execute("DROP TABLE IF EXISTS products")

        # Създава нова таблица за продуктите
        cursor.execute('''CREATE TABLE IF NOT EXISTS products (
                          id INTEGER PRIMARY KEY AUTOINCREMENT,
                          title TEXT,
                          brand TEXT,
                          price REAL,
                          sizes TEXT,
                          link TEXT)''')

        # Вмъква данните на продукта в таблицата
        cursor.execute('''INSERT INTO products (title, brand, price, sizes, link)
                          VALUES (?, ?, ?, ?, ?)''', 
                       (product_data['title'], 
                        product_data['brand'], 
                        product_data['price'], 
                        ', '.join(product_data['sizes']),  # Преобразува списъка в текст
                        product_data['link']))

        conn.commit()

        # Извлича и принтира данните от базата за проверка
        cursor.execute("SELECT * FROM products")
        rows = cursor.fetchall()
        print("Съдържание на базата след вмъкване:")
        for row in rows:
            print(row)

        conn.close()

    def run(self):
        """Стартира процеса на скрейпване."""
        print(f"Започване на скрейпинг за '{self.search_term}'...")
        initial_url = f"{self.base_url}"
        html = self.get_html(initial_url)

        if not html:
            print("Неуспешно извличане на началната страница.")
            return

        print(f"Скрейпинг на продукти от {self.base_url}...")
        self.parse_products(html)

        print(f"Скрейпинг завършен. Общо намерени продукти: {len(self.products)}")
        self.print_products()

    def print_products(self):
        """Принтира намерените продукти, сортирани по цена."""
        sorted_products = sorted(self.products, key=lambda x: x['price'] or float('inf'))
        for product in sorted_products:
            print(f"Заглавие: {product['title']}")
            print(f"Марка: {product['brand']}")
            print(f"Цена: {product['price']} лв.")
            print(f"Размери: {', '.join(product['sizes']) if product['sizes'] else 'Няма налични размери'}")
            print(f"Линк: {product['link']}")
            print("-------------------------------")


if __name__ == "__main__":
    # URL за уебсайта Pepina
    base_url = "https://pepina.bg/products/jeni/obuvki"
    search_term = "обувки"
    scraper = ProductScraper(base_url, search_term)
    scraper.run()
