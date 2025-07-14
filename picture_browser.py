import sys
import os
import argparse
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QScrollArea)
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtCore import Qt
from PIL import Image, ImageQt, UnidentifiedImageError

class PictureBrowser(QMainWindow):
    def __init__(self, folder_path=None):
        super().__init__()
        self.current_dir = folder_path
        self.image_files = []
        self.current_index = 0
        
        self.initUI()
        if folder_path:
            self.load_image_files()
            self._initialize_browser()
        
    def initUI(self):
        self.setWindowTitle('图片浏览器')
        self.setGeometry(100, 100, 800, 600)
        
        # 主部件和布局
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)
        
        # 图片显示区域
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.scroll_area.setWidget(self.image_label)
        main_layout.addWidget(self.scroll_area)
        
        # 按钮布局
        button_layout = QHBoxLayout()
        
        # 回到首页按钮
        self.first_page_btn = QPushButton('首页')
        self.first_page_btn.clicked.connect(self.first_page)
        self.first_page_btn.setEnabled(False)
        button_layout.addWidget(self.first_page_btn)
        
        # 上一页按钮
        self.prev_btn = QPushButton('上一页')
        self.prev_btn.clicked.connect(self.prev_image)
        self.prev_btn.setEnabled(False)
        button_layout.addWidget(self.prev_btn)
        
        # 下一页按钮
        self.next_btn = QPushButton('下一页')
        self.next_btn.clicked.connect(self.next_image)
        self.next_btn.setEnabled(False)
        button_layout.addWidget(self.next_btn)
        
        # 状态标签
        self.status_label = QLabel('未选择图片文件夹')
        button_layout.addWidget(self.status_label)
        
        main_layout.addLayout(button_layout)
        
    def select_directory(self):
        # 移除文件夹选择功能
        pass
        
    def load_image_files(self):
        # 支持的图片格式
        image_extensions = ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp']
        self.image_files = []
        
        for filename in os.listdir(self.current_dir):
            ext = os.path.splitext(filename)[1].lower()
            if ext in image_extensions:
                self.image_files.append(os.path.join(self.current_dir, filename))
        
        # 按文件名排序
        self.image_files.sort()
        
    def display_image(self):
        if 0 <= self.current_index < len(self.image_files):
            image_path = self.image_files[self.current_index]
            
            # 使用Pillow打开图片
            try:
                img = Image.open(image_path)
                
                # 调整图片大小以适应窗口
                window_width = self.scroll_area.width()
                window_height = self.scroll_area.height()
                
                # 保持宽高比缩放
                img.thumbnail((window_width - 20, window_height - 20))
                
                # 转换为Qt可用的格式
                qt_img = ImageQt.ImageQt(img)
                pixmap = QPixmap.fromImage(qt_img)
                
                self.image_label.setPixmap(pixmap)
                self.status_label.setText(f"图片 {self.current_index + 1}/{len(self.image_files)}: {os.path.basename(image_path)}")
            except UnidentifiedImageError:
                error_msg = f"""无法识别图片格式: {os.path.basename(image_path)}
提示: 该文件可能不是有效的图片或已损坏"""
                self.status_label.setText(error_msg)
            except PermissionError:
                error_msg = f"""权限错误: 无法读取文件 {os.path.basename(image_path)}
提示: 请检查文件访问权限"""
                self.status_label.setText(error_msg)
            except Exception as e:
                ext = os.path.splitext(image_path)[1].lower()
                error_msg = f"""加载失败: {os.path.basename(image_path)}
错误类型: {type(e).__name__}
详情: {str(e)}"""
                # 添加文件大小信息
                try:
                    file_size = os.path.getsize(image_path) / (1024 * 1024)
                    error_msg += f"文件大小: {file_size:.2f} MB"
                except:
                    pass
                # 针对常见格式的特定提示
                if ext == '.webp':
                    error_msg += "提示: 请安装WebP支持 (pip install pillow[webp])"
                elif ext in ['.tiff', '.tif']:
                    error_msg += "提示: 请安装TIFF支持 (pip install pillow[tiff])"
                self.status_label.setText(error_msg)
    
    def first_page(self):
        if self.image_files and self.current_index != 0:
            self.current_index = 0
            self.display_image()
            self.update_buttons()
    
    def prev_image(self):
        if self.image_files and self.current_index > 0:
            self.current_index -= 1
            self.display_image()
            self.update_buttons()
    
    def next_image(self):
        if self.image_files and self.current_index < len(self.image_files) - 1:
            self.current_index += 1
            self.display_image()
            self.update_buttons()
    
    def update_buttons(self):
        # 更新按钮状态
        self.first_page_btn.setEnabled(len(self.image_files) > 1 and self.current_index != 0)
        self.prev_btn.setEnabled(self.current_index > 0)
        self.next_btn.setEnabled(self.current_index < len(self.image_files) - 1)
    
    def resizeEvent(self, event):
        # 窗口大小改变时重新调整图片大小
        if self.image_files:
            self.display_image()
        super().resizeEvent(event)
    
    def _initialize_browser(self):
        """初始化浏览器状态，私有方法"""
        if self.image_files:
            self.current_index = 0
            self.display_image()
            self.update_buttons()
            self.status_label.setText(f"图片 {self.current_index + 1}/{len(self.image_files)}")
        else:
            self.status_label.setText("未找到图片文件或文件夹不存在")
    
    def set_image_folder(self, folder_path):
        """设置图片文件夹路径并加载图片\n\n        Args:
            folder_path (str): 图片文件夹绝对路径\n        Returns:
            bool: 加载成功返回True，否则返回False
        """
        self.current_dir = folder_path
        self.load_image_files()
        self._initialize_browser()
        return len(self.image_files) > 0

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='图片浏览器')
    parser.add_argument('folder_path', nargs='?', help='图片文件夹路径（可选）')
    args = parser.parse_args()
    
    app = QApplication(sys.argv)
    if args.folder_path:
        browser = PictureBrowser(args.folder_path)
    else:
        browser = PictureBrowser()
        browser.status_label.setText("请通过API设置图片文件夹路径")
    browser.show()
    sys.exit(app.exec_())