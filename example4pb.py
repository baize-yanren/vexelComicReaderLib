import sys
from PyQt5.QtWidgets import QApplication
from picture_browser import PictureBrowser

folder_path = ["D:/Documents/漫画/1/2448070-[Shiokou Yakyuubu (Shio)] KENxSOU [Digital]/2448070-[Shiokou Yakyuubu (Shio)] KENxSOU [Digital]",
    "D:/Documents/漫画/1/3342520-[URAGERI (Ura Renga)][Traditional Chinese]強制健康檢查[自由獸漢化組]/3342520-[URAGERI (Ura Renga)][Traditional Chinese]強制健康檢查[自由獸漢化組]"]

if __name__ == '__main__':
    # 必须先创建QApplication实例
    app = QApplication(sys.argv)
    
    # 方法1：直接初始化
    # browser = PictureBrowser(folder_path[0])
    # browser.show()
    # sys.exit(app.exec_())
    
    # 方法2：动态设置路径
    browser = PictureBrowser()
    if browser.set_image_folder(folder_path[0]):
        browser.show()    
        # 启动应用程序事件循环
        sys.exit(app.exec_())
    else:
        print("图片加载失败")
    

