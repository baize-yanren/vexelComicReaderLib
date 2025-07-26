import unittest
import os
import json
import tempfile
from PyQt5.QtWidgets import QApplication
from resource.library_manager import LibraryManager
from resource.lib_func import I18nManager

# 初始化QApplication
app = QApplication([])

class TestLibraryManager(unittest.TestCase):
    def setUp(self):
        # 创建临时目录
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_config_path = os.path.join(os.path.dirname(__file__), 'resource', 'settings.json')
        self.backup_config = None
        
        # 备份原始配置文件
        if os.path.exists(self.test_config_path):
            with open(self.test_config_path, 'r', encoding='utf-8') as f:
                self.backup_config = json.load(f)
        
        # 初始化I18nManager
        self.i18n = I18nManager()
        self.manager = LibraryManager(self.i18n)

    def tearDown(self):
        # 恢复原始配置文件
        if self.backup_config:
            with open(self.test_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.backup_config, f, ensure_ascii=False, indent=2)
        else:
            # 如果原始配置不存在则删除测试创建的配置
            if os.path.exists(self.test_config_path):
                os.remove(self.test_config_path)
        
        # 清理临时目录
        self.temp_dir.cleanup()

    def test_add_and_remove_library(self):
        # 创建测试目录
        test_lib_path = os.path.join(self.temp_dir.name, 'test_lib')
        os.makedirs(test_lib_path)
        
        # 测试添加库
        add_result = self.manager.add_library(test_lib_path)
        self.assertTrue(add_result)
        self.assertEqual(len(self.manager.libraries), 1)
        self.assertEqual(self.manager.libraries[0]['path'], test_lib_path)
        
        # 测试添加重复库
        add_result = self.manager.add_library(test_lib_path)
        self.assertFalse(add_result)
        
        # 测试移除库
        lib_id = self.manager.libraries[0]['id']
        remove_result = self.manager.remove_library(lib_id)
        self.assertTrue(remove_result)
        self.assertEqual(len(self.manager.libraries), 0)

    def test_scan_library(self):
        # 创建测试目录和文件
        test_lib_path = os.path.join(self.temp_dir.name, 'test_lib')
        os.makedirs(test_lib_path)
        
        # 创建测试漫画文件
        test_files = [
            'comic1.cbz', 'book.pdf', 'image.jpg', 'not_comic.txt'
        ]
        
        for file in test_files:
            with open(os.path.join(test_lib_path, file), 'w') as f:
                f.write('test content')
        
        # 添加并扫描库
        self.manager.add_library(test_lib_path)
        records = self.manager.scan_library(test_lib_path)
        
        # 应该只扫描到3个漫画文件（排除txt）
        self.assertEqual(len(records), 3)
        
        # 验证文件信息
        scanned_files = [r['name'] for r in records]
        self.assertIn('comic1.cbz', scanned_files)
        self.assertIn('book.pdf', scanned_files)
        self.assertIn('image.jpg', scanned_files)
        self.assertNotIn('not_comic.txt', scanned_files)

    def test_scan_all_libraries(self):
        # 创建两个测试库
        lib1_path = os.path.join(self.temp_dir.name, 'lib1')
        lib2_path = os.path.join(self.temp_dir.name, 'lib2')
        os.makedirs(lib1_path)
        os.makedirs(lib2_path)
        
        # 在每个库中创建文件
        with open(os.path.join(lib1_path, 'comic1.cbz'), 'w') as f:
            f.write('test')
        
        with open(os.path.join(lib2_path, 'comic2.cbr'), 'w') as f:
            f.write('test')
        
        # 添加库并扫描
        self.manager.add_library(lib1_path)
        self.manager.add_library(lib2_path)
        all_records = self.manager.scan_all_libraries()
        
        # 应该扫描到2个文件
        self.assertEqual(len(all_records), 2)
        
        # 验证最后扫描时间被更新
        for lib in self.manager.libraries:
            self.assertIsNotNone(lib['last_scan'])

    def test_update_library_name(self):
        # 创建测试库
        test_lib_path = os.path.join(self.temp_dir.name, 'test_lib')
        os.makedirs(test_lib_path)
        
        self.manager.add_library(test_lib_path)
        lib_id = self.manager.libraries[0]['id']
        original_name = self.manager.libraries[0]['name']
        
        # 更新名称
        new_name = 'updated_test_lib'
        update_result = self.manager.update_library_name(lib_id, new_name)
        
        self.assertTrue(update_result)
        self.assertEqual(self.manager.libraries[0]['name'], new_name)
        self.assertNotEqual(self.manager.libraries[0]['name'], original_name)

if __name__ == '__main__':
    unittest.main()