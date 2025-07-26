'''
@version 1.0
@brief 实现前端的一些相关功能
@author 炎刃
@date 2025-07-24
'''
import os

import json
import uuid
import zipfile
from PIL import Image
import shutil
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtCore import QFileInfo

class I18nManager:
    def __init__(self):
        self.language = "zh_CN"
        self.translations = {}
        self.load_settings()
        self.load_translations()

    def load_settings(self):
        try:
            settings_path = os.path.join(os.path.dirname(__file__), "settings.json")
            with open(settings_path, "r", encoding="utf-8") as f:
                settings = json.load(f)
                self.language = settings.get("language", "zh_CN")
        except Exception as e:
            print(f"加载设置失败: {e}")

    def load_translations(self):
        try:
            # 使用lib_func.py所在目录(resource)直接拼接i18n路径
            base_dir = os.path.dirname(os.path.abspath(__file__))
            lang_file = os.path.join(base_dir, "i18n", f"{self.language}.json")
            with open(lang_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
        except Exception as e:
            QMessageBox.critical(None, "语言文件加载失败", f"无法加载语言文件 {lang_file}: {str(e)} 将使用默认中文界面。")
            default_file = os.path.join(base_dir, "i18n", "zh_CN.json")
            with open(default_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)

    def get_text(self, key):
        keys = key.split('.')
        result = self.translations
        for k in keys:
            if isinstance(result, dict):
                result = result.get(k, {})
            else:
                return key
            if not result:
                return key
        return result


def format_file_size(size):
    """将字节大小格式化为人类可读的单位"""
    if size < 1024:
        return f'{size} B'
    elif size < 1024 * 1024:
        return f'{size/1024:.1f} KB'
    elif size < 1024 * 1024 * 1024:
        return f'{size/(1024*1024):.1f} MB'
    else:
        return f'{size/(1024*1024*1024):.1f} GB'


class ComicLibraryUtils:
    @staticmethod
    def load_libraries_config():
        """加载库配置"""
        libraries = []
        config_path = os.path.join(os.path.dirname(__file__), 'settings.json')
        if os.path.exists(config_path):
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                libraries = config.get('libraries', [])
        return libraries

    @staticmethod
    def save_libraries_config(libraries):
        """保存库配置"""
        config_path = os.path.join(os.path.dirname(__file__), 'settings.json')
        with open(config_path, 'w', encoding='utf-8') as f:
            json.dump({'libraries': libraries}, f, ensure_ascii=False, indent=2)

    @staticmethod
    def scan_library(lib_path):
        records = []
        if not os.path.isdir(lib_path):
            return records
        
        # 支持的漫画文件扩展名
        comic_extensions = ['.cbz', '.cbr', '.pdf', '.epub', '.jpg', '.jpeg', '.png']
        
        for root, _, files in os.walk(lib_path):
            for file in files:
                ext = os.path.splitext(file)[1].lower()
                if ext in comic_extensions:
                    full_path = os.path.join(root, file)
                    file_info = QFileInfo(full_path)
                    
                    # 收集文件基本信息
                    record = {
                        'full_path': full_path,
                        'name': file_info.fileName(),
                        'modified_time': file_info.lastModified().toString('yyyy-MM-dd HH:mm:ss'),
                        'size': file_info.size()
                    }
                    records.append(record)
        return records

    @staticmethod
    def create_new_library(folder_path):
        """创建新库并初始化结构

        Args:
            folder_path: 库的根目录路径

        Returns:
            新创建库的ID

        Raises:
            ValueError: 当文件夹路径无效或已存在同名库时
        """
        # 验证文件夹路径
        if not os.path.exists(folder_path):
            raise ValueError(f"文件夹不存在: {folder_path}")
        if not os.path.isdir(folder_path):
            raise ValueError(f"不是有效的文件夹: {folder_path}")

        # 获取资源目录路径
        resource_dir = os.path.join(os.path.dirname(__file__), 'resource')
        os.makedirs(resource_dir, exist_ok=True)

        # 创建cover文件夹
        cover_dir = os.path.join(resource_dir, 'cover')
        os.makedirs(cover_dir, exist_ok=True)

        # 处理record.json
        record_path = os.path.join(resource_dir, 'record.json')
        if os.path.exists(record_path):
            with open(record_path, 'r', encoding='utf-8') as f:
                record_data = json.load(f)
        else:
            record_data = {"version": "1.0", "libraries": []}

        # 生成库ID和名称
        lib_id = str(uuid.uuid4())
        lib_name = os.path.basename(folder_path)

        # 检查库是否已存在
        for lib in record_data.get('libraries', []):
            if lib.get('path') == folder_path:
                raise ValueError(f"库已存在: {folder_path}")

        # 确保libraries字段存在
        if 'libraries' not in record_data:
            record_data['libraries'] = []
        
        # 添加新库到record_data
        new_lib = {
            "id": lib_id,
            "name": lib_name,
            "path": folder_path,
            "comics": []  # 存储漫画信息，格式: [{"id": "", "name": "", "path": "", "cover": ""}, ...]
        }
        record_data['libraries'].append(new_lib)

        # 保存record.json
        with open(record_path, 'w', encoding='utf-8') as f:
            json.dump(record_data, f, ensure_ascii=False, indent=2)

        # 更新库配置（settings.json）
        current_libraries = ComicLibraryUtils.load_libraries_config()
        current_libraries.append({"name": lib_name, "path": folder_path})
        ComicLibraryUtils.save_libraries_config(current_libraries)

        return lib_id

    @staticmethod
    def extract_tags(records):
        """从记录中提取并返回排序后的标签列表"""
        tags = set()
        for record in records:
            if isinstance(record, dict) and 'tags' in record and isinstance(record['tags'], list):
                tags.update(record['tags'])
        return sorted(tags)

    @staticmethod
    def filter_favorite_records(records):
        """筛选出收藏的记录"""
        return [record for record in records if record.get("favorite", False)]

    @staticmethod
    def filter_records_by_library(records, library_id=None, category=None):
        """根据库ID或分类筛选记录"""
        if library_id:
            return [r for r in records if r.get('lib_id') == library_id]
        elif category and category != '全部':
            return [r for r in records if isinstance(r, dict) and r.get('category') == category]
        return records

    @staticmethod
    def filter_records_by_tag(records, tag_name, current_lib_path=None):
        """根据标签和当前库路径筛选记录"""
        filtered = []
        for record in records:
            record_path = record.get("basic_info", {}).get("path", "")
            if (tag_name in record.get("tags", []) and 
                (current_lib_path is None or record_path.startswith(current_lib_path))):
                filtered.append(record)
        return filtered

    @staticmethod
    def scan_all_libraries(libraries):
        """扫描所有库，验证漫画文件并提取封面"""
        all_records = []
        for lib in libraries:
            lib_path = lib['path']
            lib_name = lib['name']
            lib_id = lib.get('id', str(uuid.uuid4()))
            
            # 创建必要的目录和文件
            record_path = os.path.join(lib_path, 'record.json')
            cover_dir = os.path.join(lib_path, 'cover')
            os.makedirs(cover_dir, exist_ok=True)
            
            # 初始化record.json如果不存在
            if not os.path.exists(record_path):
                with open(record_path, 'w', encoding='utf-8') as f:
                    json.dump([], f, ensure_ascii=False, indent=2)
            
            # 读取现有记录
            try:
                with open(record_path, 'r', encoding='utf-8') as f:
                    records = json.load(f)
                    if not isinstance(records, list):
                        records = []
            except json.JSONDecodeError:
                QMessageBox.warning(None, '错误', f'无法解析{lib_name}的record.json，已重置为空白记录')
                records = []
            
            # 扫描压缩文件
            comic_extensions = ('.zip', '.rar', '.7z', '.cbz', '.cbr')
            comic_files = [f for f in os.listdir(lib_path) if f.lower().endswith(comic_extensions)]
            
            # 验证记录与文件的一致性
            record_map = {r['path']: r for r in records}
            updated_records = []
            
            for comic_file in comic_files:
                comic_path = os.path.join(lib_path, comic_file)
                comic_id = str(uuid.uuid5(uuid.NAMESPACE_URL, comic_path))
                
                # 如果记录不存在或已更新，则处理新漫画
                if comic_file not in record_map or os.path.getmtime(comic_path) > record_map[comic_file].get('modified_time', 0):
                    # 提取封面
                    cover_path = os.path.join(cover_dir, f'{comic_id}.jpg')
                    if not os.path.exists(cover_path):
                        try:
                            with zipfile.ZipFile(comic_path, 'r') as zf:
                                # 查找压缩包中的第一个图片文件
                                image_files = sorted([f for f in zf.namelist() if f.lower().endswith(('.jpg', '.jpeg', '.png', '.gif'))])
                                if image_files:
                                    with zf.open(image_files[0]) as img_file, open(cover_path, 'wb') as out_file:
                                        out_file.write(img_file.read())
                        except Exception as e:
                            print(f'提取封面失败 {comic_file}: {e}')
                            cover_path = ''
                    
                    # 创建或更新记录
                    comic_record = {
                        'id': comic_id,
                        'name': os.path.splitext(comic_file)[0],
                        'path': comic_file,
                        'full_path': comic_path,
                        'cover': cover_path,
                        'size': os.path.getsize(comic_path),
                        'modified_time': os.path.getmtime(comic_path),
                        'lib_id': lib_id,
                        'lib_name': lib_name
                    }
                    updated_records.append(comic_record)
                else:
                    updated_records.append(record_map[comic_file])
            
            # 保存更新后的记录
            with open(record_path, 'w', encoding='utf-8') as f:
                json.dump(updated_records, f, ensure_ascii=False, indent=2)
            
            all_records.extend(updated_records)
        
        return all_records