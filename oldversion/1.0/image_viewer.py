#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

class ImageViewer:
    """
    一个基于 Tkinter 的图片查看器类，用于浏览指定文件夹下的图片。
    支持在图片间进行切换，显示当前图片的状态信息，并且能够自动调整图片大小以适应窗口。

    Attributes:
        root (tk.Tk): Tkinter 主窗口对象。
        image_paths (list): 存储图片文件的路径列表。
        current_index (int): 当前显示图片在 image_paths 列表中的索引。
        status_var (tk.StringVar): 用于更新状态栏信息的变量。
    """
    def __init__(self, root, folder_path=None):
        self.root = root
        self.root.title("viewer")
        
        self.image_paths = []
        self.current_index = 0
        
        self.setup_ui()
        
        if folder_path:
            self.load_images(folder_path)
        
        if self.image_paths:
            self.show_image()

    def setup_ui(self):
        # 主框架
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))

        # 配置样式
        style = ttk.Style()
        style.configure('ButtonFrame.TFrame', background='#cccccc')
        style.configure('NavButton.TButton', background='#f0f0f0', borderwidth=1, relief='solid')

        # 图片显示区域
        self.image_label = ttk.Label(self.main_frame)
        self.image_label.grid(row=0, column=0, columnspan=3)

        # 按钮框架，用于创建贯通左右的长条
        button_frame = ttk.Frame(self.main_frame, style='ButtonFrame.TFrame')
        button_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=10)
        button_frame.columnconfigure(0, weight=4)
        button_frame.columnconfigure(1, weight=1)
        button_frame.columnconfigure(2, weight=4)

        # 导航按钮
        self.prev_button = ttk.Button(button_frame, text="上一张", command=self.prev_image, style='NavButton.TButton')
        self.prev_button.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=1, pady=1)

        self.first_button = ttk.Button(button_frame, text="首页", command=self.first_image, style='NavButton.TButton')
        self.first_button.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=1, pady=1)

        self.next_button = ttk.Button(button_frame, text="下一张", command=self.next_image, style='NavButton.TButton')
        self.next_button.grid(row=0, column=2, sticky=(tk.W, tk.E), padx=1, pady=1)

        # 状态栏
        self.status_var = tk.StringVar()
        if self.image_paths:
            self.status_var.set(f"{self.current_index + 1}/{len(self.image_paths)}: {os.path.basename(self.image_paths[self.current_index])}")
        else:
            self.status_var.set("未提供有效的图片文件夹路径")
        self.status_bar = ttk.Label(self.main_frame, textvariable=self.status_var, relief=tk.SUNKEN)
        self.status_bar.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E))

        # 配置网格权重
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        self.main_frame.columnconfigure(0, weight=1)
        self.main_frame.columnconfigure(1, weight=1)
        self.main_frame.columnconfigure(2, weight=1)
        self.main_frame.rowconfigure(0, weight=1)

    def load_images(self, folder_path):
        image_extensions = ('.jpg', '.jpeg', '.png', '.gif', '.bmp', '.webp')
        self.image_paths = []
        for root, _, files in os.walk(folder_path):
            for file in files:
                if file.lower().endswith(image_extensions):
                    self.image_paths.append(os.path.join(root, file))
        self.image_paths.sort()
        self.current_index = 0

        if self.image_paths:
            self.status_var.set(f"已加载 {len(self.image_paths)} 张图片")
        else:
            messagebox.showwarning("警告", "文件夹中未找到图片文件")
            self.status_var.set("未提供有效的图片文件夹路径")

    def show_image(self):
        if self.image_paths:
            try:
                image = Image.open(self.image_paths[self.current_index])
                # 调整图片大小以适应窗口
                screen_width = self.root.winfo_screenwidth()
                screen_height = self.root.winfo_screenheight()
                max_width = int(screen_width * 0.7)
                max_height = int(screen_height * 0.7)
                image.thumbnail((max_width, max_height))

                photo = ImageTk.PhotoImage(image)
                self.image_label.configure(image=photo)
                self.image_label.image = photo
                self.status_var.set(f"{self.current_index + 1}/{len(self.image_paths)}: {os.path.basename(self.image_paths[self.current_index])}")
            except Exception as e:
                messagebox.showerror("错误", f"无法加载图片: {str(e)}")
                self.next_image()

    def next_image(self):
        if self.image_paths:
            self.current_index = (self.current_index + 1) % len(self.image_paths)
            self.show_image()

    def prev_image(self):
        if self.image_paths:
            self.current_index = (self.current_index - 1) % len(self.image_paths)
            self.show_image()

    def first_image(self):
        if self.image_paths:
            self.current_index = 0
            self.show_image()

if __name__ == "__main__":
    root = tk.Tk()
    # 示例：请替换为实际的文件夹路径
    folder_path = ["D:/Documents/漫画/1/2448070-[Shiokou Yakyuubu (Shio)] KENxSOU [Digital]/2448070-[Shiokou Yakyuubu (Shio)] KENxSOU [Digital]",
    "D:/Documents/漫画/1/3342520-[URAGERI (Ura Renga)][Traditional Chinese]強制健康檢查[自由獸漢化組]/3342520-[URAGERI (Ura Renga)][Traditional Chinese]強制健康檢查[自由獸漢化組]"]
    app = ImageViewer(root, folder_path[1])
    root.mainloop()