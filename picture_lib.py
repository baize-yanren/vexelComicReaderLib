'''
@version 1.0
@brief 库管理前端主代码
@author 炎刃
@date 2025-07-24
'''

import os
import datetime
import sys
import os
import json
import datetime
import uuid
import zipfile
import shutil
from datetime import datetime
from settings_dialog import SettingsDialog
from lib_func import I18nManager, format_file_size, ComicLibraryUtils
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QGroupBox, QPushButton, QFileDialog, QMessageBox, 
                            QHBoxLayout, QToolBar, QAction, QSplitter, QTableWidget,
                            QTableWidgetItem, QLabel, QStatusBar, QDialog, QFileDialog, QMessageBox, QAbstractItemView, QHeaderView, QInputDialog, QLineEdit)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize, QFileInfo, QDir
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, message='sipPyTypeDict() is deprecated')



class ComicLibraryWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.all_records = []
        self.libraries = []
        try:
            self.libraries = ComicLibraryUtils.load_libraries_config() or []
        except Exception as e:
            print(f"加载库配置失败: {e}")
            self.libraries = []
        self.scan_all_libraries()
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
        
    def scan_all_libraries(self):
        # 扫描所有库并收集记录
        self.all_records = []
        for lib in self.libraries:
            lib_path = lib.get('path')
            if lib_path and os.path.exists(lib_path):
                # 调用工具类扫描库内容
                records = ComicLibraryUtils.scan_library(lib_path)
                self.all_records.extend(records)

    def open_comic_file(self, index):
        if index.isValid():
            item = self.right_content.item(index.row(), 0)
            if item:
                file_path = item.data(Qt.UserRole)
                if file_path and os.path.exists(file_path):
                    from picture_browser import ComicBrowser
                    self.browser = ComicBrowser(file_path)
                    self.browser.show()
    
    def initUI(self):
        self.setWindowTitle(self.i18n.get_text('main_window.title'))
        self.setWindowIcon(QIcon(os.path.join('resource', 'icons', 'vexellogo.png')))
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中心部件和布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 提前初始化右侧内容区域，确保属性存在
        self.right_content = QTableWidget()
        self.right_content.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 创建主分割器
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        # 添加列标题
        self.right_content.setColumnCount(3)
        # 使用国际化文本设置表格列标题
        self.right_content.setHorizontalHeaderLabels([
            self.i18n.get_text('main_window.table.name'),
            self.i18n.get_text('main_window.table.modified_date'),
            self.i18n.get_text('main_window.table.size')
        ])
        # 设置表格属性
        self.right_content.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.right_content.verticalHeader().setVisible(False)
        self.right_content.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.right_content.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.right_content.doubleClicked.connect(self.open_comic_file)
        
        # 初始化侧边栏
        self.init_sidebar()
        
        # 将侧边栏和内容区域添加到分割器
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.right_content)
        
        # 设置分割器初始大小
        self.splitter.setSizes([300, 900])
        
        # 连接库列表选择事件
        self.library_list.itemClicked.connect(self.on_library_selected)
        # 初始加载所有漫画
        # 确保从配置加载库并刷新UI
        self.libraries = ComicLibraryUtils.load_libraries_config()
        self.refresh_ui_text()
        self.scan_all_libraries()
        self.load_library_files()
    
        # 重新应用主题以确保样式正确
        self.load_theme_settings()
        


        # 更新侧边栏文本 - 修复QWidget没有count()方法的错误
        # 假设原始侧边栏项目现在位于library_list中
        if hasattr(self, 'library_list') and isinstance(self.library_list, QListWidget):
            item_keys = ["all_comics", "recently_read"]
            for i in range(min(len(item_keys), self.library_list.count())):
                item_key = item_keys[i]
                # 确保使用正确的国际化文本更新侧边栏项目
                self.library_list.item(i).setText(self.i18n.get_text(f"main_window.sidebar.{item_key}"))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        splitter_width = self.splitter.width()
        if splitter_width > 0:
            left_width = int(splitter_width * 0.3)
            right_width = splitter_width - left_width
            self.splitter.setSizes([left_width, right_width])

    def add_library(self):
        dir_path = QFileDialog.getExistingDirectory(self, self.i18n.get_text('settings.dialog.select_library'), QDir.homePath())
        if not dir_path:
            return
        
        lib_name = os.path.basename(dir_path)
        # 检查是否已存在
        for lib in self.libraries:
            if lib['path'] == dir_path:
                QMessageBox.warning(self, self.i18n.get_text('settings.error.title'), self.i18n.get_text('settings.error.library_exists'))
                return
        
        # 调用ComicLibraryUtils创建新库
        success = ComicLibraryUtils.create_new_library(dir_path)
        if not success:
            QMessageBox.warning(self, self.i18n.get_text('settings.error.title'), self.i18n.get_text('settings.error.library_creation_failed'))
            return
        
        # 更新配置
        self.libraries.append({'name': lib_name, 'path': dir_path})
        ComicLibraryUtils.save_libraries_config(self.libraries)
        
        # 更新列表
        # 刷新库列表并保留默认分类
        self.libraries = ComicLibraryUtils.load_libraries_config()
        self.library_list.clear()
        
        # 重新添加默认分类
        default_categories = [
            self.i18n.get_text('main_window.sidebar.all_comics'),
            self.i18n.get_text('main_window.sidebar.recently_read')
        ]
        # 使用zip确保分类与键一一对应，避免索引错误
        item_keys = ["all_comics", "recently_read"]
        for cat, key in zip(default_categories, item_keys):
            item = QListWidgetItem(cat)
            item.setData(Qt.UserRole, key)
            self.library_list.addItem(item)
        
        # 添加用户库
        for lib in self.libraries:
            item = QListWidgetItem(lib['name'])
            item.setData(Qt.UserRole, lib['path'])
            self.library_list.addItem(item)
        self.scan_all_libraries()

    def load_special_category(self, category):
        # 实现特殊分类加载逻辑
        self.right_content.setRowCount(0)
        if category == 'all_comics':
            # 加载所有漫画
            self.load_library_files()
        elif category == 'recently_read':
            # 加载最近阅读
            recent_records = [r for r in self.all_records if r.get('last_read')]
            recent_records.sort(key=lambda x: x.get('last_read', 0), reverse=True)
            self.populate_table(recent_records)

    def load_library_contents(self, lib_path):
        # 实现库内容加载逻辑
        self.right_content.setRowCount(0)
        lib_records = [r for r in self.all_records if r.get('library_path') == lib_path]
        self.populate_table(lib_records)

    def populate_table(self, records):
        # 通用表格填充方法
        for record in records:
            file_path = record.get('full_path')
            if not file_path or not os.path.exists(file_path):
                continue
            file_info = QFileInfo(file_path)
            file_name = record.get('name', file_info.fileName())
            modified_time = record.get('modified_time', '未知时间')
            if isinstance(modified_time, (int, float)):
                modified_time = datetime.datetime.fromtimestamp(modified_time).strftime('%Y-%m-%d %H:%M:%S')
            file_size = format_file_size(record.get('size', 0))
            row = self.right_content.rowCount()
            self.right_content.insertRow(row)
            name_item = QTableWidgetItem(file_name)
            name_item.setData(Qt.UserRole, file_path)
            self.right_content.setItem(row, 0, name_item)
            date_item = QTableWidgetItem(modified_time)
            date_item.setTextAlignment(Qt.AlignCenter)
            self.right_content.setItem(row, 1, date_item)
            size_item = QTableWidgetItem(file_size)
            size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.right_content.setItem(row, 2, size_item)

    def on_library_selected(self, current, previous):
        if current:
            # 获取选中的库路径
            lib_path = current.data(Qt.UserRole)
            if lib_path in ['all_comics', 'recently_read']:
                # 处理特殊分类
                self.load_special_category(lib_path)
            else:
                # 加载具体库内容
                self.load_library_contents(lib_path)

    def edit_library_name(self, item):
        # 获取当前库信息
        current_name = item.text()
        lib_path = item.data(Qt.UserRole)
        if not lib_path or lib_path in ['all_comics', 'recently_read']:
            return

        # 显示输入对话框
        new_name, ok = QInputDialog.getText(self, self.i18n.get_text('settings.edit_library'),
                                           self.i18n.get_text('settings.enter_new_name'),
                                           QLineEdit.Normal, current_name)

        if ok and new_name and new_name != current_name:
            # 更新内存中的库配置
            for lib in self.libraries:
                if lib['path'] == lib_path:
                    lib['name'] = new_name
                    break

            # 更新UI显示
            item.setText(new_name)
            # 保存配置
            ComicLibraryUtils.save_libraries_config(self.libraries)

    def on_collection_item_changed(self, current, previous):
        if current:
            # 处理标签项选择变化
            tag_text = current.text()
            # 可以在这里添加过滤或更新显示逻辑
            pass

    def init_sidebar(self):
        # 创建侧边栏部件
        self.sidebar = QWidget()
        sidebar_layout = QVBoxLayout(self.sidebar)
        sidebar_layout.setContentsMargins(5, 5, 5, 5)
        sidebar_layout.setSpacing(10)

        # 1. 库管理部分
        self.library_group = QGroupBox("库管理")
        library_layout = QVBoxLayout()
        self.library_list = QListWidget()
        self.add_library_btn = QPushButton("+ 添加库")
        self.add_library_btn.clicked.connect(self.add_library)
        library_layout.addWidget(self.library_list)
        library_layout.addWidget(self.add_library_btn)
        self.library_group.setLayout(library_layout)

        # 2. 标签管理部分
        self.tag_group = QGroupBox("标签管理")
        tag_layout = QVBoxLayout()
        self.tag_list = QListWidget()
        # 添加收藏列表
        self.favorite_item = QListWidgetItem("收藏")
        self.favorite_item.setData(Qt.UserRole, "favorites")
        self.tag_list.addItem(self.favorite_item)
        # 连接标签列表点击事件
        self.tag_list.currentItemChanged.connect(self.on_collection_item_changed)
        tag_layout.addWidget(self.tag_list)
        self.tag_group.setLayout(tag_layout)

        # 添加到主布局
        sidebar_layout.addWidget(self.library_group)
        sidebar_layout.addWidget(self.tag_group)

        # 加载库配置
        self.libraries = ComicLibraryUtils.load_libraries_config()
        # 连接信号
        self.library_list.currentItemChanged.connect(self.on_library_selected)
        # 启用库名称双击编辑
        self.library_list.itemDoubleClicked.connect(self.edit_library_name)
        self.library_list.setEditTriggers(QAbstractItemView.NoEditTriggers)


    def create_toolbar(self):
        self.toolbar = self.addToolBar('Main Toolbar')
        self.toolbar.setIconSize(QSize(24, 24))
        
        # 设置按钮
        self.settings_action = QAction(QIcon(os.path.join('resource', 'icons', 'settings.svg')), '', self)
        self.settings_action.triggered.connect(self.open_settings_dialog)
        self.toolbar.addAction(self.settings_action)
        
        # 导入漫画按钮
        self.import_action = QAction(QIcon(os.path.join('resource', 'icons', 'import.svg')), '', self)
        self.import_action.triggered.connect(self.import_comics)
        self.toolbar.addAction(self.import_action)
        
        return self.toolbar
    
    def open_settings_dialog(self):
        dialog = SettingsDialog(self.i18n, self)
        if dialog.exec_() == QDialog.Accepted:
            # 重新加载语言设置
            self.i18n.load_settings()
            self.i18n.load_translations()
            # 刷新UI文本
            self.refresh_ui_text()
    

    
    def refresh_ui_text(self):
        # 更新窗口标题
        self.setWindowTitle(self.i18n.get_text('main_window.title'))
        
        # 更新工具栏文本
        actions = self.toolbar.actions()
        actions[0].setText(self.i18n.get_text('main_window.toolbar.settings'))
        actions[1].setText(self.i18n.get_text('main_window.toolbar.import'))
        
        # 更新侧边栏文本 - 仅更新前4个固定项
        if hasattr(self, 'library_list') and isinstance(self.library_list, QListWidget):
            # 只更新前4个固定分类项，不更新实际库名称
            # 仅更新现有固定分类项，与item_key列表长度匹配
            item_keys = ['all_comics', 'recently_read']
            for i in range(min(len(item_keys), self.library_list.count())):
                item_key = item_keys[i]
                self.library_list.item(i).setText(self.i18n.get_text(f'main_window.sidebar.{item_key}'))
            
            # 移除现有库项（第4项之后的所有项）
            # 仅保留固定分类项，移除多余库项
            while self.library_list.count() > len(item_keys):
                self.library_list.takeItem(self.library_list.count() - 1)
            
            # 添加库列表
            libraries = ComicLibraryUtils.load_libraries_config()
            for lib in libraries:
                lib_path = lib['path']
                # 基于路径生成稳定的库ID
                lib_id = str(uuid.uuid5(uuid.NAMESPACE_URL, lib_path))
                item = QListWidgetItem(lib['name'])
                item.setData(Qt.UserRole, lib_id)
                self.library_list.addItem(item)
        
        # 更新表格标题
        if hasattr(self, 'right_content'):
            self.right_content.setHorizontalHeaderLabels([
                self.i18n.get_text('main_window.table.name'),
                self.i18n.get_text('main_window.table.modified_date'),
                self.i18n.get_text('main_window.table.size')
            ])
        
        # 更新状态栏文本
        if hasattr(self, 'total_comics'):
            self.statusBar().showMessage(self.i18n.get_text('main_window.status_bar.total_comics').format(count=self.total_comics))
        
        # 更新导入对话框标题
        if hasattr(self, 'import_action'):
            self.import_action.setText(self.i18n.get_text('main_window.toolbar.import'))
        
        # 更新设置对话框标题
        if hasattr(self, 'settings_action'):
            self.settings_action.setText(self.i18n.get_text('main_window.toolbar.settings'))

    def load_library_files(self, category=None, library_id=None):
        self.right_content.clear()
        if not hasattr(self, 'all_records'):
            self.statusBar().showMessage('未找到记录数据')
            return
            
        # 使用工具类筛选记录
        records = ComicLibraryUtils.filter_records_by_library(
            self.all_records,
            library_id=library_id,
            category=category
        )
            
        self.statusBar().showMessage(f'共找到 {len(records)} 个文件')
        
        # 使用通用表格填充方法处理所有记录
        self.populate_table(records)
        
        # 调整列宽
        self.right_content.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
    
    def on_sidebar_item_changed(self, current, previous):
        if current:
            # 根据选择的侧边栏项筛选显示内容
            item_text = current.text()
            if item_text == self.i18n.get_text("main_window.sidebar.all_comics"):
                self.load_library_files()  # 显示所有文件
            else:
                # 其他筛选逻辑可以在这里添加
                self.right_content.setRowCount(0)
                self.right_content.insertRow(0)
                self.right_content.setItem(0, 0, QTableWidgetItem(f"显示 {item_text} 内容"))

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
        record_path = os.path.join(os.path.dirname(__file__), 'resource', 'record.json')

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

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ComicLibraryWindow()
    window.show()
    sys.exit(app.exec_())

    def create_toolbar(self):
        self.toolbar = self.addToolBar('Main Toolbar')
        self.toolbar.setIconSize(QSize(24, 24))
        
        # 设置按钮
        self.settings_action = QAction(QIcon(os.path.join('resource', 'icons', 'settings.svg')), '设置', self)
        self.settings_action.triggered.connect(self.open_settings)
        self.toolbar.addAction(self.settings_action)
        
        # 导入漫画按钮
        self.import_action = QAction(QIcon(os.path.join('resource', 'icons', 'import.svg')), '导入漫画', self)
        self.import_action.triggered.connect(self.import_comic)
        self.toolbar.addAction(self.import_action)
        
        # 更新工具栏文本
        actions = self.toolbar.actions()
        actions[0].setText(self.i18n.get_text("main_window.toolbar.import"))
        actions[1].setText(self.i18n.get_text("main_window.toolbar.settings"))

        # 更新侧边栏文本
        for i in range(self.sidebar.count()):
            item_key = ["all_comics", "recently_read"][i]
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

    def create_toolbar(self):
        self.toolbar = self.addToolBar('Main Toolbar')
        self.toolbar.setIconSize(QSize(24, 24))
        
        # 设置按钮
        self.settings_action = QAction(QIcon(os.path.join('resource', 'icons', 'settings.svg')), '设置', self)
        self.settings_action.triggered.connect(self.open_settings)
        self.toolbar.addAction(self.settings_action)
        
        # 导入漫画按钮
        self.import_action = QAction(QIcon(os.path.join('resource', 'icons', 'import.svg')), '导入漫画', self)
        self.import_action.triggered.connect(self.import_comic)
        self.toolbar.addAction(self.import_action)
        
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

    def create_toolbar(self):
        self.toolbar = self.addToolBar('Main Toolbar')
        self.toolbar.setIconSize(QSize(24, 24))
        
        # 设置按钮
        self.settings_action = QAction(QIcon(os.path.join('resource', 'icons', 'settings.svg')), '设置', self)
        self.settings_action.triggered.connect(self.open_settings)
        self.toolbar.addAction(self.settings_action)
        
        # 导入漫画按钮
        self.import_action = QAction(QIcon(os.path.join('resource', 'icons', 'import.svg')), '导入漫画', self)
        self.import_action.triggered.connect(self.import_comic)
        self.toolbar.addAction(self.import_action)
        
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