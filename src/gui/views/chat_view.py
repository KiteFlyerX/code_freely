"""
聊天视图
AI 对话界面
"""
from typing import Optional
from PySide6.QtCore import Qt, Signal, QThread, QObject, QEvent
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QScrollArea,
    QFrame, QLabel, QSizePolicy, QApplication
)
from PySide6.QtGui import QTextDocument, QTextCursor, QKeySequence, QShortcut
from qfluentwidgets import (
    TextEdit, PlainTextEdit, PushButton,
    ComboBox, BodyLabel, StrongBodyLabel, ScrollArea,
    CardWidget, SimpleCardWidget, InfoBar, InfoBarPosition
)

from ...services import (
    conversation_service, config_service,
    provider_manager, get_ai_client
)
from ...database import get_db_session
from ...database.repositories import MessageRepository


class MessageEdit(PlainTextEdit):
    """支持回车发送的消息输入框"""

    send_requested = Signal()

    def keyPressEvent(self, event):
        """处理按键事件"""
        # Ctrl+Enter 或 Shift+Enter 发送（允许换行）
        if (event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter):
            if event.modifiers() & (Qt.ControlModifier | Qt.ShiftModifier):
                # 换行
                super().keyPressEvent(event)
            else:
                # 发送消息
                self.send_requested.emit()
                return
        else:
            super().keyPressEvent(event)


class ChatWorker(QObject):
    """聊天工作线程"""
    response_received = Signal(str)
    tool_call_received = Signal(str)  # 工具调用信号
    error_occurred = Signal(str)
    finished = Signal()

    def __init__(self, conversation_id: int, content: str, work_dir=None):
        super().__init__()
        self.conversation_id = conversation_id
        self.content = content
        self.work_dir = work_dir

    def run(self):
        """运行聊天任务"""
        import asyncio

        try:
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            # 使用带工具调用的流式响应
            full_response = ""
            async def stream_chat():
                nonlocal full_response
                async for chunk in conversation_service.send_message_with_tools(
                    self.conversation_id, self.content, self.work_dir
                ):
                    full_response += chunk

            loop.run_until_complete(stream_chat())
            loop.close()

            self.response_received.emit(full_response)
        except Exception as e:
            self.error_occurred.emit(str(e))
        finally:
            self.finished.emit()


class MessageBubble(CardWidget):
    """消息气泡"""

    def __init__(self, role: str, content: str, parent=None):
        super().__init__(parent)
        self.role = role
        self.content = content
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)

        # 角色标签
        role_label = StrongBodyLabel(self._get_role_label())
        layout.addWidget(role_label)

        # 内容标签
        content_label = BodyLabel(self.content)
        content_label.setWordWrap(True)
        content_label.setTextFormat(Qt.PlainText)
        layout.addWidget(content_label)

        # 样式设置
        if self.role == "user":
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #e3f2fd;
                    border-radius: 12px;
                }
            """)
        else:
            self.setStyleSheet("""
                MessageBubble {
                    background-color: #f5f5f5;
                    border-radius: 12px;
                }
            """)

    def _get_role_label(self) -> str:
        """获取角色标签"""
        return "用户" if self.role == "user" else "AI"


class ChatView(QWidget):
    """
    聊天视图
    AI 对话界面
    """

    codeApplied = Signal(dict)  # 代码应用信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self.conversation_id: Optional[int] = None
        self.current_project_path: Optional[str] = None
        self.work_dir = None  # 当前工作目录
        self._is_processing = False
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 顶部工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # 消息区域
        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(400)

        self.messages_container = QWidget()
        self.messages_layout = QVBoxLayout(self.messages_container)
        self.messages_layout.setAlignment(Qt.AlignTop)
        self.messages_layout.setSpacing(12)

        self.scroll_area.setWidget(self.messages_container)
        layout.addWidget(self.scroll_area)

        # 输入区域
        input_area = self._create_input_area()
        layout.addWidget(input_area)

    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)

        # 项目选择
        layout.addWidget(BodyLabel("项目:"))
        self.project_combo = ComboBox()
        self.project_combo.setMinimumWidth(200)
        self.project_combo.addItems(["当前目录", "选择项目..."])
        layout.addWidget(self.project_combo)

        # 模型选择
        layout.addWidget(BodyLabel("模型:"))
        self.model_combo = ComboBox()
        self.model_combo.setMinimumWidth(150)
        self.model_combo.addItems(["claude-sonnet-4-6", "gpt-4o", "deepseek-chat"])
        layout.addWidget(self.model_combo)

        layout.addStretch()

        # 新建对话按钮
        new_chat_btn = PushButton("新建对话")
        new_chat_btn.clicked.connect(self._new_chat)
        layout.addWidget(new_chat_btn)

        return toolbar

    def _create_input_area(self) -> QWidget:
        """创建输入区域"""
        container = SimpleCardWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(16, 16, 16, 16)

        # 输入框 - 使用自定义 MessageEdit 支持回车发送
        self.input_edit = MessageEdit()
        self.input_edit.setPlaceholderText("输入你的问题或指令... (按 Enter 发送，Ctrl+Enter 换行)")
        self.input_edit.setMaximumHeight(120)
        self.input_edit.setTabChangesFocus(True)
        self.input_edit.send_requested.connect(self._send_message)
        layout.addWidget(self.input_edit)

        # 按钮区域
        button_layout = QHBoxLayout()

        # 提示标签
        self.status_label = BodyLabel("")
        self.status_label.setStyleSheet("color: #888;")
        button_layout.addWidget(self.status_label)

        button_layout.addStretch()

        self.send_btn = PushButton("发送")
        self.send_btn.clicked.connect(self._send_message)

        button_layout.addWidget(self.send_btn)

        layout.addLayout(button_layout)

        # 检查提供商配置
        self._check_provider_config()

        return container

    def _new_chat(self):
        """新建对话"""
        # 先检查提供商配置
        if not self._check_provider_config():
            return

        # 创建新对话
        title = "新对话"
        self.conversation_id = conversation_service.create_conversation(
            title=title,
            project_path=self.current_project_path,
        )

        # 清空消息区域
        self._clear_messages()

        InfoBar.success(
            title="新对话已创建",
            content=f"对话 ID: {self.conversation_id}",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def _check_provider_config(self) -> bool:
        """检查提供商配置"""
        try:
            from ...database import init_database
            init_database()

            provider = provider_manager.get_active_provider()
            if not provider:
                self.status_label.setText("未配置提供商")
                self.status_label.setStyleSheet("color: orange;")
                InfoBar.warning(
                    title="未配置提供商",
                    content="请先在'提供商管理'页面配置 AI 提供商和 API 密钥",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
                return False

            if not provider.api_key or provider.api_key.startswith("test"):
                self.status_label.setText("API 密钥无效")
                self.status_label.setStyleSheet("color: orange;")
                InfoBar.warning(
                    title="API 密钥未配置",
                    content=f"请为提供商 '{provider.name}' 配置有效的 API 密钥",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )
                return False

            # 配置有效
            self.status_label.setText(f"活动: {provider.name} ({provider.model})")
            self.status_label.setStyleSheet("color: green;")
            return True

        except Exception as e:
            self.status_label.setText("配置检查失败")
            self.status_label.setStyleSheet("color: red;")
            InfoBar.error(
                title="配置检查失败",
                content=str(e),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
            return False

    def set_work_dir(self, work_dir):
        """设置工作目录"""
        self.work_dir = work_dir

    def _send_message(self):
        """发送消息"""
        if self._is_processing:
            return

        content = self.input_edit.toPlainText().strip()
        if not content:
            return

        # 检查提供商配置
        if not self._check_provider_config():
            return

        # 如果没有对话，先创建
        if self.conversation_id is None:
            if not self._check_provider_config():
                return
            self._new_chat()
            if self.conversation_id is None:
                return

        # 添加用户消息气泡
        self._add_message_bubble("user", content)

        # 清空输入框
        self.input_edit.clear()

        # 禁用发送按钮
        self._set_processing(True)

        # 创建工作线程
        self._thread = QThread()
        self._worker = ChatWorker(self.conversation_id, content, self.work_dir)
        self._worker.moveToThread(self._thread)

        # 连接信号
        self._thread.started.connect(self._worker.run)
        self._worker.response_received.connect(self._on_response_received)
        self._worker.tool_call_received.connect(self._on_tool_call)
        self._worker.error_occurred.connect(self._on_error)
        self._worker.finished.connect(self._on_finished)
        self._worker.finished.connect(self._thread.quit)
        self._thread.finished.connect(self._thread.deleteLater)

        # 启动线程
        self._thread.start()

    def _on_tool_call(self, tool_info: str):
        """工具调用处理"""
        # 显示工具调用信息
        tool_label = BodyLabel(f"[工具调用] {tool_info}")
        tool_label.setStyleSheet("color: #666; font-style: italic; padding: 4px 8px; background: #f0f0f0; border-radius: 4px;")
        self.messages_layout.addWidget(tool_label)
        self._scroll_to_bottom()

    def _on_response_received(self, response: str):
        """响应接收处理"""
        # 添加 AI 消息气泡
        self._add_message_bubble("assistant", response)

        # 滚动到底部
        self._scroll_to_bottom()

    def _on_error(self, error: str):
        """错误处理"""
        # 分析错误类型并提供更友好的提示
        error_msg = str(error)

        if "401" in error_msg or "authentication" in error_msg.lower() or "api key" in error_msg.lower():
            provider = provider_manager.get_active_provider()
            InfoBar.error(
                title="API 密钥无效",
                content=f"提供商 '{provider.name if provider else '未知'}' 的 API 密钥无效或已过期。请在'提供商管理'页面更新。",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=8000,
                parent=self
            )
        elif "timeout" in error_msg.lower():
            InfoBar.error(
                title="请求超时",
                content="AI 服务响应超时，请检查网络连接或稍后重试。",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        elif "rate limit" in error_msg.lower():
            InfoBar.error(
                title="请求频率限制",
                content="API 请求过于频繁，请稍后再试。",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )
        else:
            InfoBar.error(
                title="请求失败",
                content=error_msg[:200] + "..." if len(error_msg) > 200 else error_msg,
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def _on_finished(self):
        """完成处理"""
        self._set_processing(False)

    def _add_message_bubble(self, role: str, content: str):
        """添加消息气泡"""
        bubble = MessageBubble(role, content)
        self.messages_layout.addWidget(bubble)

    def _clear_messages(self):
        """清空消息"""
        while self.messages_layout.count():
            item = self.messages_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

    def _scroll_to_bottom(self):
        """滚动到底部"""
        scrollbar = self.scroll_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _set_processing(self, processing: bool):
        """设置处理状态"""
        self._is_processing = processing
        self.send_btn.setEnabled(not processing)
        self.input_edit.setEnabled(not processing)

        if processing:
            self.send_btn.setText("思考中...")
        else:
            self.send_btn.setText("发送")
