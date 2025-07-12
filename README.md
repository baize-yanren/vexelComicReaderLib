# Comic Viewer

该项目提供从 7z、rar 等压缩包中解压图片并查看的功能，同时包含一个图片查看器，可在文件夹路径下的所有图片间切换。

## 环境准备
1. 确保系统已安装 `7z`、`unrar` 和 `unzip` 命令行工具。
2. 安装 Python 依赖：
   ```bash
   pip install -r requirements.txt
   ```

## 解压并查看图片
1. 将需要解压的压缩包路径替换 `unzip_and_view.py` 文件中的 `your_archive.7z`。
2. 运行脚本：
   ```bash
   python unzip_and_view.py
   ```
3. 按回车键查看下一张图片。

## 使用图片查看器
1. 运行脚本：
   ```bash
   python image_viewer.py
   ```
2. 点击 "打开文件夹" 按钮选择包含图片的文件夹。
3. 使用 "上一张" 和 "下一张" 按钮切换图片。