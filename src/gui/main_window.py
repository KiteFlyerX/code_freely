"""
主窗口
CodeFreely GUI 主窗口
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

        self.setWindowTitle("AI辅助编程")
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

        # 设置视图信号
        self.settings_view.settings_changed.connect(self._on_settings_changed)

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
            title="欢迎使用 AI辅助编程",
            content="AI 编程辅助工具已就绪",
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

    def _on_settings_changed(self):
        """设置更改事件处理 - 重新加载主题"""
        self._reload_theme()

    def _reload_theme(self):
        """重新加载主题"""
        cfg = config_service.get_config()

        if cfg.theme == "dark":
            setTheme(Theme.DARK)
        elif cfg.theme == "light":
            setTheme(Theme.LIGHT)
        else:
            # 自动检测
            setTheme(Theme.AUTO)

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

    def restart_app(self):
        """重启应用程序"""
        from PySide6.QtCore import QTimer
        import sys

        # 显示提示信息
        InfoBar.info(
            title="正在重启",
            content="应用即将关闭并重新启动...",
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

        # 延迟执行重启
        QTimer.singleShot(1000, self._perform_restart)

    def _perform_restart(self):
        """执行重启操作"""
        import sys
        import os

        app = QApplication.instance()

        # 关闭所有窗口
        app.closeAllWindows()

        # 退出应用（返回码 133 表示需要重启）
        # 可以在外部启动脚本中检测这个返回码并自动重启
        app.exit(133)


def run_gui():
    """运行 GUI 应用"""
    import sys
    import locale

    # 确保使用 UTF-8 编码
    try:
        if sys.platform.startswith('win'):
            # Windows 系统
            import codecs
            import sys
            sys.stdout.reconfigure(encoding='utf-8')
            sys.stderr.reconfigure(encoding='utf-8')
            
            # 设置控制台代码页为 UTF-8
            import locale
            import ctypes
            ctypes.windll.kernel32.SetConsoleOutputCP(65001)
            
        # 设置默认编码
        if hasattr(sys, 'set_int_max_str_digits'):
            sys.set_int_max_str_digits(0)
            
    except Exception as e:
        print(f"编码设置警告: {e}")

    # 确保没有已经存在的 QApplication 实例
    app = QApplication.instance()
    if app is None:
        app = QApplication(sys.argv)

    # 设置应用程序元数据
    app.setApplicationName("CodeFreely")
    app.setOrganizationName("CodeFreely")
    
    # 设置字体以支持中文
    from PySide6.QtGui import QFontDatabase
    font = app.font()
    font.setPointSize(10)
    app.setFont(font)

    window = MainWindow()
    window.show()

    # 运行应用并获取退出码
    exit_code = app.exec()

    # 如果退出码是 133，表示需要重启
    if exit_code == 133:
        import subprocess
        import os

        # 重新启动应用
        # 获取当前脚本路径
        current_script = sys.argv[0]
        if not current_script or current_script == "-c":
            # 如果是交互式运行，尝试找到主入口
            current_script = os.path.join(os.path.dirname(__file__), "..", "..", "start_gui.py")

        # 使用相同的 Python 解释器重新启动
        try:
            subprocess.Popen([sys.executable, current_script] + sys.argv[1:])
        except Exception as e:
            print(f"重启失败: {e}")
            sys.exit(1)

    sys.exit(exit_code)
