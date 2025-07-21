import sys
import os
import json
import uuid
import zipfile
import shutil
from datetime import datetime
from settings_dialog import SettingsDialog
from lib_func import I18nManager, format_file_size, ComicLibraryUtils
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QListWidget, QListWidgetItem, QGroupBox, QPushButton, QFileDialog, QMessageBox, 
                            QHBoxLayout, QToolBar, QAction, QSplitter, QTableWidget,
                            QTableWidgetItem, QLabel, QStatusBar, QDialog, QFileDialog, QMessageBox, QAbstractItemView, QHeaderView)
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import Qt, QSize, QFileInfo
import warnings
warnings.filterwarnings('ignore', category=DeprecationWarning, message='sipPyTypeDict() is deprecated')



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
        self.setWindowTitle(self.i18n.get_text('main_window.title'))
        self.setGeometry(100, 100, 1200, 800)
        
        # 创建中心部件和布局
        self.central_widget = QWidget()
        self.setCentralWidget(self.central_widget)
        self.main_layout = QVBoxLayout(self.central_widget)
        
        # 创建工具栏
        self.create_toolbar()
        
        # 创建状态栏
        self.status_bar = QStatusBar()
        self.setStatusBar(self.status_bar)
        
        # 创建主分割器
        self.splitter = QSplitter(Qt.Horizontal)
        self.main_layout.addWidget(self.splitter)
        
        # 初始化侧边栏
        self.init_sidebar()
        self.scan_all_libraries()
        
        # 设置右侧内容区域为QTableWidget
        self.right_content = QTableWidget()
        self.right_content.setSelectionMode(QAbstractItemView.ExtendedSelection)
        
        # 添加列标题
        self.right_content.setColumnCount(3)
        # 使用国际化文本设置表格列标题
        self.right_content.setHorizontalHeaderLabels([
            self.i18n.get_text('main_window.table.name'),
            self.i18n.get_text('main_window.table.modified_date'),
            self.i18n.get_text('main_window.table.size')
        ])
        
        # 将侧边栏和内容区域添加到分割器
        self.splitter.addWidget(self.sidebar)
        self.splitter.addWidget(self.right_content)
        
        # 设置分割器初始大小
        self.splitter.setSizes([300, 900])
        
        # 加载漫画库文件
        self.load_library_files()
    
        # 重新应用主题以确保样式正确
        self.load_theme_settings()
        


        # 更新侧边栏文本 - 修复QWidget没有count()方法的错误
        # 假设原始侧边栏项目现在位于library_list中
        if hasattr(self, 'library_list') and isinstance(self.library_list, QListWidget):
            for i in range(self.library_list.count()):
                item_key = ["all_comics", "recently_read", "favorites", "categories"][i]
                # 确保使用正确的国际化文本更新侧边栏项目
                self.library_list.item(i).setText(self.i18n.get_text(f"main_window.sidebar.{item_key}"))

    def resizeEvent(self, event):
        super().resizeEvent(event)
        splitter_width = self.splitter.width()
        if splitter_width > 0:
            left_width = int(splitter_width * 0.3)
            right_width = splitter_width - left_width
            self.splitter.setSizes([left_width, right_width])

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
        
        # 更新侧边栏文本
        if hasattr(self, 'library_list') and isinstance(self.library_list, QListWidget):
            for i in range(self.library_list.count()):
                item_key = ['all_comics', 'recently_read', 'favorites', 'categories'][i]
                self.library_list.item(i).setText(self.i18n.get_text(f'main_window.sidebar.{item_key}'))
        
        # 更新表格标题
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

    def load_library_files(self, category=None):
        self.right_content.clear()
        try:
            with open('lib/record.json', 'r', encoding='utf-8') as f:
                data = json.load(f)
                # 处理可能的JSON结构：直接是数组或包含在'records'键中
                records = data if isinstance(data, list) else data.get('records', [])
                
            if category and category != '全部':
                records = [r for r in records if isinstance(r, dict) and r.get('category') == category]
                
            self.statusBar().showMessage(f'共找到 {len(records)} 个文件')
            
            for record in records:
                file_path = record.get('path')
                if not file_path or not os.path.exists(file_path):
                    continue
                    
                # 获取文件信息
                file_info = QFileInfo(file_path)
                file_name = file_info.fileName()
                modified_time = file_info.lastModified().toString('yyyy-MM-dd HH:mm')
                file_size = format_file_size(file_info.size())
                
                # 创建表格项
                row = self.right_content.rowCount()
                self.right_content.insertRow(row)
                
                # 名称列
                name_item = QTableWidgetItem(file_name)
                name_item.setIcon(icon)
                name_item.setData(Qt.UserRole, file_path)
                self.right_content.setItem(row, 0, name_item)
                
                # 修改日期列
                date_item = QTableWidgetItem(modified_time)
                date_item.setTextAlignment(Qt.AlignCenter)
                self.right_content.setItem(row, 1, date_item)
                
                # 大小列
                size_item = QTableWidgetItem(file_size)
                size_item.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.right_content.setItem(row, 2, size_item)
                
            # 调整列宽
            self.right_content.horizontalHeader().setSectionResizeMode(QHeaderView.ResizeToContents)
                
        except Exception as e:
            self.statusBar().showMessage(f'加载文件失败: {str(e)}')
            print(f'Error loading library files: {e}')



    def init_sidebar(self):
        # 创建侧边栏主容器
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

        # 2. 作品集管理部分
        self.collection_group = QGroupBox("作品集管理")
        collection_layout = QVBoxLayout()
        self.collection_list = QListWidget()
        # 添加收藏列表
        self.favorite_item = QListWidgetItem("收藏列表")
        self.favorite_item.setData(Qt.UserRole, "favorites")
        self.collection_list.addItem(self.favorite_item)
        # 连接收藏列表点击事件
        self.collection_list.currentItemChanged.connect(self.on_collection_item_changed)
        collection_layout.addWidget(self.collection_list)
        self.collection_group.setLayout(collection_layout)

        # 3. 标签管理部分
        self.tag_group = QGroupBox("标签管理")
        tag_layout = QVBoxLayout()
        self.tag_list = QListWidget()
        tag_layout.addWidget(self.tag_list)
        self.tag_group.setLayout(tag_layout)

        # 添加到主布局
        sidebar_layout.addWidget(self.library_group)
        sidebar_layout.addWidget(self.collection_group)
        sidebar_layout.addWidget(self.tag_group)

        # 加载库配置
        self.load_libraries_config()
        # 连接信号
        self.library_list.currentItemChanged.connect(self.on_library_changed)
    
    def load_libraries_config(self):
        # 从lib-func加载库配置
        self.libraries = ComicLibraryUtils.load_libraries_config()
        
        # 更新库列表显示
        self.library_list.clear()
        for lib in self.libraries:
            item = QListWidgetItem(lib['name'])
            item.setData(Qt.UserRole, lib['path'])
            self.library_list.addItem(item)
    
    def add_library(self):
        # 添加新库
        dir_path = QFileDialog.getExistingDirectory(self, self.i18n.get_text('settings.library_path.browse_title'))
        if dir_path:
            lib_name = os.path.basename(dir_path)
            # 检查是否已存在
            for lib in self.libraries:
                if lib['path'] == dir_path:
                    QMessageBox.warning(self, self.i18n.get_text('settings.error.title'), self.i18n.get_text('settings.error.library_exists'))
                    return
            
            # 创建record.json
            record_path = os.path.join(dir_path, 'record.json')
            if not os.path.exists(record_path):
                with open(record_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
            
            # 更新配置
            self.libraries.append({'name': lib_name, 'path': dir_path})
            ComicLibraryUtils.save_libraries_config(self.libraries)
            
            # 更新列表
            self.load_libraries_config()
            self.scan_all_libraries()
    
    def scan_all_libraries(self):
        # 从lib-func扫描所有库
        self.all_records = ComicLibraryUtils.scan_all_libraries(self.libraries)
        
        # 更新作品集和标签
        self.update_collections_and_tags()
    
    def update_collections_and_tags(self):
        # 更新作品集和标签列表
        collections = set()
        tags = set()
        
        for record in self.all_records:
            if isinstance(record, dict):
                if 'collection' in record:
                    collections.add(record['collection'])
                if 'tags' in record and isinstance(record['tags'], list):
                    tags.update(record['tags'])
        
        # 更新作品集列表
        self.collection_list.clear()
        # 添加收藏列表
        self.favorite_item = QListWidgetItem("收藏列表")
        self.favorite_item.setData(Qt.UserRole, "favorites")
        self.collection_list.addItem(self.favorite_item)
        # 添加其他作品集
        for coll in sorted(collections):
            self.collection_list.addItem(coll)
        
        # 更新标签列表
        self.tag_list.clear()
        for tag in sorted(tags):
            self.tag_list.addItem(tag)
    
    def on_collection_item_changed(self, current, previous):
        if not current:
            return
        item_type = current.data(Qt.UserRole)
        if item_type == "favorites":
            # 清空右侧内容区域
            self.right_content.setRowCount(0)
            # 遍历所有记录，筛选出收藏的作品
            for record in self.all_records:
                if record.get("favorite", False):
                    row = self.right_content.rowCount()
                    self.right_content.insertRow(row)
                    self.right_content.setItem(row, 0, QTableWidgetItem(record.get("title", "未知作品")))
                    self.right_content.setItem(row, 1, QTableWidgetItem(format_file_size(record.get("size", 0))))

    def on_library_changed(self, current, previous):
        if current:
            lib_path = current.data(Qt.UserRole)
            # 加载并显示库中的文件
            self.right_content.setRowCount(0)
            record_path = os.path.join(lib_path, 'record.json')
            if os.path.exists(record_path):
                with open(record_path, 'r', encoding='utf-8') as f:
                    try:
                        records = json.load(f)
                        if isinstance(records, list):
                            for i, record in enumerate(records):
                                self.right_content.insertRow(i)
                                basic_info = record.get('basic_info', {})
                                self.right_content.setItem(i, 0, QTableWidgetItem(basic_info.get('name', '未知文件')))
                                self.right_content.setItem(i, 1, QTableWidgetItem(self.format_size(basic_info.get('size', 0))))
                    except json.JSONDecodeError:
                        QMessageBox.warning(self, '错误', '无法解析该库的record.json文件')
            else:
                QMessageBox.warning(self, '错误', f'库目录下未找到record.json文件: {record_path}')
                self.right_content.setRowCount(0)
    
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