#!/usr/bin/env python
"""
CodeFreely GUI 启动脚本 - 安全版本
完全避免导入顺序问题
"""
import sys
import os

# 设置路径
script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

# 第一步：创建 QApplication（必须在任何 Qt 导入之前�?from PySide6.QtWidgets import QApplication
app = QApplication.instance()
if app is None:
    app = QApplication(sys.argv)
app.setApplicationName("CodeFreely")
app.setApplicationDisplayName("CodeFreely")
app.setOrganizationName("CodeFreely")

# 第二步：初始化数据库
from src.database import init_database
init_database()

# 第三步：延迟导入 GUI 组件
# 直接在这里创建所有组件，避免通过 import 触发模块级代�?
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QFrame, QLabel, QPushButton,
    QStackedWidget, QSizePolicy, QApplication as QtApplication
)

# 导入 Fluent Widgets 组件
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon,
    setTheme, Theme, InfoBar, InfoBarPosition,
    PushButton, BodyLabel, StrongBodyLabel, SubtitleLabel
)

# 现在导入服务和模�?from src.services import config_service, conversation_service
from src.services.config_service import AIConfig
from src.ai import get_ai_provider

# 导入视图组件
from src.gui.views.chat_view import ChatView
from src.gui.views.history_view import HistoryView
from src.gui.views.bug_view import BugView
from src.gui.views.review_view import ReviewView
from src.gui.views.knowledge_view import KnowledgeView
from src.gui.views.settings_view import SettingsView

# 创建主窗�?class SimpleMainWindow(FluentWindow):
    """简化的主窗口，用于测试"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("AI辅助编程")
        self.setMinimumSize(1200, 800)

        # 初始化主�?        cfg = config_service.get_config()
        if cfg.theme == "dark":
            setTheme(Theme.DARK)
        elif cfg.theme == "light":
            setTheme(Theme.LIGHT)
        else:
            setTheme(Theme.AUTO)

        # 创建子界�?        self.chat_view = ChatView()
        self.history_view = HistoryView()
        self.bug_view = BugView()
        self.review_view = ReviewView()
        self.knowledge_view = KnowledgeView()
        self.settings_view = SettingsView()

        # 添加到导�?        self.addSubInterface(self.chat_view, FluentIcon.CHAT, "AI 对话")
        self.addSubInterface(self.history_view, FluentIcon.HISTORY, "修改历史")
        self.addSubInterface(self.bug_view, FluentIcon.BUG, "Bug 追踪")
        self.addSubInterface(self.review_view, FluentIcon.EDIT, "代码审查")
        self.addSubInterface(self.knowledge_view, FluentIcon.DOCUMENT, "知识�?)
        self.addSubInterface(self.settings_view, FluentIcon.SETTING, "设置",
                          position=NavigationItemPosition.BOTTOM)

        # 显示欢迎信息
        InfoBar.success(
            title="欢迎使用 CodeFreely",
            content="AI 编程辅助与知识沉淀工具已就�?,
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

# 创建并显示窗�?window = SimpleMainWindow()
window.show()

# 运行应用
sys.exit(app.exec())
