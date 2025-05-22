import sys
import csv
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedWidget, QListWidget, QFileDialog,
    QApplication, QMainWindow, QFormLayout, QLineEdit, QTextEdit, QMessageBox, QHeaderView, QListWidgetItem,
    QMenu, QTableWidget, QTableWidgetItem, QTabWidget, QInputDialog
)
from PyQt6.QtCore import Qt, pyqtSignal
import duckdb

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

        # Пример прокидывания логгера
        self.logger = self.log_tab
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

# --- Важные обновления: ---------------------------------------------------

DEFAULT_COLUMNS = ['Тип объекта', 'Якорь парсера', 'Шаблон папки', 'Шаблон файла']
DB_PATH = "rules_data.duckdb"

class RulesTab(QWidget):
    """Вкладка для таблицы с правилами, загрузки/сохранения, импорта/экспорта."""
    add_rules = pyqtSignal(str)

    def __init__(self, settings_tab=None):
        super().__init__()
        self.settings_tab = settings_tab
        self.init_ui()
        self.init_db()
        self.load_from_duckdb()  # Автозагрузка при запуске

    def init_ui(self):
        layout = QVBoxLayout(self)
        btn_layout = QHBoxLayout()

        self.load_csv_btn = QPushButton("Загрузить из CSV")
        self.save_csv_btn = QPushButton("Сохранить в CSV")
        self.save_pg_btn = QPushButton("Сохранить в БД")
        self.load_pg_btn = QPushButton("Загрузить из БД")

        btn_layout.addWidget(self.load_csv_btn)
        btn_layout.addWidget(self.save_csv_btn)
        btn_layout.addWidget(self.save_pg_btn)
        btn_layout.addWidget(self.load_pg_btn)

        self.table = QTableWidget()
        self.table.setColumnCount(len(DEFAULT_COLUMNS))
        self.table.setHorizontalHeaderLabels(DEFAULT_COLUMNS)
        self.table.setEditTriggers(QTableWidget.EditTrigger.AllEditTriggers)

        self.table.setContextMenuPolicy(Qt.ContextMenuPolicy.CustomContextMenu)
        self.table.customContextMenuRequested.connect(self.show_context_menu)

        layout.addLayout(btn_layout)
        layout.addWidget(self.table)

        self.setLayout(layout)

        # Биндинг кнопок
        self.load_csv_btn.clicked.connect(self.load_from_csv)
        self.save_csv_btn.clicked.connect(self.save_to_csv)
        self.save_pg_btn.clicked.connect(self.save_to_duckdb)
        self.load_pg_btn.clicked.connect(self.load_from_duckdb)

    def init_db(self):
        self.connection = duckdb.connect(DB_PATH)
        fields = ', '.join([f'"{col}" VARCHAR' for col in DEFAULT_COLUMNS])
        self.connection.execute(f"""
            CREATE TABLE IF NOT EXISTS rules (
                "Тип объекта" TEXT,
                "Якорь парсера" TEXT,
                "Шаблон папки" TEXT,
                "Шаблон файла" TEXT
            );
            """)  # DuckDB игнорирует AUTOINCREMENT

    def show_context_menu(self, pos):
        menu = QMenu()
        add_row = menu.addAction("Добавить строку")
        del_row = menu.addAction("Удалить строку")
        clear_all = menu.addAction("Очистить всё")
        action = menu.exec(self.table.viewport().mapToGlobal(pos))

        sel_items = self.table.selectedItems()
        sel_rows = set(i.row() for i in sel_items)

        if action == add_row:
            self.add_row()
        elif action == del_row and sel_rows:
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

    def save_to_csv(self):
        path, _ = QFileDialog.getSaveFileName(self, "Сохранить в CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        with open(path, "w", newline='', encoding='utf-8') as f:
            writer = csv.writer(f)
            writer.writerow(DEFAULT_COLUMNS)
            for row in range(self.table.rowCount()):
                writer.writerow([self.table.item(row, col).text() if self.table.item(row, col) else ''
                                 for col in range(self.table.columnCount())])

    def load_from_csv(self):
        path, _ = QFileDialog.getOpenFileName(self, "Загрузить из CSV", "", "CSV Files (*.csv)")
        if not path:
            return
        with open(path, "r", newline='', encoding='utf-8') as f:
            reader = csv.reader(f)
            headers = next(reader)
            if headers != DEFAULT_COLUMNS:
                QMessageBox.warning(self, "Ошибка", "Неверные заголовки столбцов в файле!")
                return
            self.table.setRowCount(0)
            for row_data in reader:
                row = self.table.rowCount()
                self.table.insertRow(row)
                for col, value in enumerate(row_data):
                    self.table.setItem(row, col, QTableWidgetItem(value))

    def save_to_duckdb(self):
        self.connection.execute('TRUNCATE rules')
        try:
            for row in range(self.table.rowCount()):
                row_data = []
                for col in range(self.table.columnCount()):
                    item = self.table.item(row, col)
                    row_data.append(item.text() if item else None)

                # Строгая проверка совпадения столбцов и данных
                if len(row_data) != len(DEFAULT_COLUMNS):
                    print(f"Ошибка: размер данных не совпадает с количеством колонок в DEFAULT_COLUMNS")
                    continue

                placeholders = ', '.join(['?'] * len(DEFAULT_COLUMNS))
                columns_sql = ', '.join([f'"{c}"' for c in DEFAULT_COLUMNS])
                query = f'INSERT INTO rules ({columns_sql}) VALUES ({placeholders})'
                try:
                    self.connection.execute(query, row_data)
                except Exception as db_err:
                    print(f"Ошибка запроса к БД: {db_err}")

            self.connection.commit()
            QMessageBox.information(self, "Готово", "Данные успешно сохранены.")
        except Exception as ex:
            QMessageBox.information(self, "ВНИМАНИЕ!", f"Ошибка:{ex}")

    def load_from_duckdb(self):
        self.table.setRowCount(0)
        try:
            columns_sql = ', '.join([f'"{c}"' for c in DEFAULT_COLUMNS])
            cursor = self.connection.execute(f"SELECT {columns_sql} FROM rules")
            for row_data in cursor.fetchall():
                row = self.table.rowCount()
                self.table.insertRow(row)
                for col, value in enumerate(row_data):
                    self.table.setItem(row, col, QTableWidgetItem(str(value) if value else ''))
        except duckdb.Error as e:
            print("Ошибка при загрузке из duckdb:", str(e))

    def closeEvent(self, event):
        # Важно!

        self.save_to_duck_db()
        self.connection.close()
        super().closeEvent(event)


class SettingsTab(QWidget):
    """Вкладка Настройки без меню Подключения!"""
    def __init__(self):
        super().__init__()
        self.connection = duckdb.connect("settings.db")
        self.create_settings_table()
        main_layout = QHBoxLayout()
        self.menu_list = QListWidget()
        self.menu_list.setMaximumWidth(180)
        self.menu_list.addItem("Лицензия")
        self.menu_list.addItem("LLM")
        self.menu_list.addItem("Общие сведения")
        self.menu_list.currentRowChanged.connect(self.switch_settings)
        self.settings_stack = QStackedWidget()
        self.settings_stack.addWidget(self.license_widget())
        self.settings_stack.addWidget(self.llm_widget())
        self.settings_stack.addWidget(self.info_widget())
        main_layout.addWidget(self.menu_list)
        main_layout.addWidget(self.settings_stack)
        self.setLayout(main_layout)
        self.menu_list.setCurrentRow(0)
        self.load_settings()

    def create_settings_table(self):
        self.connection.execute("""
        CREATE TABLE IF NOT EXISTS settings (
            key VARCHAR PRIMARY KEY,
            value VARCHAR
        )
        """)

    def load_settings(self):
        # пример: загружать ключи для лицензии и LLM
        cursor = self.connection.execute("SELECT key, value FROM settings")
        data = dict(cursor.fetchall())
        # используйте data['license'] / data['llm'] по месту

    def switch_settings(self, index):
        self.settings_stack.setCurrentIndex(index)

    def license_widget(self):
        w = QWidget()
        layout = QVBoxLayout()
        self.license_edit = QLineEdit()
        btn_save = QPushButton("Сохранить лицензию")
        btn_save.clicked.connect(self.save_license)
        layout.addWidget(QLabel("Лицензия:"))
        layout.addWidget(self.license_edit)
        layout.addWidget(btn_save)
        w.setLayout(layout)
        return w

    def save_license(self):
        text = self.license_edit.text()
        self.connection.execute("INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?)", ("license", text))
        self.connection.commit()
        QMessageBox.information(self, "Готово", "Лицензия сохранена.")

    def llm_widget(self):
        w = QWidget()
        layout = QVBoxLayout()
        self.llm_edit = QLineEdit()
        btn_save = QPushButton("Сохранить LLM")
        btn_save.clicked.connect(self.save_llm)
        layout.addWidget(QLabel("LLM ключ:"))
        layout.addWidget(self.llm_edit)
        layout.addWidget(btn_save)
        w.setLayout(layout)
        return w

    def save_llm(self):
        text = self.llm_edit.text()
        self.connection.execute("INSERT OR REPLACE INTO settings(key, value) VALUES (?, ?)", ("llm", text))
        self.connection.commit()
        QMessageBox.information(self, "Готово", "LLM ключ сохранен.")

    def info_widget(self):
        w = QWidget()
        layout = QVBoxLayout()
        layout.addWidget(QLabel("Общие сведения о программе"))
        w.setLayout(layout)
        return w

# ------ Заглушки для остальных вкладок:
class ReleaseBuildTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
class DependenciesTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
class LogTab(QWidget):
    def __init__(self):
        super().__init__()
        self.setLayout(QVBoxLayout())
    def add_log(self, text):
        pass

if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = ReleaseBuilderApp()
    win.show()
    sys.exit(app.exec())
