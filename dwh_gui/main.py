
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QLabel, QHBoxLayout, QPushButton, QListWidget, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt
import utils.render_path
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLineEdit, QLabel, QPushButton, QComboBox

class ReleaseBuilderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DWH Release Builder")
        self.resize(1200, 800)

        self.tabs = QTabWidget()
        self.file_upload_tab = FileUploadTab()
        self.anchors_masks_tab = AnchorsTab()
        self.release_tab = ReleaseBuildTab()
        self.deps_tab = DependenciesTab()
        self.log_tab = LogTab()
        self.settings_tab = SettingsTab()

        self.tabs.addTab(self.file_upload_tab, "Загрузка файлов")
        self.tabs.addTab(self.anchors_masks_tab, "Якоря")
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

class AnchorsTab(QWidget):
    def __init__(self):
        super().__init__()
        layout = QVBoxLayout()

        self.anchor_input = QLineEdit()
        self.anchor_input.setPlaceholderText("Введите якорь (например, --model)")
        layout.addWidget(QLabel("Якорь"))
        layout.addWidget(self.anchor_input)

        self.path_template_input = QLineEdit()
        self.path_template_input.setPlaceholderText("Пример: {папка}/{стрим}/create_{storage}_{schema}_{obj}.sql")
        layout.addWidget(QLabel("Путь/Имя файла"))
        layout.addWidget(self.path_template_input)

        # Выпадающий список поддерживаемых переменных и примеров
        self.vars_hint = QComboBox()
        self.vars_hint.addItems([
            '{папка} — Например: model',
            '{стрим} — Например: mis',
            '{storage} — Например: gp',
            '{schema} — Например: core',
            '{obj} — Например: v_mis_patients'
        ])
        layout.addWidget(QLabel("Доступные переменные для шаблонов:"))
        layout.addWidget(self.vars_hint)

        self.preview = QLabel("Пример пути появится здесь…")
        layout.addWidget(self.preview)

        self.anchor_input.textChanged.connect(self.update_preview)
        self.path_template_input.textChanged.connect(self.update_preview)

        self.setLayout(layout)

    def update_preview(self):
        # Возьмём фейковые значения для примера (или потом — актуальные из кода)
        example_vars = {
            'папка': 'models',
            'стрим': 'mis',
            'storage': 'gp',
            'schema': 'core',
            'obj': 'v_mis_patients'
        }
        template = self.path_template_input.text()
        if template:
            path = utils.render_path(template, example_vars)
            self.preview.setText(f"Пример: {path}")
        else:
            self.preview.setText("Пример пути появится здесь…")


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
