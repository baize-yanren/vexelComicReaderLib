import sys
import os
import json
from settings_dialog import SettingsDialog
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QToolBar, QAction, QSplitter, QListWidget,
                            QListWidgetItem, QLabel, QStatusBar, QDialog)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize

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
        settings_action = QAction(QIcon(os.path.join("resource", "icons", "text_edit_icon.png")), 
                                 self.i18n.get_text("main_window.toolbar.settings"), self)
        settings_action.triggered.connect(self.open_settings)
        self.toolbar.addAction(settings_action)

        # 导入漫画按钮
        import_action = QAction(QIcon(os.path.join("resource", "icons", "save_icon.png")), 
                               self.i18n.get_text("main_window.toolbar.import"), self)
        import_action.triggered.connect(self.import_comics)
        self.toolbar.addAction(import_action)

    def init_sidebar(self):
        # 添加侧边栏项
        items = [
            ("all_comics", " vexellogo.png"),
            ("recently_read", " clock_icon.png"),
            ("favorites", " save_icon.png"),
            ("categories", " painter_icon.png")
        ]

        for key, icon in items:
            item = QListWidgetItem(self.i18n.get_text(f"main_window.sidebar.{key}"))
            icon_path = os.path.join(os.path.dirname(__file__), "resource", "icons", icon.strip())
            item.setIcon(QIcon(icon_path))
            self.sidebar.addItem(item)

        self.sidebar.currentItemChanged.connect(self.on_sidebar_item_changed)

    def on_sidebar_item_changed(self, current, previous):
        if current:
            self.content_area.setText(f"显示 {current.text()} 内容")

    def import_comics(self):
        # 实现漫画导入功能
        self.status_bar.showMessage("导入漫画功能待实现")

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