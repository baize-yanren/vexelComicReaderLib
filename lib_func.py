import os
import json
import uuid
from PyQt5.QtWidgets import QMessageBox

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
            lang_file = os.path.join(os.path.dirname(__file__), "resource", "i18n", f"{self.language}.json")
            with open(lang_file, "r", encoding="utf-8") as f:
                self.translations = json.load(f)
        except Exception as e:
            QMessageBox.critical(None, "语言文件加载失败", f"无法加载语言文件 {lang_file}: {str(e)} 将使用默认中文界面。")
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
    def scan_all_libraries(libraries):
        """扫描所有库的record.json"""
        all_records = []
        for lib in libraries:
            record_path = os.path.join(lib['path'], 'record.json')
            if os.path.exists(record_path):
                with open(record_path, 'r', encoding='utf-8') as f:
                    try:
                        records = json.load(f)
                        if isinstance(records, list):
                            all_records.extend(records)
                    except json.JSONDecodeError:
                        QMessageBox.warning(None, '错误', f'无法解析{lib["name"]}的record.json')
        return all_records