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
        
        # 库路径设置部分
        library_layout = QHBoxLayout()
        library_label = QLabel(self.i18n.get_text("settings.library_path.label"))
        self.library_path_edit = QLineEdit()
        browse_btn = QPushButton(self.i18n.get_text("settings.library_path.browse"))
        browse_btn.clicked.connect(self.browse_library_path)
        
        library_layout.addWidget(library_label)
        library_layout.addWidget(self.library_path_edit)
        library_layout.addWidget(browse_btn)
        
        main_layout.addLayout(library_layout)
        
        # 加载当前主题和库路径设置
        self.load_current_theme()
        
        # 添加空白分隔符
        main_layout.addSpacing(20)
        
        # 按钮区域
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        # 取消按钮
        cancel_btn = QPushButton(self.i18n.get_text("settings.cancel"))
        cancel_btn.clicked.connect(self.reject)
        
        # 保存按钮
        save_btn = QPushButton(self.i18n.get_text("settings.save"))
        save_btn.clicked.connect(self.save_settings)
        
        btn_layout.addWidget(cancel_btn)
        btn_layout.addWidget(save_btn)
        
        main_layout.addLayout(btn_layout)
        
        self.setLayout(main_layout)

    def load_available_languages(self):
        # 这里应该从i18n目录读取可用语言
        # 简化实现，直接添加已知语言
        languages = [
            ("zh_CN", self.i18n.get_text("settings.language.zh_CN")),
            ("en_US", self.i18n.get_text("settings.language.en_US"))
        ]
        
        for code, name in languages:
            self.lang_combo.addItem(name, code)
            if code == self.current_language:
                self.lang_combo.setCurrentIndex(self.lang_combo.count() - 1)

    def load_current_theme(self):
        # 从设置文件加载当前主题
        try:
            with open("settings.json", "r", encoding="utf-8") as f:
                settings = json.load(f)
                theme = settings.get("theme", "light")
                if theme == "dark":
                    self.dark_radio.setChecked(True)
                else:
                    self.light_radio.setChecked(True)
                
                # 加载库路径设置
                default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
                self.library_path = settings.get("library_path", default_path)
                self.library_path_edit.setText(self.library_path)
                
                # 确保默认目录存在
                if not os.path.exists(self.library_path):
                    os.makedirs(self.library_path)
        except Exception as e:
            print(f"加载设置失败: {e}")
            self.light_radio.setChecked(True)
            # 设置默认库路径
            default_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "lib")
            self.library_path_edit.setText(default_path)
            if not os.path.exists(default_path):
                os.makedirs(default_path)
        
    def save_settings(self):
        # 获取选中的语言
        new_lang = self.lang_combo.currentData()
        
        # 获取选中的主题
        new_theme = "dark" if self.dark_radio.isChecked() else "light"
        
        # 获取库路径
        new_library_path = self.library_path_edit.text()
        
        # 更新设置文件
        try:
            with open("settings.json", "r+", encoding="utf-8") as f:
                settings = json.load(f)
                settings["language"] = new_lang
                settings["theme"] = new_theme
                settings["library_path"] = new_library_path
                f.seek(0)
                json.dump(settings, f, indent=4, ensure_ascii=False)
                f.truncate()
                
                # 确保库目录存在
                if not os.path.exists(new_library_path):
                    os.makedirs(new_library_path)
        except Exception as e:
            QMessageBox.critical(self, self.i18n.get_text("settings.error.title"),
                                self.i18n.get_text("settings.error.save_failed").format(error=str(e)))
            return

            # 通知主窗口更新语言
            self.accept()
        else:
            self.accept()

    def browse_library_path(self):
        path = QFileDialog.getExistingDirectory(self, self.i18n.get_text("settings.library_path.browse_title"), self.library_path_edit.text())
        if path:
            self.library_path_edit.setText(path)