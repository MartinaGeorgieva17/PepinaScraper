# #crawler.py - обхожда страници
# # от уебсайт, извлича данни за продукти и ги
# # записва в база данни. 
# # Класът Crawler обединява скрейпинга и управлението на данни в една структура.

# from PepinaScraper.db import DB
# from PepinaScraper.scraper import ProductScraper
# import requests
# from concurrent.futures import ThreadPoolExecutor

# class Crawler:
#     def __init__(self, base_url, data_path='./data/'):
#         self.base_url = base_url
#         self.seed = []  # Списък за съхранение на продуктите
#         self.visited = []  # Списък за посещавани страници
#         self.data_path = data_path
#         self.current_page_number = 1
#         self.db = DB()  # Свързване с базата данни

#     def get_html(self, url):
#         """ Извличане на HTML съдържанието от URL """
#         try:
#             response = requests.get(url)
#             response.raise_for_status()
#             return response.text
#         except requests.RequestException as e:
#             print(f"Error fetching {url}: {e}")
#             return None

#     def get_seed(self, url):
#         """ Обхождане на страници и събиране на продукти """
#         print(f"Crawling page {self.current_page_number}: {url}")
#         html = self.get_html(url)
#         if html:
#             scraper = ProductScraper(url, "обувки")  # Използваме търсене на обувки
#             scraper.parse_products(html)

#             self.seed.extend(scraper.products)  # Добавяне на продуктите към seed списъка

#             self.current_page_number += 1
#             next_page_url = f"{self.base_url}?page={self.current_page_number}"
#             self.get_seed(next_page_url)

#     def save_pub_data(self, product):
#         """ Запис на продукт в базата данни """
#         try:
#             # Тук използваме метода insert_row от DB, за да запишем продукта
#             self.db.insert_row(product)
#         except Exception as e:
#             print(f"Error saving data: {e}")

#     def run(self):
#         """ Стартиране на обхождането и записване на данни """
#         print(f"Starting crawling from {self.base_url}")
#         self.get_seed(self.base_url)
#         print(f"Seed contains {len(self.seed)} products")

#         # Записваме продуктите в базата данни чрез ThreadPoolExecutor за паралелна обработка
#         with ThreadPoolExecutor(max_workers=10) as executor:
#             print("Saving data...")
#             executor.map(self.save_pub_data, self.seed)

#         self.db.close()  # Закриваме връзката с базата след приключване
#         print("Crawling process completed!")
