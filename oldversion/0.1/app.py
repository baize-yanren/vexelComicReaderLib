import tkinter as tk
from tkinter import ttk, filedialog, simpledialog
import os
import json
import pygubu

class MainApp(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("基础软件前端界面")
        self.geometry("800x600")
        self.settings_file = "settings.json"
        self.folder_path = self.load_settings()

        # 创建菜单栏
        self.create_menu()

        # 创建左侧导航栏
        self.create_navigation()
        if self.folder_path:
            self.list_files_in_navigation()

    def create_menu(self):
        menubar = tk.Menu(self)

        # 文件菜单
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="新建")
        file_menu.add_command(label="打开")
        file_menu.add_command(label="保存")
        file_menu.add_command(label="设置", command=self.show_settings)
        file_menu.add_separator()
        file_menu.add_command(label="退出", command=self.quit)
        menubar.add_cascade(label="文件", menu=file_menu)

        # 编辑菜单
        edit_menu = tk.Menu(menubar, tearoff=0)
        edit_menu.add_command(label="撤销")
        edit_menu.add_command(label="重做")
        edit_menu.add_separator()
        edit_menu.add_command(label="复制")
        edit_menu.add_command(label="粘贴")
        menubar.add_cascade(label="编辑", menu=edit_menu)

        self.config(menu=menubar)

    def create_navigation(self):
        # 创建左侧导航栏框架
        self.nav_frame = ttk.Frame(self, width=200, height=600)
        self.nav_frame.pack(side="left", fill="y")

        # 创建导航栏按钮
        file_button = ttk.Button(self.nav_frame, text="选择文件", command=self.select_file)
        file_button.pack(pady=10)
        self.file_listbox = tk.Listbox(self.nav_frame)
        self.file_listbox.pack(fill="both", expand=True)

    def select_file(self):
        file_path = filedialog.askopenfilename()
        if file_path:
            print(f"选择的文件: {file_path}")

    def show_settings(self):
        settings_window = tk.Toplevel(self)
        settings_window.title("设置")

        # 输入框和选择文件夹按钮框架
        input_frame = tk.Frame(settings_window)
        input_frame.pack(pady=10, padx=10, fill="x")

        # 输入框
        path_entry = tk.Entry(input_frame, width=50)
        path_entry.insert(0, self.folder_path)
        path_entry.pack(side="left", fill="x", expand=True)

        # 选择文件夹按钮
        def browse_folder():
            selected_folder = filedialog.askdirectory(initialdir=self.folder_path)
            if selected_folder:
                path_entry.delete(0, tk.END)
                path_entry.insert(0, selected_folder)

        browse_button = tk.Button(input_frame, text="选择文件夹", command=browse_folder)
        browse_button.pack(side="left", padx=5)
        folder_path = simpledialog.askstring("设置", "请输入文件夹目录:", initialvalue=self.folder_path)
        if folder_path:
            self.folder_path = folder_path
            self.save_settings()
            self.list_files_in_navigation()

    def save_settings(self):
        with open(self.settings_file, "w") as f:
            f.write(self.folder_path)

    def load_settings(self):
        if os.path.exists(self.settings_file):
            with open(self.settings_file, "r") as f:
                return f.read().strip()
        return ""

    def list_files_in_navigation(self):
        self.file_listbox.delete(0, tk.END)
        if os.path.exists(self.folder_path):
            for file in os.listdir(self.folder_path):
                self.file_listbox.insert(tk.END, file)

if __name__ == "__main__":
    app = MainApp()
    app.mainloop()