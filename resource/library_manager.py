'''
@version 1.0
@brief 漫画库管理核心功能实现
@author 炎刃
@date 2025-07-25
'''

import os
import json
import uuid
import datetime
from PyQt5.QtWidgets import QMessageBox, QFileDialog
from .lib_func import I18nManager, format_file_size

class LibraryManager:
    def __init__(self, i18n: I18nManager):
        self.i18n = i18n
        self.libraries = []
        self.load_libraries_config()

    def load_libraries_config(self):
        try:
            # 从library_manager.py所在目录(resource)向上一级找到项目根目录
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            config_path = os.path.join(project_root, 'settings.json')
            if os.path.exists(config_path):
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    self.libraries = config.get('libraries', [])
        except Exception as e:
            QMessageBox.warning(
                None, 
                self.i18n.get_text('error.title'), 
                self.i18n.get_text('error.load_config_failed').format(error=str(e))
            )
            self.libraries = []
        return self.libraries

    def save_libraries_config(self):
        try:
            # 与load_libraries_config保持一致，使用项目根目录下的settings.json
            current_dir = os.path.dirname(os.path.abspath(__file__))
            project_root = os.path.dirname(current_dir)
            config_path = os.path.join(project_root, 'settings.json')
            # 确保配置文件目录存在
            os.makedirs(os.path.dirname(config_path), exist_ok=True)
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump({'libraries': self.libraries}, f, ensure_ascii=False, indent=2)
            return True
        except Exception as e:
            QMessageBox.warning(
                None, 
                self.i18n.get_text('error.title'), 
                self.i18n.get_text('error.save_config_failed').format(error=str(e))
            )
            return False

    def add_library(self, dir_path: str):
        if not dir_path or not os.path.isdir(dir_path):
            QMessageBox.warning(
                None, 
                self.i18n.get_text('error.title'), 
                self.i18n.get_text('error.invalid_directory')
            )
            return False
            
        # 检查库是否已存在
        for lib in self.libraries:
            if lib['path'] == dir_path:
                QMessageBox.warning(
                    None, 
                    self.i18n.get_text('error.title'), 
                    self.i18n.get_text('settings.error.library_exists')
                )
                return False
                
        # 创建新库记录
        lib_name = os.path.basename(dir_path)
        new_lib = {
            'id': str(uuid.uuid4()),
            'name': lib_name,
            'path': dir_path,
            'last_scan': None
        }
        
        self.libraries.append(new_lib)
        return self.save_libraries_config()

    def remove_library(self, library_id: str):
        original_count = len(self.libraries)
        self.libraries = [lib for lib in self.libraries if lib.get('id') != library_id]
        
        if len(self.libraries) < original_count:
            return self.save_libraries_config()
        return False

    def scan_library(self, library_path: str):
        records = []
        if not os.path.isdir(library_path):
            return records
            
        # 支持的漫画文件扩展名
        comic_extensions = ['.cbz', '.cbr', '.pdf', '.epub', '.jpg', '.jpeg', '.png']
        
        for root, _, files in os.walk(library_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in comic_extensions:
                    full_path = os.path.join(root, file)
                    file_size = os.path.getsize(full_path)
                    modified_time = os.path.getmtime(full_path)
                    
                    records.append({
                        'full_path': full_path,
                        'name': os.path.basename(full_path),
                        'size': file_size,
                        'modified_time': modified_time,
                        'library_path': library_path
                    })
                    
        return records

    def scan_all_libraries(self):
        all_records = []
        for lib in self.libraries:
            lib_path = lib.get('path')
            if lib_path and os.path.exists(lib_path):
                records = self.scan_library(lib_path)
                all_records.extend(records)
                # 更新最后扫描时间
                lib['last_scan'] = datetime.datetime.now().isoformat()
                
        self.save_libraries_config()  # 保存最后扫描时间
        return all_records

    def get_library_by_id(self, library_id: str):
        for lib in self.libraries:
            if lib.get('id') == library_id:
                return lib
        return None

    def update_library_name(self, library_id: str, new_name: str):
        for lib in self.libraries:
            if lib.get('id') == library_id:
                lib['name'] = new_name
                return self.save_libraries_config()
        return False