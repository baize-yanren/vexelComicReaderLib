import os
import json
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