
import re
import requests
import os
from bs4 import BeautifulSoup


class ProductScraper:
    def __init__(self, base_url, search_term):
        self.base_url = base_url
        self.search_term = search_term
        self.products = []
        self.output_dir = './data'
        self.filename = f'{search_term}.html'
        self.file_path = os.path.join(self.output_dir, self.filename)

    def save_html(self, content):
        """Save the HTML content to a file."""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)

        with open(self.file_path, 'w', encoding='utf-8') as file:
            file.write(content)

    def get_html(self, url):
        headers = {"User-Agent": "Mozilla/5.0"}
        if os.path.exists(self.file_path):
            with open(self.file_path, "r", encoding="utf-8") as f:
                print("Loading content from local file.")
                return f.read()
        else:
            try:
                print(f"Sending request to {url}")
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                self.save_html(response.text)
                return response.text
            except requests.exceptions.RequestException as e:
                print(f"Request error: {e}")
                return None

    def extract_price(self, text):
        # regex за валидна цена (e.g., 720, 720.95).
        match = re.search(r'\b\d+(?:\.\d{1,2})?\b', text)
        if match:
            # връщаме цената като реално число
            return float(match.group())
        return None


    def parse_products(self, html):
        """Parse products from a single page."""
        soup = BeautifulSoup(html, 'html.parser')

        product_containers = soup.find_all("div", class_="component-product-list-product")
        if product_containers:
            for container in product_containers:
                shoe_data = {}

                # Първо проверяваме цената - ако е >1000 няма смисъл да визмаме
                # каквито и да е данни
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

                self.products.append(shoe_data)
        else:
            print("Не са намерени продукти в страницата!.")

            # Add the product data to the list
            self.products.append(product_data)

    def run(self):
        """Run the scraper."""
        print(f"Starting scraping process for '{self.search_term}'...")
        initial_url = f"{self.base_url}"
        html = self.get_html(initial_url)

        if not html:
            print("Failed to retrieve the initial page.")
            return

        print(f"Scraping products from {self.base_url}...")
        self.parse_products(html)

        print(f"Scraping completed. Total products found: {len(self.products)}")
        self.print_products()

    def print_products(self):
        """Print the scraped products sorted by price."""
        sorted_products = sorted(self.products, key=lambda x: x['price'] or float('inf'))
        for product in sorted_products:
            print(f"Title: {product['title']}")
            print(f"Brand: {product['brand']}")
            print(f"Price: {product['price']} лв.")
            print(f"Sizes: {', '.join(product['sizes']) if product['sizes'] else 'No sizes available'}")
            print(f"Link: {product['link']}")
            print("-------------------------------")


if __name__ == "__main__":
    # The URL is updated for the Pepina website
    base_url = "https://pepina.bg/products/jeni/obuvki"
    search_term = "обувки"
    scraper = ProductScraper(base_url, search_term)
    scraper.run()