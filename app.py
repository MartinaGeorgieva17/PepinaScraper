import sys
import os
from PyQt6 import QtWidgets as qtw
from PyQt6 import QtCore as qtc
from PyQt6.QtGui import QPixmap
from PepinaScraper.scraper import ProductScraper
from PepinaScraper.db import DB
from PyQt6.QtWidgets import QMessageBox
from PepinaScraper import read_config
from PepinaScraper.crawler import Crawler




BASE_URL = 'https://pepina.bg/products/jeni/obuvki'


# Създавам клас за представяне на таблицата с данни
class DataTable(qtw.QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.db = DB()  # Създаване на обект за връзка
        if not self.db.conn: # Проверка за успешно свързване с базата данни
            app = qtw.QApplication.instance() or qtw.QApplication(sys.argv)
            qtw.QMessageBox.critical(None, "Грешка на базата данни!", "Провалена връзка на базата с данни.")
            return

        self.data = self.db.select_all_data()  #  Извличаме данни от базата
        self.column_names = ["Brand", "Price", "Color"] 
        self.setup_table() 


    def setup_table(self):
        self.setColumnCount(len(self.column_names)) #Брой колони
        self.setHorizontalHeaderLabels(self.column_names) #Задаваме заглавия на колоните
        self.resizeColumnsToContents() #Настройка на колоните спрямо съдържанието
        self.setSortingEnabled(True) # Разрешаваме сортиране на таблицата
        self.update_table(self.data)


        
#Ъпдейтвам таблицата с новите данни

    def update_table(self, data):
        self.setRowCount(0) #изчистване на старите редове 
        for row_num, row_data in enumerate(data):
            self.insertRow(row_num)
            for col_num, value in enumerate(row_data):
                self.setItem(row_num, col_num, qtw.QTableWidgetItem(str(value)))


# Функация за филтриране по размер
    def filter_by_size(self, size):
        try:
            size=float(size) #Проверяваме дали въведения номер е валиден
            data = self.db.select_data_by_size(size) #извличане и сортиране на данни 
            self.update_table(data)
        except ValueError:
            qtw.QMessageBox.warning(None, "Грешка", "Моля, въведете валиден номер.")

    def sort_by_price(self, ascending = True):
        column = 1
        order = qtc.Qt.SortOrder.AscendingOrder if ascending else qtc.Qt.SortOrder.DescendingOrder
        self.sortItems(column, order)


#Клас за интерфейс и сортиране с филтър
class TableViewWidget(qtw.QWidget):   
    def __init__(self, parent, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.parent = parent
        self.setup_gui() #Настройване на графичен интерфейс
        

#Функция за настройване на графичен интерфейс
    def setup_gui(self):
        layout = qtw.QVBoxLayout() #Основен вертикален лейаут

    #Добавяне на таблица към интерфейса
    
        self.tableView = DataTable()
        layout.addWidget(self.tableView)  

    #Поле за филтриране по размер на обувката

        self.filter_size_input = qtw.QLineEdit(self)
        self.filter_size_input.setPlaceholderText('Въведете номера на обувката (пример, "38") ')
        self.filter_size_input.textChanged.connect(self.tableView.filter_by_size)
        layout.addWidget(self.filter_size_input)

#Бутон за сортиране по цена - възходящ ред
        btnSortAsc= qtw.QPushButton("Сортиране по възходящ ред.")
        btnSortAsc.clicked.connect(lambda:self.tableView.sort_by_price(ascending=True)) #Възходящо сортиране
        layout.addWidget(btnSortAsc)

#Бутон за сортиране по цена - низходящ ред 
        btnSortDesc = qtw.QPushButton("Сортиране по низходящ ред.")
        btnSortDesc.clicked.connect(lambda:self.tableView.sort_by_price(ascending=False))#Низходящо сортиране
        layout.addWidget(btnSortDesc)

    #Бутон за затваряне на прозореца 
        btnClose = qtw.QPushButton("Затваряне")
        btnClose.clicked.connect(self.close)
        layout.addWidget(btnClose)

        self.setLayout(layout) #Прилагам лейаута към текущия интерфейс


#Главен прозорец на приложението
class MainWindow(qtw.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Pepina Crawler')

        layout = qtw.QVBoxLayout() #Основен вертикален лейаут


#Главна картинка - основен прозорец 

        img_label = qtw.QLabel(self)
        pixmap = QPixmap('F:\Python_2024\PepinaScraper\PepinaScraper\images\PepinaScraper.png')
        pixmap = pixmap.scaled(600, 400, qtc.Qt.AspectRatioMode.KeepAspectRatio)
        img_label.setPixmap(pixmap)
        img_label.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(img_label)



 #Главен бутон за стартиране на скрейпа
        
        btnRunScraper = qtw.QPushButton('Стартиране на Скрейп')
        btnRunScraper.clicked.connect(self.run_scraper) #При натиск на бутона -стартира
        layout.addWidget(btnRunScraper)

#Бутон за показване на данните в таблица
        self.btnShowData = qtw.QPushButton("Показване на данните")
        self.btnShowData.clicked.connect(self.show_data) #При натискане с епоказват данните
        layout.addWidget(self.btnShowData)

#Основен widget с layout
        mainWidget = qtw.QWidget()
        mainWidget.setLayout(layout)
        self.setCentralWidget(mainWidget)
        self.show() #Показване на прозореца 

#Функция за стартиране на скрейпване
    
    def run_scraper(self):
        try:
            search_term = "обувки"  # Можете да зададете съответния термин за търсене
            scraper = ProductScraper(BASE_URL, search_term)
            scraper.run()
            self.load_data()
        except Exception as e:
            qtw.QMessageBox.critical(self, "Грешка", f"Скрейпингът не е извършен: {str(e)}")

    
    
#Функция за показване на данните в таблица: 

    def show_data(self):
        """ Проверяваме дали `tableViewWidget` вече съществува, ако не - създаваме го """
        if not hasattr(self, "tableViewWidget"):
            self.tableViewWidget = TableViewWidget(parent=self)  # Обект - създаване TableViewWidget
        self.tableViewWidget.show()  # Показване на таблицата
        self.tableViewWidget.update_table(self.db.select_all_data())



#Функция за зареждане на данните
    def load_data(self):
        db = DB() #Създавнае на обект за работа
        data = db.select_all_data() #Извличане на всички данни
        if hasattr(self,"tableViewWidget"):
            self.tableViewWidget.update_table(data) #Обновяване на таблицата

       
    def run_crawler(self):
       self.setCursor(qtc.Qt.WaitCursor)
       self.crawler.run()
       self.setCursor(qtc.Qt.ArrowCursor)

if __name__ == '__main__':
    app = qtw.QApplication(sys.argv) #Създаваме приложението

    # base_url = 'https://pepina.bg/products/jeni/obuvki'
    # try:
    #     crawler = Crawler(base_url)
    #     crawler.run()
    # except Exception as e:
    #     qtw.QMessageBox.critical(None, "Грешка при Crawler", f"Процесът на краулинг се провали: {str(e)}")

    window = MainWindow() #Създаваме главен прозорец 
    sys.exit(app.exec()) #Стартиране на основни цикъл на приложението