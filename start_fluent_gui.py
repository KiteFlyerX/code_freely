"""
CodeTraceAI GUI - 使用 PyQt-Fluent-Widgets 美化版本
使用 FluentWindow 和 qfluentwidgets 组件
"""
import sys
import os
import subprocess
from pathlib import Path

# 设置路径
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)
sys.path.insert(0, str(script_dir))

# qfluentwidgets 导入
from qfluentwidgets import (
    FluentWindow, NavigationItemPosition, FluentIcon,
    setTheme, Theme, InfoBar, InfoBarPosition,
    PushButton, PrimaryPushButton, BodyLabel, SubtitleLabel, StrongBodyLabel,
    SimpleCardWidget, CardWidget, ScrollArea, TextEdit, LineEdit,
    ComboBox, CheckBox, SwitchButton, ProgressBar,
    TableWidget, ListWidget, MessageBox,
    qconfig, QConfig, OptionsConfigItem, ConfigSerializer, BoolValidator,
    InfoBarIcon, Icon, PlainTextEdit
)

from PySide6.QtCore import Qt, Signal, QEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QStackedWidget, QApplication, QFileDialog, QHeaderView
)
from PySide6.QtGui import QFont, QTextCursor, QKeyEvent

# 尝试导入 markdown 库
try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False
    print("Warning: markdown not installed. Run: pip install markdown")

# 导入服务模块
try:
    from src.database import init_database
    from src.services import (
        config_service, conversation_service,
        provider_manager
    )
    from src.services.bug_service import bug_service, BugCreateInfo
    from src.services.knowledge_service import knowledge_service, KnowledgeCreateInfo
    from src.tools import tool_registry
    init_database()

    # 验证工具
    tools = tool_registry.list_tools()
    print(f"Services loaded. Tools: {[t.name for t in tools]}")

    if len(tools) == 0:
        print("Registering default tools...")
        from src.tools.default_tools import register_default_tools
        register_default_tools()
        tools = tool_registry.list_tools()

except Exception as e:
    print(f"Service load error: {e}")
    import traceback
    traceback.print_exc()
    provider_manager = None
    config_service = None
    conversation_service = None


def render_markdown(text):
    """渲染 Markdown"""
    if not HAS_MARKDOWN:
        return text
    try:
        md = markdown.Markdown(extensions=[
            'fenced_code', 'codehilite', 'tables', 'nl2br', 'sane_lists', 'toc',
        ])
        return md.convert(text)
    except Exception as e:
        print(f"Markdown error: {e}")
        return text


def format_chat_message(content):
    """格式化聊天消息"""
    if not HAS_MARKDOWN:
        return content
    return render_markdown(content)


class ChatWidget(QWidget):
    """聊天页面"""

    def __init__(self):
        super().__init__()
        self.setObjectName("chatWidget")
        self.chat_conversation_id = None
        self._is_processing = False

        # 当前工作目录
        self.current_work_dir = Path.cwd()

        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 顶部工具栏卡片
        toolbar_card = SimpleCardWidget()
        toolbar_layout = QHBoxLayout(toolbar_card)
        toolbar_layout.setContentsMargins(16, 12, 16, 12)

        # 提供商状态
        toolbar_layout.addWidget(StrongBodyLabel("AI:"))
        self.chat_status_label = BodyLabel("未配置提供商")
        self.chat_status_label.setStyleSheet("color: orange;")
        toolbar_layout.addWidget(self.chat_status_label)

        # Token 统计
        toolbar_layout.addWidget(BodyLabel("|"))
        self.token_stats_label = BodyLabel("Tokens: -")
        self.token_stats_label.setStyleSheet("color: #888; font-size: 11px;")
        self.token_stats_label.setToolTip("Token 使用统计")
        toolbar_layout.addWidget(self.token_stats_label)

        toolbar_layout.addStretch()

        # 自动提交选项
        self.auto_commit_checkbox = CheckBox("自动提交代码")
        # 从配置中读取自动提交状态
        try:
            auto_commit_enabled = config_service.get_config().auto_commit
            self.auto_commit_checkbox.setChecked(auto_commit_enabled)
        except:
            self.auto_commit_checkbox.setChecked(False)
        self.auto_commit_checkbox.setToolTip("应用代码修改时自动提交到 Git")
        toolbar_layout.addWidget(self.auto_commit_checkbox)

        toolbar_layout.addSpacing(10)

        # 版本号显示
        try:
            current_version = config_service.get_config().app_version
            self.version_label = BodyLabel(f"v{current_version}")
            self.version_label.setStyleSheet("color: #888; font-size: 11px;")
            self.version_label.setToolTip("当前版本")
            toolbar_layout.addWidget(self.version_label)
        except:
            pass

        toolbar_layout.addSpacing(10)

        # 新建对话按钮
        new_chat_btn = PrimaryPushButton("新建对话")
        new_chat_btn.clicked.connect(self._on_new_chat)
        toolbar_layout.addWidget(new_chat_btn)

        layout.addWidget(toolbar_card)

        # 聊天区域（使用卡片）
        chat_card = SimpleCardWidget()
        chat_layout = QVBoxLayout(chat_card)
        chat_layout.setContentsMargins(16, 16, 16, 16)

        # 消息显示区
        self.chat_area = TextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setMinimumHeight(400)
        chat_layout.addWidget(self.chat_area)

        layout.addWidget(chat_card, 1)

        # 输入区域卡片
        input_card = SimpleCardWidget()
        input_layout = QVBoxLayout(input_card)
        input_layout.setContentsMargins(16, 16, 16, 16)

        # 输入框
        self.chat_input = PlainTextEdit()
        self.chat_input.setPlaceholderText("输入你的问题... (Enter 发送, Shift+Enter 换行)")
        self.chat_input.setMaximumHeight(120)
        # 安装事件过滤器处理回车键
        self.chat_input.installEventFilter(self)
        input_layout.addWidget(self.chat_input)

        # 底部按钮区域
        button_layout = QHBoxLayout()

        # 左侧工作目录
        button_layout.addWidget(StrongBodyLabel("工作目录:"))
        self.work_dir_label = BodyLabel(self._get_work_dir_display())
        self.work_dir_label.setStyleSheet("color: #666; font-size: 11px;")
        self.work_dir_label.setMaximumWidth(300)
        self.work_dir_label.setToolTip(str(self.current_work_dir))
        button_layout.addWidget(self.work_dir_label)

        change_dir_btn = PushButton("切换")
        change_dir_btn.setFixedWidth(60)
        change_dir_btn.clicked.connect(self._change_work_directory)
        button_layout.addWidget(change_dir_btn)

        button_layout.addStretch()

        # 右侧发送按钮
        self.send_btn = PrimaryPushButton("发送")
        self.send_btn.clicked.connect(self._on_send)
        button_layout.addWidget(self.send_btn)

        input_layout.addLayout(button_layout)
        layout.addWidget(input_card)

        # 初始化状态
        self._check_provider()

    def _check_provider(self):
        """检查提供商配置"""
        try:
            provider = provider_manager.get_ccswitch_active_provider()
            is_from_ccswitch = True

            if not provider:
                provider = provider_manager.get_active_provider()
                is_from_ccswitch = False

            if provider:
                has_valid_key = bool(provider.api_key and not provider.api_key.startswith("test"))
                if has_valid_key:
                    ccswitch_tag = " [CC]" if is_from_ccswitch else ""
                    self.chat_status_label.setText(f"活动: {provider.name} ({provider.model}){ccswitch_tag}")
                    self.chat_status_label.setStyleSheet("color: green;")
                else:
                    self.chat_status_label.setText("API 密钥无效")
                    self.chat_status_label.setStyleSheet("color: orange;")
            else:
                self.chat_status_label.setText("未配置 (使用 CC-Switch)")
                self.chat_status_label.setStyleSheet("color: orange;")
        except Exception as e:
            self.chat_status_label.setText(f"配置错误: {e}")
            self.chat_status_label.setStyleSheet("color: red;")

    def _get_work_dir_display(self):
        """获取工作目录显示文本"""
        try:
            cwd = self.current_work_dir
            home = Path.home()

            if cwd.is_relative_to(home):
                return f"~/{cwd.relative_to(home)}"
            else:
                path_str = str(cwd)
                if len(path_str) > 40:
                    return "..." + path_str[-37:]
                return path_str
        except Exception as e:
            return str(self.current_work_dir)

    def _update_work_dir_display(self):
        """更新工作目录显示"""
        self.work_dir_label.setText(self._get_work_dir_display())
        self.work_dir_label.setToolTip(str(self.current_work_dir))

    def _change_work_directory(self):
        """切换工作目录"""
        from PySide6.QtWidgets import QFileDialog

        new_dir = QFileDialog.getExistingDirectory(
            self,
            "选择工作目录",
            str(self.current_work_dir)
        )

        if new_dir:
            try:
                new_path = Path(new_dir)
                os.chdir(new_path)
                self.current_work_dir = new_path
                self._update_work_dir_display()

                InfoBar.success(
                    title="目录已切换",
                    content=f"工作目录: {self._get_work_dir_display()}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            except Exception as e:
                InfoBar.error(
                    title="切换失败",
                    content=str(e),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )

    def _on_new_chat(self):
        """新建对话"""
        try:
            self.chat_conversation_id = conversation_service.create_conversation(
                title="新对话",
                project_path=None,
            )
            self.chat_area.clear()
            self.chat_area.append(f"--- 新对话 (ID: {self.chat_conversation_id}) ---")
            self.chat_area.append("\n欢迎使用 CodeTraceAI！\n")
            self.chat_area.append("配置提示: 请使用 CC-Switch 配置 AI 提供商\n")
            InfoBar.success(
                title="新对话已创建",
                content=f"对话 ID: {self.chat_conversation_id}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            self._update_token_stats()
        except Exception as e:
            InfoBar.error(
                title="创建失败",
                content=str(e),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def _on_send(self):
        """发送消息"""
        if self._is_processing:
            return

        content = self.chat_input.toPlainText().strip()
        if not content:
            return

        # 显示用户消息
        self.chat_area.append(f"\n[用户]: {content}")
        self.chat_input.clear()

        # 禁用输入
        self._set_processing(True)

        # 同步自动提交选项到配置
        from src.services.config_service import config_service
        config_service.update_app_config(auto_commit=self.auto_commit_checkbox.isChecked())

        # 使用线程处理
        import queue
        import threading
        import asyncio
        result_queue = queue.Queue()

        def run_chat():
            try:
                if self.chat_conversation_id is None:
                    self.chat_conversation_id = conversation_service.create_conversation("新对话")

                # 在新的事件循环中运行异步生成器
                async def stream_response():
                    async for chunk in conversation_service.send_message_with_tools_stream(
                        self.chat_conversation_id, content, self.current_work_dir
                    ):
                        # 实时发送每个 chunk
                        result_queue.put({"status": "chunk", "content": chunk})

                # 创建新的事件循环并运行
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    loop.run_until_complete(stream_response())
                finally:
                    loop.run_until_complete(loop.shutdown_asyncgens())
                    loop.close()

                result_queue.put({"status": "done"})
            except Exception as e:
                result_queue.put({"status": "error", "data": str(e)})
                result_queue.put({"status": "done"})

        threading.Thread(target=run_chat, daemon=True).start()

        # 轮询结果并实时显示
        from PySide6.QtCore import QTimer

        def check_result():
            try:
                while True:
                    result = result_queue.get_nowait()
                    if result.get("status") == "done":
                        self._set_processing(False)
                        self.chat_input.setFocus()
                        self._update_token_stats()
                        return
                    elif result.get("status") == "chunk":
                        # 实时显示流式内容
                        chunk = result.get("content", "")
                        # 移动光标到末尾并插入文本
                        cursor = self.chat_area.textCursor()
                        cursor.movePosition(QTextCursor.End)
                        self.chat_area.setTextCursor(cursor)
                        self.chat_area.insertPlainText(chunk)
                    elif result.get("status") == "error":
                        self.chat_area.append(f"\n[错误] {result.get('data', '')}")
            except queue.Empty:
                QTimer.singleShot(10, check_result)

        QTimer.singleShot(10, check_result)

    def _set_processing(self, processing):
        """设置处理状态"""
        self._is_processing = processing
        self.send_btn.setEnabled(not processing)
        self.chat_input.setEnabled(not processing)
        self.send_btn.setText("思考中..." if processing else "发送")

    def _update_token_stats(self):
        """更新 token 统计"""
        try:
            from src.database.repositories import MessageRepository, ConversationRepository
            from src.database import get_db_session

            msg_repo = MessageRepository(get_db_session())
            conv_repo = ConversationRepository(get_db_session())

            # 当前对话的token统计
            if self.chat_conversation_id:
                messages = msg_repo.get_by_conversation(self.chat_conversation_id)
                total_input = sum(m.input_tokens or 0 for m in messages)
                total_output = sum(m.output_tokens or 0 for m in messages)
                total_tokens = sum(m.total_tokens or 0 for m in messages)
                max_context = max((m.context_length or 0 for m in messages), default=0)
            else:
                total_input = total_output = total_tokens = 0
                max_context = 0

            # 所有对话的总token统计
            all_conversations = conv_repo.list_all()
            all_messages = []
            for conv in all_conversations:
                all_messages.extend(msg_repo.get_by_conversation(conv.id))

            total_input_all = sum(m.input_tokens or 0 for m in all_messages)
            total_output_all = sum(m.output_tokens or 0 for m in all_messages)
            total_tokens_all = sum(m.total_tokens or 0 for m in all_messages)

            if total_tokens > 0:
                self.token_stats_label.setText(
                    f"Tokens: {total_tokens:,} (入: {total_input:,}, 出: {total_output:,}) | 总计: {total_tokens_all:,} | 上下文: {max_context}"
                )
                self.token_stats_label.setStyleSheet("color: #10b981; font-size: 11px;")
            else:
                self.token_stats_label.setText(f"Tokens: - | 总计: {total_tokens_all:,} | 上下文: {max_context}")
                self.token_stats_label.setStyleSheet("color: #888; font-size: 11px;")

            # 更新版本号显示
            if hasattr(self, 'version_label'):
                try:
                    current_version = config_service.get_config().app_version
                    self.version_label.setText(f"v{current_version}")
                except:
                    pass

        except Exception as e:
            print(f"Token stats error: {e}")

    def eventFilter(self, obj, event):
        """事件过滤器 - 处理输入框的回车键"""
        if obj == self.chat_input and event.type() == QEvent.Type.KeyPress:
            if event.key() == Qt.Key.Key_Return or event.key() == Qt.Key.Key_Enter:
                # 检查是否有 Shift 修饰键
                if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
                    # Shift+Enter: 换行
                    cursor = self.chat_input.textCursor()
                    cursor.insertText("\n")
                    return True
                else:
                    # Enter: 发送消息
                    self._on_send()
                    return True
        return super().eventFilter(obj, event)


class HistoryWidget(QWidget):
    """历史记录页面"""

    def __init__(self):
        super().__init__()
        self.setObjectName("historyWidget")
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        # 标题卡片
        title_card = SimpleCardWidget()
        title_layout = QHBoxLayout(title_card)
        title_layout.setContentsMargins(16, 12, 16, 12)
        title_layout.addWidget(SubtitleLabel("修改历史"))
        title_layout.addStretch()
        layout.addWidget(title_card)

        # 内容卡片
        content_card = SimpleCardWidget()
        content_layout = QVBoxLayout(content_card)
        content_layout.setContentsMargins(16, 16, 16, 16)

        content_layout.addWidget(BodyLabel("代码修改历史记录"))
        layout.addWidget(content_card, 1)


class BugWidget(QWidget):
    """Bug 追踪页面"""

    def __init__(self):
        super().__init__()
        self.setObjectName("bugWidget")
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title_card = SimpleCardWidget()
        title_layout = QHBoxLayout(title_card)
        title_layout.setContentsMargins(16, 12, 16, 12)
        title_layout.addWidget(SubtitleLabel("Bug 追踪"))
        title_layout.addStretch()
        layout.addWidget(title_card)

        content_card = SimpleCardWidget()
        content_layout = QVBoxLayout(content_card)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.addWidget(BodyLabel("Bug 追踪与管理"))
        layout.addWidget(content_card, 1)


class KnowledgeWidget(QWidget):
    """知识库页面"""

    def __init__(self):
        super().__init__()
        self.setObjectName("knowledgeWidget")
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)

        title_card = SimpleCardWidget()
        title_layout = QHBoxLayout(title_card)
        title_layout.setContentsMargins(16, 12, 16, 12)
        title_layout.addWidget(SubtitleLabel("知识库"))
        title_layout.addStretch()
        layout.addWidget(title_card)

        content_card = SimpleCardWidget()
        content_layout = QVBoxLayout(content_card)
        content_layout.setContentsMargins(16, 16, 16, 16)
        content_layout.addWidget(BodyLabel("知识库浏览与搜索"))
        layout.addWidget(content_card, 1)


class SettingsWidget(QWidget):
    """设置页面"""

    def __init__(self):
        super().__init__()
        self.setObjectName("settingsWidget")
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)

        title_card = SimpleCardWidget()
        title_layout = QHBoxLayout(title_card)
        title_layout.setContentsMargins(16, 12, 16, 12)
        title_layout.addWidget(SubtitleLabel("设置"))
        title_layout.addStretch()
        main_layout.addWidget(title_card)

        # 创建滚动区域
        scroll_area = ScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setMinimumHeight(400)

        # 滚动内容容器
        scroll_content = QWidget()
        layout = QVBoxLayout(scroll_content)
        layout.setContentsMargins(0, 10, 0, 10)
        layout.setSpacing(16)

        # 配置说明卡片
        config_card = CardWidget()
        config_layout = QVBoxLayout(config_card)
        config_layout.setContentsMargins(16, 16, 16, 16)

        config_layout.addWidget(StrongBodyLabel("AI 配置说明"))

        ccswitch_info = BodyLabel()
        ccswitch_info.setText(
            "本应用使用 CC-Switch 管理 AI 提供商配置。\n\n"
            "配置步骤:\n"
            "1. 下载并安装 CC-Switch\n"
            "2. 在 CC-Switch 中添加您的 AI 提供商和 API 密钥\n"
            "3. 启用您想要使用的提供商\n"
            "4. 重启本应用即可自动读取配置"
        )
        ccswitch_info.setWordWrap(True)
        ccswitch_info.setStyleSheet("""
            BodyLabel {
                padding: 16px;
                background-color: rgba(13, 110, 253, 0.08);
                border-radius: 8px;
            }
        """)
        config_layout.addWidget(ccswitch_info)

        # CC-Switch 状态
        self.ccswitch_status_label = BodyLabel("正在检测 cc-switch...")
        self.ccswitch_status_label.setStyleSheet("""
            BodyLabel {
                padding: 12px;
                background-color: #f5f5f5;
                border-radius: 6px;
            }
        """)
        config_layout.addWidget(self.ccswitch_status_label)

        layout.addWidget(config_card)

        # 工具信息卡片
        tool_info_card = CardWidget()
        tool_info_layout = QVBoxLayout(tool_info_card)
        tool_info_layout.setContentsMargins(16, 16, 16, 16)

        tool_info_layout.addWidget(StrongBodyLabel("工具信息"))

        # 获取工具列表
        try:
            from src.tools import tool_registry
            tools = tool_registry.list_tools()

            tool_list_text = ""
            for tool in tools:
                tool_list_text += f"• {tool.name}: {tool.description}\n"

            tool_info_label = BodyLabel(tool_list_text if tool_list_text else "暂无工具")
        except Exception as e:
            tool_info_label = BodyLabel(f"加载工具失败: {e}")

        tool_info_label.setWordWrap(True)
        tool_info_label.setStyleSheet("""
            BodyLabel {
                padding: 12px;
                background-color: #ffffff;
                color: #000000;
                border: 1px solid #e0e0e0;
                border-radius: 6px;
                font-family: "Microsoft YaHei", "SimHei", Arial, sans-serif;
                font-size: 13px;
            }
        """)
        tool_info_layout.addWidget(tool_info_label)

        # 工具版本
        tool_version_label = BodyLabel("工具版本: v1.0.0")
        tool_version_label.setStyleSheet("""
            BodyLabel {
                padding: 8px;
                background-color: rgba(16, 185, 129, 0.1);
                color: #10b981;
                border-radius: 6px;
                font-weight: bold;
            }
        """)
        tool_info_layout.addWidget(tool_version_label)

        layout.addWidget(tool_info_card)
        layout.addStretch()

        # 设置滚动区域内容
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # 刷新状态
        self._refresh_ccswitch_status()

    def _refresh_ccswitch_status(self):
        """刷新 CC-Switch 状态"""
        if provider_manager is None:
            self.ccswitch_status_label.setText("❌ 服务未初始化")
            return

        try:
            provider = provider_manager.get_ccswitch_active_provider()
            if provider:
                self.ccswitch_status_label.setText(f"✅ CC-Switch: {provider.name} ({provider.model})")
                self.ccswitch_status_label.setStyleSheet("""
                    BodyLabel {
                        padding: 12px;
                        background-color: #e8f5e9;
                        color: #2e7d32;
                        border-radius: 6px;
                    }
                """)
            else:
                self.ccswitch_status_label.setText("⚠️ 未检测到 cc-switch 配置")
                self.ccswitch_status_label.setStyleSheet("""
                    BodyLabel {
                        padding: 12px;
                        background-color: #fff3e0;
                        color: #ef6c00;
                        border-radius: 6px;
                    }
                """)
        except Exception as e:
            self.ccswitch_status_label.setText(f"❌ 检测失败: {e}")


class MainWindow(FluentWindow):
    """主窗口 - 使用 FluentWindow"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CodeTraceAI - AI 编程辅助工具")
        self.setMinimumSize(1200, 800)

        # 初始化主题
        self._init_theme()

        # 创建子界面
        self.chat_widget = ChatWidget()
        self.history_widget = HistoryWidget()
        self.bug_widget = BugWidget()
        self.knowledge_widget = KnowledgeWidget()
        self.settings_widget = SettingsWidget()

        # 添加到导航
        self.addSubInterface(
            self.chat_widget, FluentIcon.CHAT, "AI 对话"
        )
        self.addSubInterface(
            self.history_widget, FluentIcon.HISTORY, "修改历史"
        )
        self.addSubInterface(
            self.bug_widget, FluentIcon.DEVELOPER_TOOLS, "Bug 追踪"
        )
        self.addSubInterface(
            self.knowledge_widget, FluentIcon.DOCUMENT, "知识库"
        )
        self.addSubInterface(
            self.settings_widget, FluentIcon.SETTING, "设置",
            position=NavigationItemPosition.BOTTOM
        )

        # 设置窗口图标
        self.setWindowTitle("CodeTraceAI")

    def _init_theme(self):
        """初始化主题"""
        try:
            cfg = config_service.get_config()
            if cfg.theme == "dark":
                setTheme(Theme.DARK)
            elif cfg.theme == "light":
                setTheme(Theme.LIGHT)
            else:
                setTheme(Theme.AUTO)
        except:
            setTheme(Theme.AUTO)


def main():
    """主函数"""
    app = QApplication(sys.argv)
    app.setApplicationName("CodeTraceAI")
    app.setOrganizationName("CodeTraceAI")

    # 设置应用样式
    app.setStyle("Fusion")

    # 创建主窗口
    window = MainWindow()
    window.show()

    sys.exit(app.exec())


if __name__ == "__main__":
    main()
