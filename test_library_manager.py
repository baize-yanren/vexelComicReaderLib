import unittest
import os
import json
import tempfile
from pathlib import Path
from PyQt5.QtWidgets import QApplication
from resource.library_manager import LibraryManager
from resource.lib_func import I18nManager

class TestLibraryManager(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # 在类级别初始化QApplication
        cls.app = QApplication([])

    @classmethod
    def tearDownClass(cls):
        # 清理QApplication
        cls.app.quit()

    def setUp(self):
        # 创建临时目录
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.test_config_path = Path(__file__).parent / 'resource' / 'settings.json'
        self.backup_config = None
    def setUp(self):
        # 创建临时目录
        self.temp_dir = tempfile.TemporaryDirectory()
        self.temp_path = Path(self.temp_dir.name)
        self.test_config_path = Path(__file__).parent / 'settings.json'
        self.backup_config = None
        
        # 备份原始配置文件
        if self.test_config_path.exists():
            with open(self.test_config_path, 'r', encoding='utf-8') as f:
                self.backup_config = json.load(f)
        
        # 初始化I18nManager
        self.i18n = I18nManager()
        self.manager = LibraryManager(self.i18n)
        # 强制清除现有库并保存空状态，确保测试隔离
        self.manager.libraries = []
        self.manager.save_libraries_config()
        # 重新加载配置以确保清除生效
        self.manager.load_libraries_config()

    def _create_test_library(self, lib_name='test_lib'):
        """创建测试库目录并返回路径"""
        lib_path = self.temp_path / lib_name
        lib_path.mkdir(exist_ok=True)
        return lib_path

    def _create_test_files(self, lib_path, files):
        """在指定库路径下创建测试文件"""
        for file in files:
            (lib_path / file).write_text('test content')

    def tearDown(self):
        # 恢复原始配置文件
        if self.backup_config:
            with open(self.test_config_path, 'w', encoding='utf-8') as f:
                json.dump(self.backup_config, f, ensure_ascii=False, indent=2)
        else:
            # 如果原始配置不存在则删除测试创建的配置
            if self.test_config_path.exists():
                self.test_config_path.unlink()
        
        # 清理临时目录
        self.temp_dir.cleanup()

    def test_add_and_remove_library(self):
        # 创建测试目录
        test_lib_path = self._create_test_library('test_lib')
        test_lib_str = str(test_lib_path)
        
        # 测试添加库
        add_result = self.manager.add_library(test_lib_str)
        self.assertTrue(add_result)
        self.assertEqual(len(self.manager.libraries), 1)
        self.assertEqual(self.manager.libraries[0]['path'], str(test_lib_path))
        
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
        test_lib_path = self._create_test_library('test_lib')
        
        # 创建测试漫画文件
        test_files = [
            'comic1.cbz', 'book.pdf', 'image.jpg', 'not_comic.txt'
        ]
        self._create_test_files(test_lib_path, test_files)
        
        # 添加并扫描库
        self.manager.add_library(str(test_lib_path))
        records = self.manager.scan_library(str(test_lib_path))
        
        # 应该只扫描到3个漫画文件（排除txt）
        self.assertEqual(len(records), 3, "Incorrect number of scanned comic files")
        
        # 验证文件信息
        scanned_files = [r['name'] for r in records]
        self.assertIn('comic1.cbz', scanned_files, "comic1.cbz not scanned")
        self.assertIn('book.pdf', scanned_files, "book.pdf not scanned")
        self.assertIn('image.jpg', scanned_files, "image.jpg not scanned")
        self.assertNotIn('not_comic.txt', scanned_files, "not_comic.txt should not be scanned")

    def test_scan_all_libraries(self):
        # 创建两个测试库
        lib1_path = self._create_test_library('lib1')
        lib2_path = self._create_test_library('lib2')
        
        # 在每个库中创建文件
        self._create_test_files(lib1_path, ['comic1.cbz'])
        self._create_test_files(lib2_path, ['comic2.cbr'])
        
        # 添加库并扫描
        self.manager.add_library(str(lib1_path))
        self.manager.add_library(str(lib2_path))
        all_records = self.manager.scan_all_libraries()
        # 验证扫描到的文件路径是否正确
        scanned_paths = [record['path'] for record in all_records]
        self.assertIn(str(lib1_path / 'comic1.cbz'), scanned_paths)
        self.assertIn(str(lib2_path / 'comic2.cbr'), scanned_paths)
        
        # 应该扫描到2个文件
        self.assertEqual(len(all_records), 2, "Total scanned files count is incorrect")
        
        # 验证扫描到的文件名
        scanned_files = [record['name'] for record in all_records]
        self.assertIn('comic1.cbz', scanned_files, "comic1.cbz not found in scan results")
        self.assertIn('comic2.cbr', scanned_files, "comic2.cbr not found in scan results")
        
        # 验证最后扫描时间被更新
        for lib in self.manager.libraries:
            self.assertIsNotNone(lib['last_scan'], f"Last scan time for library {lib['name']} was not updated")

    def test_update_library_name(self):
        # 创建测试库
        test_lib_path = self._create_test_library('test_lib')
        test_lib_str = str(test_lib_path)
        
        # 确保添加前库列表为空
        self.assertEqual(len(self.manager.libraries), 0, "Library list not empty before add")
        add_result = self.manager.add_library(test_lib_str)
        # 添加调试信息
        if not add_result:
            existing_paths = [lib['path'] for lib in self.manager.libraries]
            self.fail(f"Failed to add library {test_lib_str}. Existing paths: {existing_paths}")
        self.assertTrue(add_result)
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