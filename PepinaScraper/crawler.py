from PepinaScraper.scraper import ProductScraper
from PepinaScraper.db import DB
import requests
import os
import sys
import threading
from concurrent.futures import ThreadPoolExecutor


sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

class Crawler():
    def __init__(self, base_url, data_path='./data/'):
        self.base_url = base_url
        self.seed = []
        self.visited = []
        self.data_path = data_path
        self.current_page_number = 1
        self.db = DB()

    def get_html(self, url):
        try:
            response = requests.get(url)
            response.raise_for_status()
            return response.text
        except requests.RequestException as e:
            print(f"Error fetching {url}: {e}")
            return None

    def get_seed(self, url):
        print(f"Crawling page {self.current_page_number}: {url}")
        html = self.get_html(url)
        if html:
            scraper = ProductScraper(url, "обувки")  # Assuming 'обувки' is your search term
            scraper.parse_products(html)

            self.seed.extend(scraper.products)  # Append scraped products

            self.current_page_number += 1
            next_page_url = f"{self.base_url}?page={self.current_page_number}"
            self.get_seed(next_page_url)

    def save_pub_data(self, product):
        try:
            self.db.insert_row(product)
        except Exception as e:
            print(f"Error saving data: {e}")

    def run(self):
        print(f"Starting crawling from {self.base_url}")
        self.get_seed(self.base_url)
        print(f"Seed contains {len(self.seed)} URLs")

        with ThreadPoolExecutor(max_workers=10) as executor:
            print("Saving data...")
            executor.map(self.save_pub_data, self.seed)

        self.db.conn.close()
        print("Crawling process completed!")


if __name__ == '__main__':
    base_url = 'https://pepina.bg/products/jeni/obuvki'
    if len(sys.argv) > 1:
        base_url = sys.argv[1]

    crawler = Crawler(base_url)
    crawler.run()