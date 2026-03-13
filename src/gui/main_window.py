"""
主窗口
CodeTraceAI GUI 主窗口
"""
from typing import Optional
from PySide6.QtCore import Qt, Signal, QObject, QThread
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QStackedWidget,
    QMessageBox, QApplication
)
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon,
    setTheme, Theme, InfoBar, InfoBarPosition,
    PushButton, BodyLabel, SubtitleLabel, StrongBodyLabel
)

from ..services import (
    config_service, conversation_service, bug_service,
    review_service, knowledge_service
)
from .views.chat_view import ChatView
from .views.history_view import HistoryView
from .views.bug_view import BugView
from .views.review_view import ReviewView
from .views.knowledge_view import KnowledgeView
from .views.settings_view import SettingsView


class WorkerSignals(QObject):
    """工作线程信号"""
    error = Signal(str)
    finished = Signal()
    result = Signal(object)


class MainWindow(FluentWindow):
    """
    主窗口
    """

    def __init__(self):
        super().__init__()

        self.setWindowTitle("CodeTraceAI - AI 编程辅助与知识沉淀工具")
        self.setMinimumSize(1200, 800)

        # 初始化主题
        self._init_theme()

        # 创建子界面
        self.chat_view = ChatView()
        self.history_view = HistoryView()
        self.bug_view = BugView()
        self.review_view = ReviewView()
        self.knowledge_view = KnowledgeView()
        self.settings_view = SettingsView()

        # 添加到栈式窗口
        self.addSubInterface(
            self.chat_view, FluentIcon.CHAT, "AI 对话"
        )
        self.addSubInterface(
            self.history_view, FluentIcon.HISTORY, "修改历史"
        )
        self.addSubInterface(
            self.bug_view, FluentIcon.BUG, "Bug 追踪"
        )
        self.addSubInterface(
            self.review_view, FluentIcon.EDIT, "代码审查"
        )
        self.addSubInterface(
            self.knowledge_view, FluentIcon.DOCUMENT, "知识库"
        )
        self.addSubInterface(
            self.settings_view, FluentIcon.SETTING, "设置",
            position=NavigationItemPosition.BOTTOM
        )

        # 连接信号
        self._connect_signals()

        # 初始化配置
        self._init_config()

        # 显示欢迎信息
        self._show_welcome()

    def _init_theme(self):
        """初始化主题"""
        cfg = config_service.get_config()

        if cfg.theme == "dark":
            setTheme(Theme.DARK)
        elif cfg.theme == "light":
            setTheme(Theme.LIGHT)
        else:
            # 自动检测
            setTheme(Theme.AUTO)

    def _connect_signals(self):
        """连接信号"""
        # 聊天视图信号
        self.chat_view.codeApplied.connect(self._on_code_applied)

        # Bug 视图信号
        self.bug_view.bugCreated.connect(self._on_bug_created)

        # 审查视图信号
        self.review_view.reviewSubmitted.connect(self._on_review_submitted)

        # 知识库视图信号
        self.knowledge_view.entryCreated.connect(self._on_entry_created)

    def _init_config(self):
        """初始化配置"""
        # 验证 API 密钥
        if not conversation_service.validate_api_key():
            InfoBar.warning(
                title="API 密钥未配置",
                content="请在设置中配置您的 API 密钥以使用 AI 功能",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def _show_welcome(self):
        """显示欢迎信息"""
        InfoBar.success(
            title="欢迎使用 CodeTraceAI",
            content="AI 编程辅助与知识沉淀工具已就绪",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

    def _on_code_applied(self, data: dict):
        """代码应用事件处理"""
        file_path = data.get("file_path", "")
        InfoBar.success(
            title="代码已应用",
            content=f"已将修改应用到: {file_path}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

        # 可以在这里自动创建 Bug 追踪或知识库条目
        self._suggest_knowledge_extraction(data)

    def _on_bug_created(self, bug_id: int):
        """Bug 创建事件处理"""
        InfoBar.success(
            title="Bug 已创建",
            content=f"Bug ID: {bug_id}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

    def _on_review_submitted(self, review_id: int):
        """审查提交事件处理"""
        InfoBar.success(
            title="审查已提交",
            content=f"审查 ID: {review_id}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

    def _on_entry_created(self, entry_id: int):
        """知识库条目创建事件处理"""
        InfoBar.success(
            title="知识条目已创建",
            content=f"条目 ID: {entry_id}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=3000,
            parent=self
        )

    def _suggest_knowledge_extraction(self, data: dict):
        """建议提取知识"""
        # 这里可以弹出一个对话框询问是否提取到知识库
        pass

    def show_chat(self):
        """显示聊天界面"""
        self.navigationInterface.setCurrentItem(
            self.chat_view.objectName()
        )

    def show_history(self):
        """显示历史界面"""
        self.navigationInterface.setCurrentItem(
            self.history_view.objectName()
        )

    def show_bugs(self):
        """显示 Bug 界面"""
        self.navigationInterface.setCurrentItem(
            self.bug_view.objectName()
        )

    def show_reviews(self):
        """显示审查界面"""
        self.navigationInterface.setCurrentItem(
            self.review_view.objectName()
        )

    def show_knowledge(self):
        """显示知识库界面"""
        self.navigationInterface.setCurrentItem(
            self.knowledge_view.objectName()
        )

    def show_settings(self):
        """显示设置界面"""
        self.navigationInterface.setCurrentItem(
            self.settings_view.objectName()
        )


def run_gui():
    """运行 GUI 应用"""
    import sys

    # 确保没有已经存在的 QApplication 实例
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    app.setApplicationName("CodeTraceAI")
    app.setOrganizationName("CodeTraceAI")

    window = MainWindow()
    window.show()

    sys.exit(app.exec())
