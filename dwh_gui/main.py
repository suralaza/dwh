
import sys
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedWidget, QListWidget, QFileDialog,QApplication, QMainWindow,
    QFormLayout, QLineEdit, QTextEdit, QMessageBox,QHeaderView, QListWidgetItem,QMenu,QTableWidget, QTableWidgetItem,QTabWidget,QInputDialog
)
from PyQt6.QtCore import Qt, QPoint, pyqtSignal
import psycopg2
import csv


class ReleaseBuilderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DWH Release Builder")
        self.resize(1200, 800)

        self.tabs = QTabWidget()
        self.rules_mask_tab = RulesTab()
        self.file_upload_tab = FileUploadTab()
        self.release_tab = ReleaseBuildTab()
        self.deps_tab = DependenciesTab()
        self.log_tab = LogTab()
        self.settings_tab = SettingsTab()

        self.tabs.addTab(self.rules_mask_tab, "Правила")
        self.tabs.addTab(self.file_upload_tab, "Загрузка файлов")
        self.tabs.addTab(self.release_tab, "Сборка релиза")
        self.tabs.addTab(self.deps_tab, "Зависимости")
        self.tabs.addTab(self.log_tab, "Лог")
        self.tabs.addTab(self.settings_tab, "Настройки")

        self.setCentralWidget(self.tabs)

        # Для примера: прокинем логгер для вывода сообщений
        self.logger = self.log_tab


        # Связывание событий, пример
        self.file_upload_tab.file_uploaded.connect(
            lambda fname: self.logger.add_log(f"Загружен файл: {fname}")
        )
        self.rules_mask_tab.add_rules.connect(
            lambda val: self.logger.add_log(f"Правила: {val}")
        )

class FileUploadTab(QWidget):
    file_uploaded = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.label = QLabel("Загрузите релизные файлы для обработки")
        self.upload_btn = QPushButton("Загрузить файл")
        self.upload_btn.clicked.connect(self.open_file_dialog)

        self.files_list = QListWidget()
        self.files = []

        layout.addWidget(self.label)
        layout.addWidget(self.upload_btn)
        layout.addWidget(self.files_list)
        self.setLayout(layout)

    def open_file_dialog(self):
        dlg = QFileDialog(self)
        dlg.setFileMode(QFileDialog.FileMode.ExistingFiles)
        if dlg.exec():
            files = dlg.selectedFiles()
            for f in files:
                if f not in self.files:
                    self.files.append(f)
                    self.files_list.addItem(f)
                    self.file_uploaded.emit(f)

class SettingsTab(QWidget):
    """Вкладка настроек с меню выбора категорий слева."""

    def __init__(self):
        super().__init__()
        self.connection = None  # Для хранения соединения с БД
        self.init_ui()

    def init_ui(self):
        main_layout = QHBoxLayout()
        self.menu_list = QListWidget()
        self.menu_list.setMaximumWidth(180)
        self.menu_list.addItem("Подключения")
        self.menu_list.addItem("Лицензия")
        self.menu_list.addItem("LLM")
        self.menu_list.addItem("Общие сведения")
        self.menu_list.currentRowChanged.connect(self.switch_settings)
        self.settings_stack = QStackedWidget()
        self.conn_widget_instance = self.conn_widget()
        self.settings_stack.addWidget(self.conn_widget_instance)
        self.settings_stack.addWidget(self.license_widget())
        self.settings_stack.addWidget(self.llm_widget())
        self.settings_stack.addWidget(self.info_widget())
        main_layout.addWidget(self.menu_list)
        main_layout.addWidget(self.settings_stack)
        self.setLayout(main_layout)
        self.menu_list.setCurrentRow(0)

    def switch_settings(self, index):
        self.settings_stack.setCurrentIndex(index)

    def conn_widget(self):
        """Панель настроек подключения."""
        widget = QWidget()
        layout = QFormLayout(widget)
        self.host_edit = QLineEdit('localhost')
        self.port_edit = QLineEdit('5433')
        self.db_edit = QLineEdit()
        self.user_edit = QLineEdit()
        self.pass_edit = QLineEdit()
        self.pass_edit.setEchoMode(QLineEdit.EchoMode.Password)
        layout.addRow("Host", self.host_edit)
        layout.addRow("Port", self.port_edit)
        layout.addRow("Database", self.db_edit)
        layout.addRow("User", self.user_edit)
        layout.addRow("Password", self.pass_edit)
        return widget

    def license_widget(self):
        """Панель с лицензией."""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        self.license_edit = QTextEdit()
        layout.addWidget(QLabel("Лицензионный ключ или информация:"))
        layout.addWidget(self.license_edit)
        return widget

    def llm_widget(self):
        """Панель LLM (настройки модели)."""
        widget = QWidget()
        layout = QFormLayout(widget)
        self.llm_api_url = QLineEdit()
        self.llm_api_key = QLineEdit()
        layout.addRow("API URL", self.llm_api_url)
        layout.addRow("API KEY", self.llm_api_key)
        return widget


    def get_conn_params(self):
        """Всегда возвращает параметры прямо из полей ввода."""
        return {
            "host": self.host_edit.text(),
            "port": self.port_edit.text(),
            "dbname": self.db_edit.text(),
            "user": self.user_edit.text(),
            "password": self.pass_edit.text()
        }

    def info_widget(self):
        """Панель с общими сведениями"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        info = QLabel(
            "<b>Имя приложения</b>: DWH Release Builder<br>"
            "<b>Версия</b>: 1.0.0<br>"
            "<b>Автор</b>: SpaceKnot<br>"
            "&copy;2025"
        )
        info.setTextFormat(Qt.TextFormat.RichText)
        layout.addWidget(info)
        layout.addStretch(1)
        return widget



DEFAULT_COLUMNS = ['Тип объекта БД', 'Якорь парсера', 'Шаблон папки', 'Шаблон имени файла']

class RulesTab(QWidget):
    """Вкладка для таблицы с правилами, загрузки/сохранения, импорта/экспорта."""
    add_rules = pyqtSignal(str)

    def __init__(self, settings_tab=None):
        super().__init__()
        self.init_ui()
        self.settings_tab = SettingsTab()

    def init_ui(self):
        layout = QVBoxLayout(self)
        btn_layout = QHBoxLayout()

        self.load_csv_btn = QPushButton("Загрузить из CSV")
        self.save_csv_btn = QPushButton("Сохранить в CSV")
        self.load_pg_btn = QPushButton("Загрузить из БД")

        btn_layout.addWidget(self.load_csv_btn)
        btn_layout.addWidget(self.save_csv_btn)
        btn_layout.addWidget(self.load_pg_btn)

        self.table = QTableWidget()
        self.table.setColumnCount(len(DEFAULT_COLUMNS))
        self.table.setHorizontalHeaderLabels(DEFAULT_COLUMNS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)

        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addLayout(btn_layout)
        layout.addWidget(self.table)

        # Биндинг кнопок
        self.load_csv_btn.clicked.connect(self.load_from_csv)
        self.save_csv_btn.clicked.connect(self.save_to_csv)
        self.load_pg_btn.clicked.connect(self.load_from_postgres)


    def show_context_menu(self, pos):
        menu = QMenu()
        add_row = menu.addAction("Добавить строку")
        del_row = menu.addAction("Удалить строку")
        clear_all = menu.addAction("Очистить всё")
        action = menu.exec(self.table.viewport().mapToGlobal(pos))

        sel_items = self.table.selectedItems()
        sel_rows = set(i.row() for i in sel_items)
        sel_cols = set(i.column() for i in sel_items)

        if action == add_row:
            self.add_row()
        elif action == del_row:
            # Разрешаем удалять только если выбрана строка
            self.delete_row(list(sel_rows)[0])
        elif action == clear_all:
            self.table.setRowCount(0)
            self.table.setColumnCount(len(DEFAULT_COLUMNS))
            self.table.setHorizontalHeaderLabels(DEFAULT_COLUMNS)

    def add_row(self):
        row = self.table.rowCount()
        self.table.insertRow(row)
        for col in range(self.table.columnCount()):
            self.table.setItem(row, col, QTableWidgetItem(""))

    def delete_row(self, row):
        self.table.removeRow(row)


    def load_from_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Открыть CSV", "", "CSV (*.csv)")
        if not path:
            return
        try:
            with open(path, 'r', encoding='utf-8') as f:
                reader = csv.reader(f)
                headers = next(reader)
                self.table.setColumnCount(len(headers))
                self.table.setHorizontalHeaderLabels(headers)
                self.table.setRowCount(0)
                for row_data in reader:
                    row = self.table.rowCount()
                    self.table.insertRow(row)
                    for col, val in enumerate(row_data):
                        self.table.setItem(row, col, QTableWidgetItem(val))
            QMessageBox.information(self, "Успех", "Данные загружены из CSV")
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Ошибка", f"{e}\n{traceback.format_exc()}")

    def save_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить CSV", "", "CSV (*.csv)")
        if not path:
            return
        try:
            with open(path, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                headers = [self.table.horizontalHeaderItem(col).text() if self.table.horizontalHeaderItem(
                    col) else f"col{col + 1}"
                           for col in range(self.table.columnCount())]
                writer.writerow(headers)
                for row in range(self.table.rowCount()):
                    row_data = [
                        self.table.item(row, col).text() if self.table.item(row, col) else ''
                        for col in range(self.table.columnCount())
                    ]
                    writer.writerow(row_data)
            QMessageBox.information(self, "Успех", "Данные сохранены в CSV")
        except Exception as e:
            import traceback
            QMessageBox.critical(self, "Ошибка", f"{e}\n{traceback.format_exc()}")

    def load_from_postgres(self):

        params = self.settings_tab.get_conn_params()
        print(params)
        if not params:
            QMessageBox.warning(self, "ВНИМАНИЕ!", "Параметры подключения к БД не заданы.")
            return

        try:
            conn = psycopg2.connect(**params)
            cursor = conn.cursor()
            cursor.execute("SELECT type, anchor, folder_template, file_template FROM rules_table")
            rows = cursor.fetchall()
            self.table.setRowCount(0)
            self.table.setColumnCount(len(DEFAULT_COLUMNS))
            self.table.setHorizontalHeaderLabels(DEFAULT_COLUMNS)
            for r, row_data in enumerate(rows):
                self.table.insertRow(r)
                for c, value in enumerate(row_data):
                    self.table.setItem(r, c, QTableWidgetItem(str(value)))
            cursor.close()
            conn.close()
        except Exception as e:
            QMessageBox.critical(self, "Ошибка БД", f"Ошибка при загрузке правил:\n{e}")




class ReleaseBuildTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.label = QLabel("Предпросмотр релизных блоков и итоговой структуры")
        self.log_text = QTextEdit()
        self.log_text.setReadOnly(True)
        self.build_btn = QPushButton("Собрать релиз")
        layout.addWidget(self.label)
        layout.addWidget(self.build_btn)
        layout.addWidget(QLabel("Лог предсборки:"))

        layout.addWidget(self.log_text)
        self.setLayout(layout)

        # TODO: реализовать предпросмотр структуры, лог ошибок

class DependenciesTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Зависимости: структура объектов и дагов")
        # Здесь позже будет визуализация lineage
        layout.addWidget(label)
        self.setLayout(layout)

class LogTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        self.log_area = QTextEdit()
        self.log_area.setReadOnly(True)
        layout.addWidget(QLabel("Лог событий"))
        layout.addWidget(self.log_area)
        self.setLayout(layout)

    def add_log(self, message):
        self.log_area.append(message)




def main():
    app = QApplication(sys.argv)
    win = ReleaseBuilderApp()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
