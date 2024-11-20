import re
import requests
import os
from bs4 import BeautifulSoup


class Scraper:
    def __init__(self, url):
        self.url = url
        self.shoes_data = []
        self.output_dir = './data'
        self.filename = 'obuvki.html'
        self.file_path = os.path.join(self.output_dir, self.filename)

    def save_html(self, content):
        '''Saves the HTML content to a file'''
        #
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        with open(self.file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def get_html(self, url):
        headers = {"User-Agent": "Mozilla/5.0"}

        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                print("Зареждане на съдържание от локалния файл")
                return f.read()
        else:
            try:
                print(f"Изпраща заявка до {url}")
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                self.save_html(response.text)
                return response.text
            except requests.exceptions.RequestException as e:
                print(f"Грешка при заявка: {e}")
                return None

    def extract_price(self, text):
        # Matches valid price formats (e.g., 720, 720.95).
        match = re.search(r'\b\d+(?:\.\d{1,2})?\b', text)
        if match:
            return float(match.group())
        return None

    def parse_data(self, html):
        soup = BeautifulSoup(html, 'html.parser')

        product_containers = soup.find_all("div", class_="component-product-list-product")
        if product_containers:
            for container in product_containers:
                shoe_data = {}

                price_tag = container.find("div", class_="regular-price")
                if price_tag:
                    price_text = price_tag.text.strip()

                    price =self.extract_price(price_text)

                    if price and price < 1000:
                        shoe_data["price"] = price
                    else:
                        continue # skip loop if price doesn't meet condition
                else:
                    continue # skip loop if price_tag is not found

                link_tag = container.find("a", class_="product-link")
                shoe_data["link"] = link_tag['href'] if link_tag else None

                # img_tag = container.find("div", class_="main-image").find("img")
                # shoe_data["image"] = img_tag['src'] if img_tag else None

                brand_tag = container.find("div", class_="brand")
                shoe_data["brand"] = brand_tag.text.strip() if brand_tag else None

                title_tag = container.find("div", class_="title")
                shoe_data["title"] = title_tag.text.strip() if title_tag else None


                color_tag = container.find("div", class_="color")
                shoe_data["color"] = color_tag.text.strip() if color_tag else "N/A"

                size_tags = container.find("div", class_="available-configurations")
                if size_tags:
                    shoe_data["sizes"] = [size.text.strip() for size in size_tags.find_all("div", class_="value")]
                else:
                    shoe_data["sizes"] = []

                self.shoes_data.append(shoe_data)
        else:
            print("Не са намерени продукти в страницата!.")


    def run(self):
        print("Започва scraping процесът...")

        html = self.get_html(self.url)
        if html:
            self.parse_data(html)
            print(f"Парсингът е завършен, намерени обувки:{len(self.shoes_data)}!")
        else:
            print(f"Не беше получен HTML от сайта!")



if __name__ == "__main__":
    scraper = Scraper("https://pepina.bg/products/jeni/obuvki")
    scraper.run()