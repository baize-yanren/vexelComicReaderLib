import sys
import os
import json
import uuid
import zipfile
import shutil
from datetime import datetime
from settings_dialog import SettingsDialog
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QToolBar, QAction, QSplitter, QListWidget,
                            QListWidgetItem, QLabel, QStatusBar, QDialog, QFileDialog, QMessageBox)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, message='sipPyTypeDict() is deprecated')

class I18nManager:
    def __init__(self):
        self.language = "zh_CN"
        self.translations = {}
        self.load_settings()
        self.load_translations()

    def load_settings(self):
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
                self.language = settings.get("language", "zh_CN")
        except Exception as e:
            print(f"加载设置失败: {e}")

    def load_translations(self):
        try:
            lang_file = os.path.join(os.path.dirname(__file__), "resource", "i18n", f"{self.language}.json")
            with open(lang_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
        except Exception as e:
            print(f"加载语言文件失败: {e}")
            # 加载默认中文
            default_file = os.path.join(os.path.dirname(__file__), "resource", "i18n", "zh_CN.json")
            with open(default_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)

    def get_text(self, key):
        keys = key.split('.')
        result = self.translations
        for k in keys:
            if isinstance(result, dict):
                result = result.get(k, {})
            else:
                # 如果当前结果不是字典，无法继续解析，返回原始key
                return key
            if not result:
                return key
        return result

class ComicLibraryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.i18n = I18nManager()
        self.load_theme_settings()
        self.initUI()
        
    def load_theme_settings(self):
        # 加载主题设置并应用
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
                theme = settings.get("theme", "light")
                self.apply_theme(theme)
        except Exception as e:
            print(f"加载主题设置失败: {e}")
            self.apply_theme("light")
        
    def apply_theme(self, theme):
        # 应用主题样式
        if theme == "dark":
            self.setStyleSheet("QWidget { background-color: #333; color: white; }")
        else:
            self.setStyleSheet("")
        
    def initUI(self):
        # 设置窗口标题和大小
        self.setWindowTitle(self.i18n.get_text("main_window.title"))
        self.resize(1280, 720)

        # 设置窗口图标
        icon_path = os.path.join(os.path.dirname(__file__), 'resource', 'icons', 'vexellogo.png')
        self.setWindowIcon(QIcon(icon_path))

        # 创建工具栏
        self.create_toolbar()

        # 创建主布局
        main_widget = QWidget()
        self.setCentralWidget(main_widget)
        main_layout = QVBoxLayout(main_widget)

        # 创建分割器（3:7比例）
        self.splitter = QSplitter(Qt.Horizontal)
        # 设置初始分割比例（基于1280px宽度）
        self.splitter.setSizes([384, 896])

        # 左侧目录
        self.sidebar = QListWidget()
        self.init_sidebar()
        self.splitter.addWidget(self.sidebar)

        # 右侧内容区
        self.content_area = QLabel("漫画内容展示区")
        self.content_area.setAlignment(Qt.AlignCenter)
        self.content_area.setStyleSheet("background-color: #f0f0f0;")
        self.splitter.addWidget(self.content_area)

        main_layout.addWidget(self.splitter)

        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        self.status_bar.showMessage(self.i18n.get_text("main_window.status_bar.total_comics").format(count=0))

    def create_toolbar(self):
        self.toolbar = self.addToolBar("Main Toolbar")
        self.toolbar.setIconSize(QSize(24, 24))

        # 设置按钮
        settings_action = QAction(QIcon(os.path.join("resource", "icons", "settings.svg")), 
                                 self.i18n.get_text("main_window.toolbar.settings"), self)
        settings_action.triggered.connect(self.open_settings)
        self.toolbar.addAction(settings_action)

        # 导入漫画按钮
        import_action = QAction(QIcon(os.path.join("resource", "icons", "import.svg")), 
                               self.i18n.get_text("main_window.toolbar.import"), self)
        import_action.triggered.connect(self.import_comics)
        self.toolbar.addAction(import_action)

    def init_sidebar(self):
        # 添加侧边栏项
        items = [
            ("all_comics", ""),
            ("recently_read", "clock_icon.png"),
            ("favorites", "favourite.svg"),
            ("categories", "painter_icon.png")
        ]

        for key, icon in items:
            item = QListWidgetItem(self.i18n.get_text(f"main_window.sidebar.{key}"))
            icon_path = os.path.join(os.path.dirname(__file__), "resource", "icons", icon)
            item.setIcon(QIcon(icon_path))
            self.sidebar.addItem(item)

        self.sidebar.currentItemChanged.connect(self.on_sidebar_item_changed)

    def on_sidebar_item_changed(self, current, previous):
        if current:
            self.content_area.setText(f"显示 {current.text()} 内容")

    def import_comics(self):
        # 打开文件选择对话框，支持选择文件和文件夹
        options = QFileDialog.Options()
        options |= QFileDialog.DontUseNativeDialog
        dialog = QFileDialog(self, self.i18n.get_text("import.comic.title"), "", self.i18n.get_text("import.comic.filter"))
        dialog.setFileMode(QFileDialog.ExistingFile | QFileDialog.Directory)
        dialog.setOptions(options)

        if dialog.exec_():
            file_path = dialog.selectedFiles()[0]
        else:
            return

        if not file_path:
            return

        try:
            # 判断文件类型
            if os.path.isdir(file_path):
                self._import_folder(file_path)
            elif file_path.endswith(('.zip', '.rar', '.7z')):
                self._import_archive(file_path)
            else:
                QMessageBox.warning(self, self.i18n.get_text("import.error.title"),
                                   self.i18n.get_text("import.error.invalid_type"))
                return

            self.status_bar.showMessage(self.i18n.get_text("import.success"))
            QMessageBox.information(self, self.i18n.get_text("import.success.title"),
                                   self.i18n.get_text("import.success.message"))
        except Exception as e:
            self.status_bar.showMessage(self.i18n.get_text("import.failed"))
            QMessageBox.critical(self, self.i18n.get_text("import.error.title"),
                               f"{self.i18n.get_text("import.error.details")}: {str(e)}")

    def _import_folder(self, folder_path):
        # 获取文件夹信息
        folder_name = os.path.basename(folder_path)
        size = self._get_folder_size(folder_path)
        created_time = datetime.fromtimestamp(os.path.getctime(folder_path)).isoformat() + 'Z'
        modified_time = datetime.fromtimestamp(os.path.getmtime(folder_path)).isoformat() + 'Z'
        import_time = datetime.utcnow().isoformat() + 'Z'

        # 创建文件记录
        file_record = {
            "id": str(uuid.uuid4()),
            "basic_info": {
                "name": folder_name,
                "path": folder_path,
                "type": "folder",
                "size": size,
                "created_time": created_time,
                "modified_time": modified_time,
                "import_time": import_time
            },
            "metadata": {
                "tags": [],
                "favorite": False,
                "rating": 0,
                "custom_fields": {}
            }
        }

        self._update_record_json(file_record)

    def _import_archive(self, archive_path):
        # 获取压缩包信息
        archive_name = os.path.basename(archive_path)
        size = os.path.getsize(archive_path)
        created_time = datetime.fromtimestamp(os.path.getctime(archive_path)).isoformat() + 'Z'
        modified_time = datetime.fromtimestamp(os.path.getmtime(archive_path)).isoformat() + 'Z'
        import_time = datetime.datetime.now(datetime.UTC).isoformat() + 'Z'
        archive_type = os.path.splitext(archive_path)[1][1:].lower()

        # 检查是否安装了必要的压缩包处理库
        try:
            import patoolib
            from patoolib.util import PatoolError
        except ImportError:
            raise Exception(self.i18n.get_text("import.error.missing_library").format(library="patoolib"))

        # 检查压缩包是否有效
        try:
            patoolib.test_archive(archive_path)
        except PatoolError as e:
            raise Exception(self.i18n.get_text("import.error.invalid_archive").format(type=archive_type, error=str(e)))

        # 创建文件记录
        file_record = {
            "id": str(uuid.uuid4()),
            "basic_info": {
                "name": archive_name,
                "path": archive_path,
                "type": "archive",
                "size": size,
                "created_time": created_time,
                "modified_time": modified_time,
                "import_time": import_time,
                "archive_type": archive_type
            },
            "metadata": {
                "tags": [],
                "favorite": False,
                "rating": 0,
                "custom_fields": {}
            }
        }

        self._update_record_json(file_record)

    def _get_folder_size(self, folder_path):
        total_size = 0
        for dirpath, dirnames, filenames in os.walk(folder_path):
            for f in filenames:
                fp = os.path.join(dirpath, f)
                total_size += os.path.getsize(fp)
        return total_size

    def _update_record_json(self, file_record):
        record_path = os.path.join(os.path.dirname(__file__), 'lib', 'record.json')

        # 读取现有记录
        try:
            with open(record_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            data = {"version": "1.0", "files": []}

        # 添加新记录
        data["files"].append(file_record)

        # 写入更新后的记录
        with open(record_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def open_settings(self):
        dialog = SettingsDialog(self.i18n, self)
        if dialog.exec_() == QDialog.Accepted:
            # 重新加载语言
            self.i18n.load_settings()
            self.i18n.load_translations()
            self.update_ui_text()


    def update_ui_text(self):
        self.setWindowTitle(self.i18n.get_text("main_window.title"))
        self.status_bar.showMessage(self.i18n.get_text("main_window.status_bar.total_comics").format(count=0))
        
        # 重新应用主题以确保样式正确
        self.load_theme_settings()
        
        # 更新工具栏文本
        actions = self.toolbar.actions()
        actions[0].setText(self.i18n.get_text("main_window.toolbar.import"))
        actions[1].setText(self.i18n.get_text("main_window.toolbar.settings"))

        # 更新侧边栏文本
        for i in range(self.sidebar.count()):
            item_key = ["all_comics", "recently_read", "favorites", "categories"][i]
            self.sidebar.item(i).setText(self.i18n.get_text(f"main_window.sidebar.{item_key}"))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        splitter_width = self.splitter.width()
        if splitter_width > 0:
            left_width = int(splitter_width * 0.3)
            right_width = splitter_width - left_width
            self.splitter.setSizes([left_width, right_width])

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ComicLibraryWindow()
    window.show()
    sys.exit(app.exec_())