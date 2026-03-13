#!/usr/bin/env python
"""
CodeTraceAI GUI 启动脚本
"""
import sys
import os

# 添加项目路径
script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

# 创建 QApplication - 必须在任何 Qt 组件之前
from PySide6.QtWidgets import QApplication

# 检查是否已有实例
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)

app.setApplicationName("CodeTraceAI")
app.setApplicationDisplayName("CodeTraceAI")
app.setOrganizationName("CodeTraceAI")

# 初始化数据库
from src.database import init_database
init_database()

# 导入并创建主窗口
from src.gui.main_window import MainWindow

window = MainWindow()
window.show()

# 运行应用
sys.exit(app.exec())
