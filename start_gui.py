#!/usr/bin/env python
"""
CodeTraceAI GUI 启动脚本
"""
import sys
import os

# 添加项目路径
script_dir = os.path.dirname(os.path.abspath(__file__))
project_dir = os.path.dirname(script_dir)
sys.path.insert(0, project_dir)

# 先创建 QApplication
from PySide6.QtWidgets import QApplication

app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

app.setApplicationName("CodeTraceAI")
app.setOrganizationName("CodeTraceAI")

# 现在导入并运行 GUI
from src.gui import MainWindow

window = MainWindow()
window.show()

sys.exit(app.exec())
