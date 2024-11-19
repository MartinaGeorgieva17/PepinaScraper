import requests
import re
import threading
import time
import os
import sys



try:
    from PepinaScraper.scraper import Scraper
    from PepinaScraper.db import DB
except:
    from .scraper import Scraper
    from .db import DB

class Crawler():
	def __init__(self, base_url, data_path='./data/'):
		self.base_url = base_url
		self.seed = []
		self.visited = []
		self.data_path = data_path
		self.current_page_number = 1
		self.db = DB()


	def make_filename(self,url):
		""" Extracts domain from a url.
			Prepend data_path and append '.html'

			:param url: string

			return <domain>.html string
		"""
		rx = re.compile(r'^https?:\/\/(?:www.)?([^\/]+)\/?')
		m = rx.search(url)
		if m:
			filename = self.data_path + m[1]  + '.html'
			# print(filename)
			return filename
		else:
			print(f'Can not get domain from {url}')
			exit(-1)

	def write_to_file(self,filename, content):
		""" Write string to given filename
				:param filename: string
				:param content: sring
		"""
		try:
			with open(filename, 'w',encoding='utf-8') as f:
				f.write(content)
		except FileNotFoundError:
			print(f'File {filename} does not exists!')
		except Exception as e:
			print(f'Can not write to file: {filename}: {str(e)}')
			exit(-1)

	def get_html(self,url):
		# GET request without SSL verification:
		try:
			r = requests.get(url)
		except requests.RequestException:
			r = requests.get(url,verify=False)
		except Exception as e:
			print(f'Can not get url: {url}: {str(e)}!')
			exit(-1)

		# set content encoding explicitely
		r.encoding="utf-8"

		if r.ok:
			return r.text
		else:
			print('The server did not return success response. Bye...')
			exit()


	def get_seed(self, url):
		print(f'Crawling main page {self.current_page_number}: {url}')
		html = self.get_html(url)

		scraper = Scraper(html)
		pubs_urls = scraper.get_pubs_urls()

		# if pubs_urls is not empy => crawl next
		if pubs_urls:
			# prepend 'https://pepina.bg' to pubs_urls:
			pubs_urls = ['https://pepina.bg'+url for url in pubs_urls]

			# concatenate pubs.urls to self.seed
			self.seed.extend(pubs_urls)

			# make next page url
			self.current_page_number+=1
			next_page_url = f'{self.base_url}?page_1_1={self.current_page_number}'

			# get urls from next_page_url
			self.get_seed(next_page_url)

	def get_pub_data(self, url):
		print(f'Crawling page: {url}')
		html = self.get_html(url)

		scraper = Scraper(html)
		pub_data = scraper.get_pub_data()

		return pub_data

	def save_pub_data(self,url):
		try:
			print(f"Записване на данни за Url: {url}")
			pub_data = self.get_pub_data(url)
			if pub_data:
				self.db.insert_row(pub_data)
			else:
				print(f"Няма данни за {url}")
		except Exception as e: 
			print(f"Грешка при записване на данни за {url} e {e}")



	def run(self):
		# Starts crawling
		print(f"Започвам краулинг процеса от: {self.base_url}")
		self.get_seed(self.base_url)
		print(f'Seed contains {len(self.seed)} urls')

		with ThreadPoolExecutor(max_workers=10) as executor:
			print("Започва записването на данни..")
			executor.map(self.save_pub_data, self.seed)

		self.db.conn.close()
		print('Процесът на Crawler е завършен!')


if __name__ == '__main__':
	base_url = 'https://pepina.bg/products/jeni/obuvki'

	if len(sys.argv) > 1:
		base_url = sys.argv[1]

	crawler = Crawler(base_url)
	crawler.run()