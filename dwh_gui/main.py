
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QLabel, QHBoxLayout, QPushButton, QListWidget, QFileDialog, QTextEdit
)
from PyQt6.QtCore import Qt
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QLineEdit, QLabel, QComboBox,
    QPushButton, QFileDialog, QMessageBox, QHBoxLayout
)
import yaml
import os


class ReleaseBuilderApp(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("DWH Release Builder")
        self.resize(1200, 800)

        self.tabs = QTabWidget()
        self.file_upload_tab = FileUploadTab()
        self.anchors_masks_tab = AnchorUI()
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

class AnchorUI(QWidget):
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

        # Кнопки для работы с yaml
        btn_layout = QHBoxLayout()
        self.save_btn = QPushButton("Сохранить шаблон YAML")
        self.load_btn = QPushButton("Загрузить шаблон YAML")
        self.new_btn = QPushButton("Создать новый")
        btn_layout.addWidget(self.new_btn)
        btn_layout.addWidget(self.save_btn)
        btn_layout.addWidget(self.load_btn)
        layout.addLayout(btn_layout)

        self.anchor_input.textChanged.connect(self.update_preview)
        self.path_template_input.textChanged.connect(self.update_preview)
        self.save_btn.clicked.connect(self.save_to_yaml)
        self.load_btn.clicked.connect(self.load_from_yaml)
        self.new_btn.clicked.connect(self.new_template)

        self.setLayout(layout)

    def update_preview(self):
        example_vars = {
            'папка': 'models',
            'стрим': 'mis',
            'storage': 'gp',
            'schema': 'core',
            'obj': 'v_mis_patients'
        }
        template = self.path_template_input.text()
        if template:
            try:
                path = template.format(**example_vars)
                self.preview.setText(f"Пример: {path}")
            except Exception:
                self.preview.setText("Ошибка в шаблоне!")
        else:
            self.preview.setText("Пример пути появится здесь…")

    def save_to_yaml(self):
        anchor = self.anchor_input.text().strip()
        template = self.path_template_input.text().strip()
        if not anchor or not template:
            QMessageBox.warning(self, "Ошибка", "Заполните оба поля!")
            return

        data = {
            "anchor": anchor,
            "template": template
        }

        filename, _ = QFileDialog.getSaveFileName(self, "Сохранить YAML шаблон", filter="YAML Files (*.yaml *.yml)")
        if filename:
            if not filename.endswith('.yaml') and not filename.endswith('.yml'):
                filename += ".yaml"
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    yaml.dump(data, f, allow_unicode=True)
                QMessageBox.information(self, "Готово", f"Шаблон сохранён в:\n{filename}")
            except Exception as ex:
                QMessageBox.critical(self, "Ошибка сохранения", str(ex))

    def load_from_yaml(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Загрузить YAML шаблон", filter="YAML Files (*.yaml *.yml)")
        if filename and os.path.exists(filename):
            try:

                with open(filename, 'r', encoding='utf-8') as f:
                    data = yaml.safe_load(f)
                self.anchor_input.setText(data.get('anchor', ''))
                self.path_template_input.setText(data.get('template', ''))
                QMessageBox.information(self, "Загружено", "Шаблон успешно загружен.")
            except Exception as ex:
                QMessageBox.critical(self, "Ошибка загрузки", str(ex))

            def new_template(self):
                self.anchor_input.clear()
                self.path_template_input.clear()
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
