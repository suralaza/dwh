#точка входа
import sys
from PyQt6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout, QTabWidget,
    QLabel, QHBoxLayout, QPushButton, QListWidget, QFileDialog, QTextEdit
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
        layout = QVBoxLayout()
        label = QLabel("Добавьте и настройте якоря и маски файлов")
        layout.addWidget(label)
        # Будет реализовано:
        # - таблица якорей
        # - редактор масок
        # - кнопки добавить/удалить
        self.setLayout(layout)

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
