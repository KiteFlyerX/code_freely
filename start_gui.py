#!/usr/bin/env python
"""
CodeTraceAI GUI 启动脚本
"""
import sys
import os

# 设置路径
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

# 创建 QApplication - 必须在任何 PySide6 组件导入之前
from PySide6.QtWidgets import QApplication
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

app.setApplicationName("CodeTraceAI")
app.setApplicationDisplayName("CodeTraceAI")
app.setOrganizationName("CodeTraceAI")

# 初始化数据库
from src.database import init_database
init_database()

# 导入 GUI 组件并创建窗口
# 注意：不要导入 run_gui，直接导入 MainWindow
from src.gui.main_window import MainWindow

window = MainWindow()
window.show()

# 运行应用
sys.exit(app.exec())
