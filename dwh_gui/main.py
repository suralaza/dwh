import sys,os
import json
from PyQt6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QStackedWidget, QListWidget, QFileDialog,
    QApplication, QMainWindow, QFormLayout, QLineEdit, QTextEdit, QMessageBox, QHeaderView, QListWidgetItem,
    QMenu, QTableWidget, QTableWidgetItem, QTabWidget, QInputDialog,QCheckBox, QGroupBox,
    QTreeWidget,
    QTreeWidgetItem,  QPushButton, QComboBox, QScrollArea
)
from PyQt6.QtCore import Qt, pyqtSignal


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


DEFAULTTYPES = ["doc", "service", "src", "other"]
ANCHORVARIABLES = 'header', 'footer'

class AnchorVariableWidget(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.layout = QHBoxLayout(self)
        self.nameinput = QLineEdit()
        self.nameinput.setPlaceholderText("Название переменной")
        self.startswithinput = QLineEdit()
        self.startswithinput.setPlaceholderText("Начинается с...")
        self.layout.addWidget(QLabel("Переменная"))
        self.layout.addWidget(self.nameinput)
        self.layout.addWidget(QLabel("Начинается с"))
        self.layout.addWidget(self.startswithinput)
        self.setLayout(self.layout)
    def get(self):
        return {
            "name": self.nameinput.text(),
            "startswith": self.startswithinput.text()
        }
    def set(self, data):
        self.nameinput.setText(data.get("name", ""))
        self.startswithinput.setText(data.get("startswith", ""))

class RuleFormWidget(QGroupBox):
    def __init__(self, parent=None):
        super().__init__("Параметры папки", parent)
        layout = QVBoxLayout(self)
        # Тип объекта
        self.typebox = QComboBox()
        self.typebox.addItems(DEFAULTTYPES)
        layout.addWidget(QLabel("Тип объекта"))
        layout.addWidget(self.typebox)

        # Якорь парсера
        self.anchorinput = QLineEdit()
        self.anchorinput.setPlaceholderText("Якорь парсера")
        layout.addWidget(QLabel("Якорь парсера"))
        layout.addWidget(self.anchorinput)

        # Переменные header/footer
        varlayout = QVBoxLayout()
        self.varcheckboxes = {}
        self.varlineedits = {}
        for v in ANCHORVARIABLES:
            hl = QHBoxLayout()
            cb = QCheckBox()
            le = QLineEdit()
            le.setPlaceholderText(f"Шаблон для {v}")
            hl.addWidget(cb)
            hl.addWidget(QLabel(v))
            hl.addWidget(le)
            self.varcheckboxesv = cb
            self.varlineedits[v] = le
            varlayout.addLayout(hl)
        layout.addWidget(QLabel("Переменные"))
        layout.addLayout(varlayout)

        # Переменные якоря: кнопка добавить, список и кнопка очистить
        self.anchorvars = []
        self.anchorvarlayout = QVBoxLayout()
        anchorgroup = QGroupBox("Переменные якоря")
        anchorgroup.setLayout(self.anchorvarlayout)
        addbtn = QPushButton("Добавить переменную якоря")
        addbtn.clicked.connect(self.addanchorvar)
        clearbtn = QPushButton("Очистить переменные якоря")
        clearbtn.clicked.connect(self.clearanchorvars)
        btnhbox = QHBoxLayout()
        btnhbox.addWidget(addbtn)
        btnhbox.addWidget(clearbtn)
        layout.addWidget(anchorgroup)
        layout.addLayout(btnhbox)
        self.setLayout(layout)
    def addanchorvar(self):
        w = AnchorVariableWidget()
        self.anchorvarlayout.addWidget(w)
        self.anchorvars.append(w)
    def clearanchorvars(self):
        for w in self.anchorvars:
            w.setParent(None)
        self.anchorvars.clear()
    def getdata(self):
        return {
            "type": self.typebox.currentText(),
            "anchor": self.anchorinput.text(),
            "variables": {
                v: {
                    "use": self.varcheckboxesv.isChecked(),
                    "template": self.varlineedits[v].text()
                } for v in ANCHORVARIABLES
            },
            "anchorvars": [w.get() for w in self.anchorvars]
        }

    def setdata(self, data):
        self.typebox.setCurrentText(data.get("type", DEFAULTTYPES[0]))
        self.anchorinput.setText(data.get("anchor", ""))
        varsdata = data.get("variables", {})
        for v in ANCHORVARIABLES:
            dct = varsdata.get(v, {})
            self.varcheckboxesv.setChecked(dct.get("use", False))
            self.varlineedits[v].setText(dct.get("template", ""))
        self.clearanchorvars()
        for vdict in data.get("anchorvars", ):
            self.addanchorvar()
            self.anchorvars[-1].set(vdict)

class RulesTab(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.projectfolder = ""
        self.folderforms = {}  # путь: RuleFormWidget

        mainlayout = QHBoxLayout(self)

        # Слева — меню действий
        self.menu = QListWidget()
        self.menu.addItem("Репозиторий Git")
        self.menu.addItem("Редактировать правила")
        self.menu.addItem("Очистить правила")
        self.menu.addItem("Сохранить в Yaml")
        self.menu.addItem("Загрузить из Yaml")
        self.menu.currentRowChanged.connect(self.menuaction)
        self.menu.setMaximumWidth(220)
        mainlayout.addWidget(self.menu)

        # Справа — дерево и параметры
        self.rightvbox = QVBoxLayout()
        # Дерево папок/файлов
        self.tree = QTreeWidget()
        self.tree.setHeaderLabels(["Папка / файл", "Параметры"])
        self.tree.itemSelectionChanged.connect(self.onitemselected)
        self.rightvbox.addWidget(self.tree, stretch=3)
        # Под деревом — скролл для формы активной папки
        self.scroll = QScrollArea()
        self.scroll.setWidgetResizable(True)
        self.formarea = QWidget()
        self.vboxform = QVBoxLayout(self.formarea)
        self.scroll.setWidget(self.formarea)
        self.rightvbox.addWidget(self.scroll, stretch=2)
        mainlayout.addLayout(self.rightvbox)
        self.setLayout(mainlayout)

    def menuaction(self, index):
        if index == 0:  # Репозиторий Git
            folder = QFileDialog.getExistingDirectory(self, "Выберите папку репозитория Git")
            if not folder: return
            self.projectfolder = folder
            self.loadtree()
        elif index == 1:  # Редактировать правила
            self.expandtreeall()
        elif index == 2:  # Очистить правила
            if QMessageBox.question(self, "Очистка", "Удалить все правила?") != QMessageBox.StandardButton.Yes:
                return
            for w in self.folderforms.values():
                w.setdata({})
        elif index == 3:  # Сохранить в Json
            path, = QFileDialog.getSaveFileName(self, "Сохранить структуру", "", "JSON (.json)")
            if path:
                self.save_to_json(path)
        elif index == 4:  # Загрузить из Json
            path, _ = QFileDialog.getOpenFileName(self, "Загрузить структуру", "", "JSON (.json)")
            if path:
                self.loadfromjson(path)
        self.menu.clearSelection()

    def loadtree(self):
        self.tree.clear()
        self.folderforms.clear()

        def additems(parentitem, currentpath):
            for name in sorted(os.listdir(currentpath)):
                fullpath = os.path.join(currentpath, name)
                isdir = os.path.isdir(fullpath)
                item = QTreeWidgetItem([name])
                parentitem.addChild(item)
                # форма только к папкам
                if isdir:
                    relpath = os.path.relpath(fullpath, self.projectfolder)
                    w = RuleFormWidget()
                    self.folderformsrel_path = w
                    item.setData(0, Qt.ItemDataRole.UserRole, relpath)
                    additems(item, fullpath)
        rootitem = QTreeWidgetItem(os.path.basename(self.project_folder))
        w = RuleFormWidget()
        self.folderforms["."] = w
        rootitem.setData(0, Qt.ItemDataRole.UserRole, ".")
        additems(rootitem, self.projectfolder)
        self.tree.addTopLevelItem(rootitem)
        rootitem.setExpanded(True)
        self.tree.setCurrentItem(rootitem)
        self.onitemselected()

    def onitemselected(self):
        print("Выбран элемент в дереве!")

    def expandtreeall(self):
        def recexpand(item):
            item.setExpanded(True)
            for i in range(item.childCount()):
                recexpand(item.child(i))

class SettingsTab(QWidget):
    """Вкладка Настройки без меню Подключения!"""
    def __init__(self):
        super().__init__()
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
        #сохранить в csv
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
        #сохранить в csv
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
