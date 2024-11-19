import sys
import os

from PyQt6 import QtWidgets as qtw
from PyQt6 import QtCore as qtc
from PyQt6.QtGui import QPixmap
from PyQt6.QtWidgets import QMessageBox
from PyQt6.QtSql import QSqlTableModel

from PepinaScraper.scraper import Scraper
from PepinaScraper.db import DB

BASE_URL = 'https://pepina.bg/products/jeni/obuvki'


class TableViewWidget(qtw.QWidget):
    def __init__(self, db_connection, parent=None):
        super().__init__(parent)
        self.db_connection = db_connection
        self.setWindowTitle("Shoes data")

        # Layout setup
        layout = qtw.QVBoxLayout(self)

        # Filter input for size
        self.filter_input = qtw.QLineEdit(self)
        self.filter_input.setPlaceholderText("Filter by size...")
        self.filter_input.textChanged.connect(self.apply_filter)
        layout.addWidget(self.filter_input)

        # Table view setup
        self.table_view = qtw.QTableView(self)
        layout.addWidget(self.table_view)

        # Model setup
        self.model = QSqlTableModel(self, db_connection)
        self.model.setTable("shoes")
        self.model.setEditStrategy(QSqlTableModel.EditStrategy.OnFieldChange)
        self.model.select()


        # Set model to table view
        self.table_view.setModel(self.model)

        # Enable sorting
        self.table_view.setSortingEnabled(True)

        # Customize table view
        self.table_view.resizeColumnsToContents()

    def apply_filter(self):
        # Get the text from the filter input
        size = self.filter_input.text().strip()

        # Apply filter if there's a size input, otherwise clear filter
        if size:
            # Use FIND_IN_SET for CSV string filtering
            self.model.setFilter(f"FIND_IN_SET('{size}', sizes) > 0")
        else:
            self.model.setFilter("")  # Clear the filter


class MainWindow(qtw.QMainWindow):
    '''Главен прозорец на приложението'''
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Pepina Crawler')

        self.db = DB()
        if not self.db.conn:
            QMessageBox.critical(None, "Грешка на базата данни!", "Провалена връзка на базата с данни.")
            sys.exit()

        self.setup_gui()

    def setup_gui(self):
        layout = qtw.QVBoxLayout() #Основен вертикален лейаут

        #Главна картинка - основен прозорец
        img_label = qtw.QLabel(self)
        pixmap = QPixmap('./PepinaScraper/images/PepinaScraper.png')
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

    def run_scraper(self):
        '''Функция за стартиране на скрейпване'''

        try:
            self.db.drop_shoes_table()
            self.db.create_shoes_table()
        except Exception as e:
            print(f"Грешка при работа с базата данни: {e}")
            return

        try:
            scraper = Scraper(BASE_URL)
            scraper.run()
            self.db.insert_rows(scraper.shoes_data)
        except Exception as e:
            qtw.QMessageBox.critical(self, "Грешка", f"Скрейпингът не е извършен: {str(e)}")

        # Изпълняваме select отново, за да презаредим данните във view-то
        self.tableViewWidget.model.select()

    def show_data(self):
        '''Функция за показване на данните в таблица:'''

        #Проверяваме дали `tableViewWidget` вече съществува, ако не - създаваме го
        if not hasattr(self, "tableViewWidget"):
            self.tableViewWidget = TableViewWidget(self.db.qsql_conn)  # Обект - създаване TableViewWidget
        self.tableViewWidget.show()  # Показване на таблицата


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