import requests
import os
from bs4 import BeautifulSoup
from PepinaScraper.db import DB
import time



class Scraper:
    def __init__(self, url):
        self.url = url
        self.shoes = []
        self.db = DB()

    def get_html(self, url):
        filename = f'./data/obuvki_{int(time.time())}.html'
        headers = {"User-Agent": "Mozilla/5.0"}

        if os.path.exists(filename):
            with open(filename, "r", encoding="utf-8") as f:
                print("Зареждане на съдържание от локалния файл")
                return f.read()
        else:
            try:
                print(f"Изпраща заявка до {url}")
                response = requests.get(url, headers=headers)
                response.raise_for_status()
                if not os.path.exists('./data'):
                    os.makedirs('./data')
                with open(filename, "w", encoding="utf-8") as f:
                    f.write(response.text)
                    print(f"Съдържанието е записано в: {filename}")
                return response.text
            except requests.exceptions.RequestException as e:
                print(f"Грешка при заявка: {e}")
                return None

    def parse_data(self, html):
        soup = BeautifulSoup(html, 'html.parser')

        section_title = soup.find("h1", class_="title")
        if section_title and "Дамски обувки" in section_title.text:
            product_containers = soup.find_all("div", class_="component-product-list-product")

            for container in product_containers:
                shoe_data = {}

                link_tag = container.find("a", class_="product-link")
                shoe_data["link"] = link_tag['href'] if link_tag else None

                # img_tag = container.find("div", class_="main-image").find("img")
                # shoe_data["image"] = img_tag['src'] if img_tag else None

                brand_tag = container.find("div", class_="brand")
                shoe_data["brand"] = brand_tag.text.strip() if brand_tag else None

                title_tag = container.find("div", class_="title")
                shoe_data["title"] = title_tag.text.strip() if title_tag else None





                # price_tag = container.find("div", class_="regular-price")
                # shoe_data["price"] = price_tag.text.strip() if price_tag else None



                price_tag = container.find("div", class_="regular-price")
                if price_tag:
                    price_text = price_tag.text.strip()
                    price_text = price_text.replace("лв", "").replace(",", ".").strip()
                    try:
                        price = float(price_text)
                        if price < 1000:
                            shoe_data["price"] = price
                        else:
                            print(f"Пропусната обувка с цена над 1000 лв: {shoe_data}")
                            continue
                    except ValueError:
                        print(f"Невалидна цена за обувка: {shoe_data}")
                        continue
                else:
                    print("Липсва цената на обувка")
                    continue    #Продължаваме с друга обувка, ако няма цена
            

            
                color_tag = container.find("div", class_="color")
                shoe_data["color"] = color_tag.text.strip() if color_tag else "N/A"


                size_tags = container.find("div", class_="available-configurations")
                if size_tags:
                    shoe_data["sizes"] = [size.text.strip() for size in size_tags.find_all("div", class_="value")]
                else:
                    shoe_data["sizes"] = []

                print(f"Добавена обувка {shoe_data}")

                self.shoes.append(shoe_data)
        else:
            print("Секцията 'Дамски обувки' не беше намерена на страницата.")

    def get_all_pages(self):
        page = 1
        all_shoes = []
        while True:
            url_with_page = f"{self.url}?page={page}"
            html = self.get_html(url_with_page)
            if html:
                self.parse_data(html)
                all_shoes.extend(self.shoes)
                page += 1
                # Изход, ако няма следваща страница
                if not self.has_next_page(html):
                    break
            else:
                print("Не беше получен HTML от сайта!")
                break
        return all_shoes


    def has_next_page(self, html):
        soup = BeautifulSoup(html, 'html.parser')
        next_button = soup.find("a", {"class": "next"})
        return next_button is not None
    

    def sort_by_brand(self):
        self.shoes.sort(key=lambda x: x['brand'])

    def filter_by_size(self, size):
        return [shoe for shoe in self.shoes if size in shoe['sizes']]

    def scrape(self):
        html = self.get_html(self.url)
        if html:
            self.parse_data(html)
        return self.shoes
    

    def fetch_shoes_data(self, max_price=1000, brand_filter=None):
        html = self.get_html(self.url)
        if html:
            self.parse_data(html)
        # Филтрираме само валидни обувки
            valid_shoes = [
                shoe for shoe in self.shoes 
                if shoe['price'] < max_price and (not brand_filter or shoe['brand'] == brand_filter)
        ]
            if not valid_shoes:
                print("Няма обувки, отговарящи на критериите.")
            return valid_shoes
        else:
            raise Exception("Не успяхме да получим данни.")
        
    def save_to_db(self):
        for shoe in self.shoes:
        # Предполага се, че имате метод в DB, който проверява за съществуването на обувката по уникален линк
            if not self.db.does_shoe_exist(shoe['link']):
                self.db.insert_shoe(shoe)
        else:
            print(f"Обувката с линк {shoe['link']} вече съществува в базата данни.")



    def run(self):
        print("Започва scraping процесът...")
        
        try:
            self.db.drop_shoes_table()
            self.db.create_shoes_table()
            print("Таблиците в базата данни бяха обновени.")
        except Exception as e:
            print(f"Грешка при работа с базата данни: {e}")
            return

        html = self.get_html(self.url)
        if html:
            self.parse_data(html)
            print(f"Парсингът е завършен, намерени обувки:{len(self.shoes)}!")
        else:
            print(f"Не беше получен HTML от сайта!")



if __name__ == "__main__":
    scraper = Scraper("https://pepina.bg/products/jeni/obuvki")
    scraper.run()

# scraper.sort_by_brand()
# print("Обувки, сортирани по брандове:")
# for shoe in scraper.shoes:
#     print(shoe)

# filtered_by_size = scraper.filter_by_size("38")
# print("\nОбувки с размер 38:")
# for shoe in filtered_by_size:
#     print(shoe)

    scraper.sort_by_brand()
    print("Обувки, сортирани по брандове:")
    for shoe in scraper.shoes:
        print(shoe)


    filtered_by_size = scraper.filter_by_size("38")
    print("\nОбувки с размер 38:")
    for shoe in filtered_by_size:
        print(shoe)