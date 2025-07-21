import sys
import json
import os
from PyQt5.QtWidgets import (QDialog, QVBoxLayout, QHBoxLayout, QLabel, QComboBox, 
                            QPushButton, QWidget, QMessageBox, QRadioButton, QButtonGroup, QLineEdit, QFileDialog)
from PyQt5.QtCore import Qt

class SettingsDialog(QDialog):
    def __init__(self, i18n, parent=None):
        super().__init__(parent)
        self.i18n = i18n
        self.current_language = self.i18n.language
        self.initUI()

    def initUI(self):
        self.setWindowTitle(self.i18n.get_text("settings.title"))
        self.setMinimumWidth(300)

        # 创建主布局
        main_layout = QVBoxLayout()

        # 语言设置部分
        lang_layout = QHBoxLayout()
        lang_label = QLabel(self.i18n.get_text("settings.language.label"))
        self.lang_combo = QComboBox()
        
        # 加载可用语言
        self.load_available_languages()
        
        lang_layout.addWidget(lang_label)
        lang_layout.addWidget(self.lang_combo)
        
        # 添加到主布局
        main_layout.addLayout(lang_layout)

        # 主题设置部分
        theme_layout = QHBoxLayout()
        theme_label = QLabel(self.i18n.get_text("settings.theme.label"))
        
        self.theme_group = QButtonGroup(self)
        self.light_radio = QRadioButton(self.i18n.get_text("settings.theme.light"))
        self.dark_radio = QRadioButton(self.i18n.get_text("settings.theme.dark"))
        
        self.theme_group.addButton(self.light_radio, 0)
        self.theme_group.addButton(self.dark_radio, 1)
        
        # 加载当前主题设置
        # self.load_current_theme()
        
        theme_layout.addWidget(theme_label)
        theme_layout.addWidget(self.light_radio)
        theme_layout.addWidget(self.dark_radio)
        
        main_layout.addLayout(theme_layout)
        
        # 加载当前主题和库路径设置
        self.load_current_theme()
        
        # 添加空白分隔符
        main_layout.addSpacing(20)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        # 取消按钮
        cancel_btn = QPushButton(self.i18n.get_text("settings.buttons.cancel"))
        cancel_btn.clicked.connect(self.reject)
        
        # 保存按钮
        save_btn = QPushButton(self.i18n.get_text("settings.buttons.save"))
        save_btn.clicked.connect(self.save_settings)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)

    def load_available_languages(self):
        # 加载当前语言设置
        try:
            settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
                self.current_language = settings.get("language", "zh_CN")
        except Exception as e:
            print(f"加载语言设置失败: {e}")
            self.current_language = "zh_CN"
        
        # 添加可用语言
        languages = [
            ("zh_CN", self.i18n.get_text("settings.language.zh_CN")),
            ("en_US", self.i18n.get_text("settings.language.en_US"))
        ]
        
        for code, name in languages:
            self.lang_combo.addItem(name, code)
            if code == self.current_language:
                self.lang_combo.setCurrentIndex(self.lang_combo.count() - 1)

    def load_current_theme(self):
        # 加载当前主题设置
        try:
            with open('settings.json', 'r', encoding='utf-8') as f:
                settings = json.load(f)
                theme = settings.get('theme', 'light')
                if theme == 'dark':
                    self.dark_radio.setChecked(True)
                else:
                    self.light_radio.setChecked(True)
        except Exception as e:
            print(f"加载设置失败: {e}")
            self.light_radio.setChecked(True)
        
    def save_settings(self):
        # 获取选中的语言
        new_lang = self.lang_combo.currentData()
        
        # 获取选中的主题
        new_theme = "dark" if self.dark_radio.isChecked() else "light"
        
        # 更新设置文件
        try:
            # 使用绝对路径保存设置文件
            settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
            with open(settings_path, "r+", encoding="utf-8") as f:
                settings = json.load(f)
                settings["language"] = new_lang
                settings["theme"] = new_theme
                f.seek(0)
                json.dump(settings, f, indent=4, ensure_ascii=False)
                f.truncate()
        except Exception as e:
            QMessageBox.critical(self, self.i18n.get_text("settings.error.title"),
                                self.i18n.get_text("settings.error.save_failed").format(error=str(e)))
            return

        # 通知主窗口更新语言
        self.accept()