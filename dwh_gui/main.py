
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QLabel, QHBoxLayout, QPushButton, QListWidget, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QTableWidget, QTableWidgetItem,
    QLineEdit, QMessageBox, QLabel, QHeaderView, QInputDialog
)
from PyQt6.QtCore import Qt

class ReleaseBuilderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DWH Release Builder")
        self.resize(1200, 800)

        self.tabs = QTabWidget()
        self.file_upload_tab = FileUploadTab()
        self.anchors_masks_tab = AnchorsMasksTab()
        self.release_tab = ReleaseBuildTab()
        self.deps_tab = DependenciesTab()
        self.log_tab = LogTab()
        self.settings_tab = SettingsTab()

        self.tabs.addTab(self.file_upload_tab, "Загрузка файлов")
        self.tabs.addTab(self.anchors_masks_tab, "Якоря и маски")
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

class FileUploadTab(QWidget):
    from PyQt6.QtCore import pyqtSignal
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

class AnchorsMasksTab(QWidget):
    def __init__(self):
        super().__init__()
        main_layout = QHBoxLayout()

        # ----- ЯКОРЯ -----
        anchor_group = QVBoxLayout()
        anchor_label = QLabel("Якоря")
        self.anchor_table = QTableWidget(0, 2)
        self.anchor_table.setHorizontalHeaderLabels(["Файл / шаблон", "Якорь"])
        self.anchor_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        anchor_btns = QHBoxLayout()
        self.add_anchor_btn = QPushButton("Добавить")
        self.del_anchor_btn = QPushButton("Удалить выбранный")
        self.edit_anchor_btn = QPushButton("Редактировать")
        anchor_btns.addWidget(self.add_anchor_btn)
        anchor_btns.addWidget(self.edit_anchor_btn)
        anchor_btns.addWidget(self.del_anchor_btn)
        anchor_group.addWidget(anchor_label)
        anchor_group.addWidget(self.anchor_table)
        anchor_group.addLayout(anchor_btns)

        # ----- МАСКИ -----
        mask_group = QVBoxLayout()
        mask_label = QLabel("Маски имен файлов")
        self.mask_table = QTableWidget(0, 2)
        self.mask_table.setHorizontalHeaderLabels(["Маска-шаблон", "Пример замены"])
        self.mask_table.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeMode.Stretch)
        mask_btns = QHBoxLayout()
        self.add_mask_btn = QPushButton("Добавить")
        self.del_mask_btn = QPushButton("Удалить выбранную")
        self.edit_mask_btn = QPushButton("Редактировать")
        mask_btns.addWidget(self.add_mask_btn)
        mask_btns.addWidget(self.edit_mask_btn)
        mask_btns.addWidget(self.del_mask_btn)
        mask_group.addWidget(mask_label)
        mask_group.addWidget(self.mask_table)
        mask_group.addLayout(mask_btns)

        # ----- Preview -----
        preview_group = QVBoxLayout()
        self.preview_label = QLabel("Предпросмотр масок:")
        self.preview_result = QLabel("")
        preview_group.addWidget(self.preview_label)
        preview_group.addWidget(self.preview_result)

        # --------------------------------

        main_layout.addLayout(anchor_group, 2)
        main_layout.addLayout(mask_group, 2)
        main_layout.addLayout(preview_group, 1)
        self.setLayout(main_layout)

        # -------------------------------
        # Логика - сигналы и обработчики
        # -------------------------------

        self.add_anchor_btn.clicked.connect(self.add_anchor)
        self.del_anchor_btn.clicked.connect(self.delete_anchor)
        self.edit_anchor_btn.clicked.connect(self.edit_anchor)

        self.add_mask_btn.clicked.connect(self.add_mask)
        self.del_mask_btn.clicked.connect(self.delete_mask)
        self.edit_mask_btn.clicked.connect(self.edit_mask)

        self.mask_table.itemSelectionChanged.connect(self.update_preview)
        self.anchor_table.itemSelectionChanged.connect(self.update_preview)

    def add_anchor(self):
        # Диалог на два ввода: Файл/Шаблон и Якорь

        file_name, ok1 = QInputDialog.getText(self, "Добавить якорь", "Введите имя файла или шаблон:")
        if not ok1 or not file_name.strip():
            return
        anchor, ok2 = QInputDialog.getText(self, "Добавить якорь", "Введите якорь (имя/паттерн):")
        if ok2 and anchor.strip():
            row = self.anchor_table.rowCount()
            self.anchor_table.insertRow(row)
            self.anchor_table.setItem(row, 0, QTableWidgetItem(file_name.strip()))
            self.anchor_table.setItem(row, 1, QTableWidgetItem(anchor.strip()))

    def delete_anchor(self):
        rows = set([i.row() for i in self.anchor_table.selectedIndexes()])
        for row in sorted(rows, reverse=True):
            self.anchor_table.removeRow(row)

    def edit_anchor(self):
        rows = set([i.row() for i in self.anchor_table.selectedIndexes()])
        if not rows:
            QMessageBox.warning(self, "Нет выбора", "Выберите строку для редактирования")
            return
        row = list(rows)[0]
        file_name = self.anchor_table.item(row, 0).text()
        anchor = self.anchor_table.item(row, 1).text()
        new_file, ok1 = QInputDialog.getText(self, "Редактировать файл/шаблон", "Имя файла/шаблон:", text=file_name)
        if not ok1 or not new_file.strip():
            return
        new_anchor, ok2 = QInputDialog.getText(self, "Редактировать якорь", "Якорь:", text=anchor)
        if ok2 and new_anchor.strip():
            self.anchor_table.setItem(row, 0, QTableWidgetItem(new_file.strip()))
            self.anchor_table.setItem(row, 1, QTableWidgetItem(new_anchor.strip()))

    def add_mask(self):
        mask, ok1 = QInputDialog.getText(self, "Добавить маску", "Введите маску-шаблон (например, table_{date}.csv):")
        if not ok1 or not mask.strip():
            return
        template_result = self.apply_mask_example(mask.strip())
        row = self.mask_table.rowCount()
        self.mask_table.insertRow(row)
        self.mask_table.setItem(row, 0, QTableWidgetItem(mask.strip()))
        self.mask_table.setItem(row, 1, QTableWidgetItem(template_result))

    def delete_mask(self):
        rows = set([i.row() for i in self.mask_table.selectedIndexes()])
        for row in sorted(rows, reverse=True):
            self.mask_table.removeRow(row)

    def edit_mask(self):
        rows = set([i.row() for i in self.mask_table.selectedIndexes()])
        if not rows:
            QMessageBox.warning(self, "Нет выбора", "Выберите строку для редактирования")
            return
        row = list(rows)[0]
        mask = self.mask_table.item(row, 0).text()
        new_mask, ok1 = QInputDialog.getText(self, "Редактировать маску", "Маска-шаблон:", text=mask)
        if ok1 and new_mask.strip():
            template_result = self.apply_mask_example(new_mask.strip())
            self.mask_table.setItem(row, 0, QTableWidgetItem(new_mask.strip()))
            self.mask_table.setItem(row, 1, QTableWidgetItem(template_result))

    def apply_mask_example(self, mask):
        # Простейшая замена {date} и {ver} для предпросмотра
        result = mask.replace("{date}", "2023-01-01").replace("{ver}", "v1")
        return result

    def update_preview(self):
        # Отобразить предпросмотр маски для выбранной строки
        selected = self.mask_table.selectedItems()
        if selected:
            mask = self.mask_table.item(selected[0].row(), 0).text()
            result = self.apply_mask_example(mask)
            self.preview_result.setText(f"Пример: {result}")
        else:
            self.preview_result.setText("")


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

class SettingsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()
        label = QLabel("Настройки (список ключей, триал, параметры)")
        layout.addWidget(label)
        # TODO: взаимодействие с личными ключами и триалом
        self.setLayout(layout)

def main():
    app = QApplication(sys.argv)
    win = ReleaseBuilderApp()
    win.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
