#!/usr/bin/env python
"""
CodeTraceAI GUI 启动脚本
支持自动重启功能
"""
import sys
import os
import subprocess

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
exit_code = app.exec()

# 如果退出码是 133，表示需要重启
if exit_code == 133:
    print("正在重启应用...")
    # 重新启动应用
    try:
        # 使用相同的 Python 解释器和参数重新启动
        subprocess.Popen([sys.executable] + sys.argv)
    except Exception as e:
        print(f"重启失败: {e}")
        sys.exit(1)

sys.exit(exit_code)
