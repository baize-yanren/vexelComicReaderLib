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
import zipfile
from PIL import Image
import io
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
        try:
            if not dir_path or not os.path.isdir(dir_path):
                return False, 'invalid_directory'
                
            # 检查库是否已存在
            for lib in self.libraries:
                if lib['path'] == dir_path:
                    return False, 'library_exists'
                    
            # 检查并创建record.json和cover文件夹
            record_path = os.path.join(dir_path, 'record.json')
            cover_dir = os.path.join(dir_path, 'cover')
            
            if not os.path.exists(record_path):
                with open(record_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
            
            if not os.path.exists(cover_dir):
                os.makedirs(cover_dir, exist_ok=True)
                
            # 创建新库记录
            lib_name = os.path.basename(dir_path)
            new_lib = {
                'id': str(uuid.uuid4()),
                'name': lib_name,
                'path': dir_path,
                'last_scan': datetime.datetime.now().isoformat()
            }
            
            self.libraries.append(new_lib)
            if not self.save_libraries_config():
                return False, 'save_config_failed'
                
            # 调用扫描库方法
            scan_result, scan_error = self.scan_library(dir_path)
            if not scan_result and scan_error:
                return False, scan_error
                
            return True, None
        except Exception as e:
            return False, f'unknown_error: {str(e)}'

    def remove_library(self, library_id: str):
        original_count = len(self.libraries)
        self.libraries = [lib for lib in self.libraries if lib.get('id') != library_id]
        
        if len(self.libraries) < original_count:
            return self.save_libraries_config()
        return False

    def scan_library(self, library_path: str):
        try:
            if not os.path.isdir(library_path):
                return False, 'invalid_library_path'
                
            # 检查record.json文件是否存在
            record_path = os.path.join(library_path, 'record.json')
            if not os.path.exists(record_path):
                return False, 'record_file_not_found'
                
            # 读取record.json文件
            with open(record_path, 'r', encoding='utf-8') as f:
                existing_records = json.load(f)
                
            # 提取现有记录中的文件路径，用于检查新文件
            existing_files = {rec['full_path']: rec for rec in existing_records}
            
            # 支持的漫画文件扩展名
            comic_extensions = ['.cbz', '.cbr', '.pdf', '.epub']
            image_extensions = ['.jpg', '.jpeg', '.png', '.gif']
            
            # 扫描库目录下的文件
            has_new_files = False
            new_records = existing_records.copy()
            
            cover_dir = os.path.join(library_path, 'cover')
            os.makedirs(cover_dir, exist_ok=True)
            
            for root, _, files in os.walk(library_path):
                # 跳过cover目录
                if root == cover_dir:
                    continue
                    
                for file in files:
                    file_lower = file.lower()
                    ext = os.path.splitext(file_lower)[1]
                    
                    # 处理压缩包文件
                    if ext in comic_extensions:
                        full_path = os.path.join(root, file)
                        
                        # 检查是否为新文件
                        if full_path not in existing_files:
                            has_new_files = True
                            
                            # 生成唯一ID
                            comic_id = f'comic_{len(new_records) + 1:03d}'
                            
                            # 提取压缩包中的第一个图像作为封面
                            cover_path = self._extract_cover(full_path, cover_dir, comic_id)
                            
                            # 创建新记录
                            file_size = os.path.getsize(full_path)
                            modified_time = os.path.getmtime(full_path)
                            
                            new_record = {
                                'comic_id': comic_id,
                                'full_path': full_path,
                                'name': os.path.basename(full_path),
                                'size': file_size,
                                'modified_time': modified_time,
                                'cover_path': cover_path,
                                'library_path': library_path
                            }
                            
                            new_records.append(new_record)
                            
                        # 更新现有文件信息
                        elif existing_files[full_path]['modified_time'] != os.path.getmtime(full_path):
                            has_new_files = True
                            index = next(i for i, rec in enumerate(new_records) if rec['full_path'] == full_path)
                            
                            # 更新文件大小和修改时间
                            new_records[index]['size'] = os.path.getsize(full_path)
                            new_records[index]['modified_time'] = os.path.getmtime(full_path)
                            
                            # 更新封面（如果需要）
                            comic_id = new_records[index]['comic_id']
                            cover_path = self._extract_cover(full_path, cover_dir, comic_id)
                            new_records[index]['cover_path'] = cover_path
                            
                    # 处理单独的图像文件
                    elif ext in image_extensions:
                        full_path = os.path.join(root, file)
                        
                        # 检查是否为新文件
                        if full_path not in existing_files:
                            has_new_files = True
                            
                            # 生成唯一ID
                            comic_id = f'comic_{len(new_records) + 1:03d}'
                            
                            # 复制图像作为封面
                            cover_filename = f'{comic_id}{ext}'
                            cover_path = os.path.join(cover_dir, cover_filename)
                            
                            # 保存封面
                            try:
                                with Image.open(full_path) as img:
                                    img.save(cover_path)
                            except Exception as e:
                                print(f'Error saving cover for {full_path}: {e}')
                                cover_path = None
                                
                            # 创建新记录
                            file_size = os.path.getsize(full_path)
                            modified_time = os.path.getmtime(full_path)
                            
                            new_record = {
                                'comic_id': comic_id,
                                'full_path': full_path,
                                'name': os.path.basename(full_path),
                                'size': file_size,
                                'modified_time': modified_time,
                                'cover_path': cover_path,
                                'library_path': library_path
                            }
                            
                            new_records.append(new_record)
                            
                        # 更新现有文件信息
                        elif existing_files[full_path]['modified_time'] != os.path.getmtime(full_path):
                            has_new_files = True
                            index = next(i for i, rec in enumerate(new_records) if rec['full_path'] == full_path)
                            
                            # 更新文件大小和修改时间
                            new_records[index]['size'] = os.path.getsize(full_path)
                            new_records[index]['modified_time'] = os.path.getmtime(full_path)
                            
        except Exception as e:
            return False, f'error_scanning: {str(e)}'
            
        # 如果有新文件，更新record.json
        if has_new_files:
            try:
                with open(record_path, 'w', encoding='utf-8') as f:
                    json.dump(new_records, f, ensure_ascii=False, indent=2)
                return True, None
            except Exception as e:
                return False, f'error_saving_record: {str(e)}'
        else:
            return False, None

    def _extract_cover(self, archive_path: str, cover_dir: str, comic_id: str) -> str:
        """从压缩包中提取第一个图像文件作为封面"""
        try:
            if archive_path.lower().endswith('.cbz'):
                with zipfile.ZipFile(archive_path, 'r') as zip_ref:
                    # 获取所有文件并按名称排序
                    files = sorted(zip_ref.namelist())
                    for file in files:
                        file_lower = file.lower()
                        if any(file_lower.endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.gif']):
                            # 读取图像文件
                            with zip_ref.open(file) as img_file:
                                img_data = img_file.read()
                                
                            # 确定图像扩展名
                            ext = os.path.splitext(file_lower)[1]
                            cover_filename = f'{comic_id}{ext}'
                            cover_path = os.path.join(cover_dir, cover_filename)
                            
                            # 保存封面
                            with open(cover_path, 'wb') as f:
                                f.write(img_data)
                            return cover_path
            # 可以在这里添加其他压缩格式的支持（如.cbr）
            return None
        except Exception as e:
            print(f'Error extracting cover from {archive_path}: {e}')
            return None

    def scan_all_libraries(self):
        all_records = []
        for lib in self.libraries:
            lib_path = lib.get('path')
            if lib_path and os.path.exists(lib_path):
                success, error = self.scan_library(lib_path)
                if success:
                    # 读取更新后的record.json文件
                    record_path = os.path.join(lib_path, 'record.json')
                    try:
                        with open(record_path, 'r', encoding='utf-8') as f:
                            records = json.load(f)
                            all_records.extend(records)
                    except Exception as e:
                        print(f'Error reading record.json for library {lib_path}: {e}')
                elif error:
                    print(f'Error scanning library {lib_path}: {error}')
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