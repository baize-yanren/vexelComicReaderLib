import sys
import os
import argparse
from PyQt5.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                            QHBoxLayout, QPushButton, QLabel, QScrollArea, QSizePolicy)
from PyQt5.QtGui import QPixmap, QImage, QImageReader, QIcon
from PyQt5.QtCore import Qt, QByteArray, QTimer
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
        self.setWindowTitle('VexelViewer')
        # 设置窗口图标
        icon_path = "d:/Documents/GithubCode/comic-viewer/resource/icons/vexellogo.png"
        self.setWindowIcon(QIcon(icon_path))
        self.setGeometry(100, 100, 600, 900)
        
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
        
        # 控制区域布局（垂直）
        control_layout = QVBoxLayout()
        
        # 按钮行布局（水平）
        button_row_layout = QHBoxLayout()
        
        # 上一页按钮
        self.prev_btn = QPushButton('上一页')
        self.prev_btn.clicked.connect(self.prev_image)
        self.prev_btn.setEnabled(False)
        self.prev_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        button_row_layout.addWidget(self.prev_btn)
        button_row_layout.setStretchFactor(self.prev_btn, 4)
        
        # 首页按钮
        self.first_page_btn = QPushButton('首页')
        self.first_page_btn.clicked.connect(self.first_page)
        self.first_page_btn.setEnabled(False)
        self.first_page_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        button_row_layout.addWidget(self.first_page_btn)
        button_row_layout.setStretchFactor(self.first_page_btn, 2)
        
        # 下一页按钮
        self.next_btn = QPushButton('下一页')
        self.next_btn.clicked.connect(self.next_image)
        self.next_btn.setEnabled(False)
        self.next_btn.setSizePolicy(QSizePolicy.Preferred, QSizePolicy.Preferred)
        button_row_layout.addWidget(self.next_btn)
        button_row_layout.setStretchFactor(self.next_btn, 4)
        
        # 状态行布局（水平）
        status_row_layout = QHBoxLayout()
        self.status_label = QLabel('未选择图片文件夹')
        status_row_layout.addWidget(self.status_label)
        
        # 将按钮行和状态行添加到控制区域布局
        control_layout.addLayout(button_row_layout)
        control_layout.addLayout(status_row_layout)
        
        main_layout.addLayout(control_layout)
        
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
            
            # 使用QImageReader打开图片以支持WebP格式
            try:
                # 获取文件扩展名
                ext = os.path.splitext(image_path)[1].lower()
                reader = QImageReader(image_path)
                
                # 对WebP格式显式设置格式
                if ext == '.webp':
                    reader.setFormat(QByteArray(b"webp"))
                
                image = reader.read()
                if image.isNull():
                    raise ValueError(f"无法读取图片: {reader.errorString()}")
                
                # 调整图片大小以适应窗口
                # 获取视口实际显示尺寸
                def adjust_initial_image():
                    window_width = self.scroll_area.viewport().width()
                    window_height = self.scroll_area.viewport().height()
                    
                    # 确保至少有最小尺寸，避免初始化为0
                    window_width = max(window_width, 400)
                    window_height = max(window_height, 300)
                    
                    # 保持宽高比缩放
                    # 长边优先填满显示区域
                    scaled_image = image.scaled(window_width - 20, window_height - 20, 
                                               Qt.KeepAspectRatio, Qt.SmoothTransformation)
                    pixmap = QPixmap.fromImage(scaled_image)
                    
                    self.image_label.setPixmap(pixmap)
                
                QTimer.singleShot(0, adjust_initial_image)
                self.status_label.setText(f"图片 {self.current_index + 1}/{len(self.image_files)}: {os.path.basename(image_path)}")
            except ValueError as e:
                error_msg = f"""无法读取图片: {os.path.basename(image_path)}
错误信息: {str(e)}"""
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
                    error_msg += "提示: 请确保已正确安装WebP支持"
                elif ext in ['.tiff', '.tif']:
                    error_msg += "提示: 请确保已正确安装TIFF支持"
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
    # 设置应用图标，确保任务栏显示
    icon_path = "d:/Documents/GithubCode/comic-viewer/resource/icons/vexellogo.png"
    app.setWindowIcon(QIcon(icon_path))
    if args.folder_path:
        browser = PictureBrowser(args.folder_path)
    else:
        browser = PictureBrowser()
        browser.status_label.setText("请通过API设置图片文件夹路径")
    browser.show()
    sys.exit(app.exec_())