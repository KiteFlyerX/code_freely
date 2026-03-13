"""
最小 GUI 测试
"""
import sys
from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget

# 创建应用
app = QApplication(sys.argv)

# 创建窗口
window = QMainWindow()
window.setWindowTitle("CodeTraceAI Test")
window.setMinimumSize(400, 300)

# 创建中心部件
central = QWidget()
layout = QVBoxLayout(central)
label = QLabel("CodeTraceAI GUI 测试 - 如果你看到这个窗口，说明 GUI 基础功能正常！")
layout.addWidget(label)
window.setCentralWidget(central)
window.show()

# 运行
sys.exit(app.exec())
