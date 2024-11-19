import sys
from PyQt6 import QtWidgets as qtw
from PyQt6 import QtCore as qtc
from PyQt6.QtGui import QPixmap
from PepinaScraper.scraper import ProductScraper
from PepinaScraper.db import DB


BASE_URL = 'https://pepina.bg/products/jeni/obuvki'


# Клас за представяне на таблицата с данни
class DataTable(qtw.QTableWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.db = DB()  # Връзка с базата данни

        if not self.db.conn:  # Проверка на връзката
            qtw.QMessageBox.critical(
                None,
                "Грешка на базата данни!",
                "Провалена връзка с базата данни."
            )
            return

        self.column_names = ["Brand", "Price", "Color"]
        self.setup_table()

    def setup_table(self):
        """Настройване на таблицата."""
        self.setColumnCount(len(self.column_names))
        self.setHorizontalHeaderLabels(self.column_names)
        self.resizeColumnsToContents()
        self.setSortingEnabled(True)
        self.update_table(self.db.select_all_data())

    def update_table(self, data):
        """Обновяване на таблицата с нови данни."""
        self.setRowCount(0)  # Изчистване на старите редове
        for row_num, row_data in enumerate(data):
            self.insertRow(row_num)
            for col_num, value in enumerate(row_data):
                self.setItem(row_num, col_num, qtw.QTableWidgetItem(str(value)))

    def filter_by_size(self, size):
        """Филтриране на данните по размер."""
        try:
            size = float(size)
            data = self.db.select_data_by_size(size)
            self.update_table(data)
        except ValueError:
            qtw.QMessageBox.warning(None, "Грешка", "Моля, въведете валиден номер.")

    def sort_by_price(self, ascending=True):
        """Сортиране на таблицата по цена."""
        column = 1
        order = qtc.Qt.SortOrder.AscendingOrder if ascending else qtc.Qt.SortOrder.DescendingOrder
        self.sortItems(column, order)


# Клас за управление на таблицата с филтри и сортиране
class TableViewWidget(qtw.QWidget):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setup_gui()

    def setup_gui(self):
        """Настройване на интерфейса."""
        layout = qtw.QVBoxLayout()

        self.tableView = DataTable()
        layout.addWidget(self.tableView)

        self.filter_size_input = qtw.QLineEdit(self)
        self.filter_size_input.setPlaceholderText('Въведете номера на обувката (напр., "38")')
        self.filter_size_input.textChanged.connect(self.tableView.filter_by_size)
        layout.addWidget(self.filter_size_input)

        btnSortAsc = qtw.QPushButton("Сортиране по възходящ ред.")
        btnSortAsc.clicked.connect(lambda: self.tableView.sort_by_price(ascending=True))
        layout.addWidget(btnSortAsc)

        btnSortDesc = qtw.QPushButton("Сортиране по низходящ ред.")
        btnSortDesc.clicked.connect(lambda: self.tableView.sort_by_price(ascending=False))
        layout.addWidget(btnSortDesc)

        btnClose = qtw.QPushButton("Затваряне")
        btnClose.clicked.connect(self.close)
        layout.addWidget(btnClose)

        self.setLayout(layout)


# Главен прозорец на приложението
class MainWindow(qtw.QMainWindow):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.setWindowTitle('Pepina Crawler')
        self.setup_gui()

    def setup_gui(self):
        """Настройка на главния прозорец."""
        layout = qtw.QVBoxLayout()

        img_label = qtw.QLabel(self)
        pixmap = QPixmap('F:/Python_2024/PepinaScraper/PepinaScraper/images/PepinaScraper.png')
        pixmap = pixmap.scaled(600, 400, qtc.Qt.AspectRatioMode.KeepAspectRatio)
        img_label.setPixmap(pixmap)
        img_label.setAlignment(qtc.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(img_label)

        btnRunScraper = qtw.QPushButton('Стартиране на Скрейп')
        btnRunScraper.clicked.connect(self.run_scraper)
        layout.addWidget(btnRunScraper)

        self.btnShowData = qtw.QPushButton("Показване на данните")
        self.btnShowData.clicked.connect(self.show_data)
        layout.addWidget(self.btnShowData)

        mainWidget = qtw.QWidget()
        mainWidget.setLayout(layout)
        self.setCentralWidget(mainWidget)

    def run_scraper(self):
        """Стартиране на скрейпера."""
        try:
            scraper = ProductScraper(BASE_URL, "обувки")
            scraper.run()
        except Exception as e:
            qtw.QMessageBox.critical(self, "Грешка", f"Скрейпингът не е извършен: {str(e)}")

    def show_data(self):
        """Показване на данните в нов прозорец."""
        self.tableViewWidget = TableViewWidget()
        self.tableViewWidget.show()


# Главен блок за стартиране на приложението
if __name__ == '__main__':
    app = qtw.QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())
