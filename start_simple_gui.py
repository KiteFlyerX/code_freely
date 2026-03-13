"""
CodeTraceAI GUI - 简化工作版本
基于成功运行的 test_minimal_gui.py 构建
"""
import sys
import os
import subprocess
from pathlib import Path

# 设置路径
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)
sys.path.insert(0, str(script_dir))

# 创建应用
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QListWidget, QStackedWidget,
    QInputDialog, QMessageBox, QLineEdit, QFileDialog, QSplitter, QStatusBar
)
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor, QTextDocument

# 尝试导入 markdown 库
try:
    import markdown
    HAS_MARKDOWN = True
except ImportError:
    HAS_MARKDOWN = False
    print("Warning: markdown not installed. Run: pip install markdown")

# 导入服务模块（这些不涉及 Qt）
try:
    from src.database import init_database
    from src.services import (
        config_service, conversation_service,
        provider_manager, ProviderConfig, ProviderType
    )
    # 尝试导入 PROVIDER_PRESETS，如果失败则使用空列表
    try:
        from src.services import PROVIDER_PRESETS
    except ImportError:
        PROVIDER_PRESETS = []
        print("Warning: PROVIDER_PRESETS not available")
    from src.services.bug_service import bug_service, BugCreateInfo
    from src.services.knowledge_service import knowledge_service, KnowledgeCreateInfo
    init_database()
    print("Services loaded successfully")
except Exception as e:
    print(f"Warning: Some services failed to load: {e}")
    # 设置默认值避免程序崩溃
    PROVIDER_PRESETS = []
    provider_manager = None
    config_service = None
    conversation_service = None


def render_markdown(text):
    """将 Markdown 文本转换为 HTML"""
    if not HAS_MARKDOWN:
        return text

    try:
        import markdown
        # 配置 Markdown 扩展
        md = markdown.Markdown(extensions=[
            'fenced_code',      # 代码块 ```lang```
            'codehilite',       # 语法高亮
            'tables',           # 表格
            'nl2br',            # 换行转 <br>
            'sane_lists',       # 更好的列表
            'toc',              # 目录
        ])

        # 转换为 HTML
        html = md.convert(text)

        # 添加 CSS 样式
        styled_html = f"""
        <style>
            body {{
                font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;
                font-size: 10pt;
                line-height: 1.6;
                color: #333;
            }}
            h1, h2, h3, h4, h5, h6 {{
                color: #1976d2;
                margin-top: 16px;
                margin-bottom: 8px;
                font-weight: 600;
            }}
            h1 {{ font-size: 1.5em; border-bottom: 2px solid #e0e0e0; padding-bottom: 8px; }}
            h2 {{ font-size: 1.3em; border-bottom: 1px solid #e0e0e0; padding-bottom: 4px; }}
            h3 {{ font-size: 1.15em; }}
            code {{
                font-family: 'Consolas', 'Courier New', monospace;
                background-color: #f5f5f5;
                padding: 2px 6px;
                border-radius: 3px;
                font-size: 0.9em;
            }}
            pre {{
                background-color: #263238;
                color: #eceff1;
                padding: 12px;
                border-radius: 4px;
                overflow-x: auto;
                margin: 8px 0;
            }}
            pre code {{
                background-color: transparent;
                padding: 0;
                color: inherit;
            }}
            blockquote {{
                border-left: 4px solid #1976d2;
                margin: 8px 0;
                padding-left: 12px;
                color: #666;
                font-style: italic;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 8px 0;
            }}
            th, td {{
                border: 1px solid #e0e0e0;
                padding: 8px 12px;
                text-align: left;
            }}
            th {{
                background-color: #f5f5f5;
                font-weight: 600;
            }}
            ul, ol {{
                margin: 8px 0;
                padding-left: 24px;
            }}
            li {{
                margin: 4px 0;
            }}
            a {{
                color: #1976d2;
                text-decoration: none;
            }}
            a:hover {{
                text-decoration: underline;
            }}
            .tool-call {{
                color: #388e3c;
                font-weight: 500;
                margin: 8px 0;
            }}
            .system-msg {{
                color: #757575;
                font-style: italic;
                margin: 4px 0;
            }}
        </style>
        {html}
        """
        return styled_html
    except Exception as e:
        print(f"Markdown render error: {e}")
        return text


def format_chat_message(content):
    """格式化聊天消息，支持简单的 Markdown 语法"""
    if not HAS_MARKDOWN:
        return content

    # 处理系统消息标记
    lines = []
    for line in content.split('\n'):
        if line.startswith('> 使用工具:'):
            lines.append(f'<p class="tool-call">{line}</p>')
        elif line.startswith('[系统]'):
            lines.append(f'<p class="system-msg">{line}</p>')
        elif line.startswith('[AI]'):
            lines.append(f'<p class="system-msg">{line}</p>')
        elif line.startswith('[错误]'):
            lines.append(f'<p class="error-msg" style="color:#d32f2f;">{line}</p>')
        else:
            lines.append(line)

    formatted = '\n'.join(lines)
    return render_markdown(formatted)


# 全局样式设置
def setup_app_style(app, dark_mode=False):
    """设置应用样式"""
    # 设置默认字体
    font = QFont("Segoe UI", 10)
    app.setFont(font)

    # 设置样式表
    app.setStyle("Fusion")

    # 根据模式选择配色
    if dark_mode:
        bg_color = "#1e1e1e"
        widget_bg = "#252526"
        text_color = "#e0e0e0"
        input_bg = "#2d2d2d"
        border_color = "#3e3e42"
        button_bg = "#0d6efd"
        button_hover = "#0b5ed7"
        table_bg = "#2d2d2d"
        table_header = "#3e3e42"
        list_bg = "#2d2d2d"
        list_hover = "#3e3e42"
        list_selected = "#1a3a5c"
        code_bg = "#1e1e1e"
        link_color = "#4dabf7"
    else:
        bg_color = "#f5f5f5"
        widget_bg = "#ffffff"
        text_color = "#333333"
        input_bg = "#ffffff"
        border_color = "#e0e0e0"
        button_bg = "#1976d2"
        button_hover = "#1565c0"
        table_bg = "#ffffff"
        table_header = "#fafafa"
        list_bg = "#ffffff"
        list_hover = "#f5f5f5"
        list_selected = "#e3f2fd"
        code_bg = "#263238"
        link_color = "#1976d2"

    # 自定义样式
    style_sheet = f"""
    QMainWindow {{
        background-color: {bg_color};
    }}

    QWidget {{
        background-color: {bg_color};
        color: {text_color};
        font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;
        font-size: 10pt;
    }}

    QListWidget {{
        background-color: {list_bg};
        border: 1px solid {border_color};
        border-radius: 4px;
        padding: 4px;
    }}

    QListWidget::item {{
        padding: 8px;
        border-radius: 3px;
    }}

    QListWidget::item:selected {{
        background-color: {list_selected};
        color: #ffffff;
    }}

    QListWidget::item:hover {{
        background-color: {list_hover};
    }}

    QPushButton {{
        background-color: {button_bg};
        color: #ffffff;
        border: none;
        border-radius: 4px;
        padding: 8px 16px;
        font-weight: 500;
    }}

    QPushButton:hover {{
        background-color: {button_hover};
    }}

    QPushButton:pressed {{
        background-color: #0d47a1;
    }}

    QPushButton:disabled {{
        background-color: #5a5a5a;
        color: #a0a0a0;
    }}

    QTextEdit {{
        background-color: {input_bg};
        border: 1px solid {border_color};
        border-radius: 4px;
        padding: 8px;
        font-family: 'Consolas', 'Monaco', 'Courier New', monospace;
        font-size: 10pt;
        line-height: 1.5;
        selection-background-color: {list_selected};
        color: {text_color};
    }}

    QLineEdit {{
        background-color: {input_bg};
        border: 1px solid {border_color};
        border-radius: 4px;
        padding: 6px 10px;
        font-size: 10pt;
        color: {text_color};
    }}

    QLineEdit:focus {{
        border: 1px solid {button_bg};
    }}

    QTableWidget {{
        background-color: {table_bg};
        border: 1px solid {border_color};
        border-radius: 4px;
        gridline-color: {border_color};
        color: {text_color};
    }}

    QTableWidget::item {{
        padding: 6px;
        border-bottom: 1px solid {border_color};
    }}

    QTableWidget::item:selected {{
        background-color: {list_selected};
        color: #ffffff;
    }}

    QTableWidget::horizontalHeader {{
        background-color: {table_header};
        border-bottom: 2px solid {border_color};
        padding: 8px;
        font-weight: 600;
    }}

    QHeaderView::section {{
        background-color: {table_header};
        border: none;
        border-bottom: 2px solid {border_color};
        border-right: 1px solid {border_color};
        padding: 8px;
        font-weight: 600;
    }}

    QLabel {{
        color: {text_color};
        font-size: 10pt;
    }}

    QStatusBar {{
        background-color: {widget_bg};
        border-top: 1px solid {border_color};
        color: #a0a0a0;
    }}

    /* Markdown 渲染样式 */
    body {{
        font-family: 'Segoe UI', 'Microsoft YaHei UI', sans-serif;
        font-size: 10pt;
        line-height: 1.6;
        color: {text_color};
    }}

    h1, h2, h3, h4, h5, h6 {{
        color: {link_color};
        margin-top: 16px;
        margin-bottom: 8px;
        font-weight: 600;
    }}

    h1 {{ font-size: 1.5em; border-bottom: 2px solid {border_color}; padding-bottom: 8px; }}
    h2 {{ font-size: 1.3em; border-bottom: 1px solid {border_color}; padding-bottom: 4px; }}

    code {{
        font-family: 'Consolas', 'Courier New', monospace;
        background-color: {list_hover};
        padding: 2px 6px;
        border-radius: 3px;
        font-size: 0.9em;
    }}

    pre {{
        background-color: {code_bg};
        color: #eceff1;
        padding: 12px;
        border-radius: 4px;
        overflow-x: auto;
        margin: 8px 0;
    }}

    pre code {{
        background-color: transparent;
        padding: 0;
        color: inherit;
    }}

    blockquote {{
        border-left: 4px solid {link_color};
        margin: 8px 0;
        padding-left: 12px;
        color: #a0a0a0;
        font-style: italic;
    }}

    table {{
        border-collapse: collapse;
        width: 100%;
        margin: 8px 0;
    }}

    th, td {{
        border: 1px solid {border_color};
        padding: 8px 12px;
        text-align: left;
    }}

    th {{
        background-color: {list_hover};
        font-weight: 600;
    }}

    a {{
        color: {link_color};
        text-decoration: none;
    }}

    a:hover {{
        text-decoration: underline;
    }}

    .tool-call {{
        color: #388e3c;
        font-weight: 500;
        margin: 8px 0;
    }}

    .system-msg {{
        color: #a0a0a0;
        font-style: italic;
        margin: 4px 0;
    }}
    """
    app.setStyleSheet(style_sheet)

# 简化的主窗口
class CodeTraceAIWindow(QMainWindow):
    """简化的主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CodeTraceAI - AI 编程辅助与知识沉淀工具")
        self.setMinimumSize(1000, 700)

        # 当前工作目录
        self.current_work_dir = Path.cwd()

        # 活跃的线程列表
        self._active_threads = []

        # HTML 模式标志（用于 Markdown 渲染）
        self._use_html = HAS_MARKDOWN

        # 深色模式标志
        self._dark_mode = True

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 左侧导航
        nav_list = QListWidget()
        nav_list.addItems([
            "AI 对话",
            "修改历史",
            "Bug 追踪",
            "知识库",
            "提供商管理",
            "设置"
        ])
        nav_list.setMaximumWidth(150)
        nav_list.currentRowChanged.connect(self.show_page)

        # 右侧内容区
        self.content_stack = QStackedWidget()
        self.pages = {}

        # 创建各个页面
        self.create_chat_page()
        self.create_history_page()
        self.create_bug_page()
        self.create_knowledge_page()
        self.create_provider_page()
        self.create_settings_page()

        # 添加到布局
        main_layout.addWidget(nav_list)
        main_layout.addWidget(self.content_stack)

        # 创建状态栏显示工作目录
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self._update_work_dir_display()

        # 添加切换目录按钮到状态栏
        change_dir_btn = QPushButton("切换目录")
        change_dir_btn.setMaximumWidth(80)
        change_dir_btn.clicked.connect(self._change_work_directory)
        self.statusBar.addPermanentWidget(change_dir_btn)

    def _update_work_dir_display(self):
        """更新工作目录显示"""
        try:
            # 显示相对路径（如果可能）
            from pathlib import Path
            cwd = Path.cwd()
            home = Path.home()

            if cwd.is_relative_to(home):
                # 显示为 ~/path 格式
                display_path = f"~/{cwd.relative_to(home)}"
            else:
                display_path = str(cwd)

            # 限制显示长度
            if len(display_path) > 50:
                display_path = "..." + display_path[-47:]

            self.statusBar.showMessage(f"工作目录: {display_path}")
        except Exception as e:
            self.statusBar.showMessage(f"工作目录: {str(self.current_work_dir)}")

    def _append_chat_message(self, role, content):
        """追加聊天消息，支持 Markdown 渲染"""
        from PySide6.QtGui import QTextCursor

        if role == "user":
            # 用户消息：普通文本
            self.chat_area.append(f"\n[用户]: {content}")
        elif role == "ai":
            if self._use_html:
                # 使用 HTML/Markdown 渲染
                cursor = self.chat_area.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.chat_area.setTextCursor(cursor)

                # 渲染 Markdown
                html_content = format_chat_message(content)
                self.chat_area.insertHtml(html_content)
            else:
                # 纯文本模式
                self.chat_area.append(f"\n[AI]: {content}")
        else:
            self.chat_area.append(f"\n{content}")

        # 滚动到底部
        scrollbar = self.chat_area.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _change_work_directory(self):
        """切换工作目录"""
        from pathlib import Path

        # 使用文件对话框选择目录
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

                QMessageBox.information(
                    self,
                    "目录已切换",
                    f"工作目录已切换到:\n{new_path}"
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "切换失败",
                    f"无法切换到目录 {new_dir}:\n{str(e)}"
                )

    def create_chat_page(self):
        """创建聊天页面"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # 顶部工具栏
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("AI 对话"))

        # 提供商状态
        toolbar.addWidget(QLabel("|"))
        self.chat_status_label = QLabel("未配置提供商")
        self.chat_status_label.setStyleSheet("color: orange; font-size: 11px;")
        toolbar.addWidget(self.chat_status_label)

        toolbar.addStretch()

        new_btn = QPushButton("新建对话")
        new_btn.clicked.connect(self._on_new_chat)
        toolbar.addWidget(new_btn)

        commit_btn = QPushButton("提交代码")
        commit_btn.setToolTip("提交当前目录的代码更改")
        commit_btn.clicked.connect(self._on_commit_code)
        toolbar.addWidget(commit_btn)

        layout.addLayout(toolbar)

        # 聊天区域
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setPlaceholderText("对话记录将显示在这里...")
        # 设置等宽字体用于代码显示
        chat_font = QFont("Consolas", 10)
        if not chat_font.exactMatch():
            chat_font = QFont("Courier New", 10)
        self.chat_area.setFont(chat_font)
        layout.addWidget(self.chat_area)

        # 输入区域
        input_layout = QVBoxLayout()

        # 自定义输入框，支持回车发送
        self.chat_input = QTextEdit()
        self.chat_input.setMaximumHeight(80)
        self.chat_input.setPlaceholderText("输入你的问题... (按 Enter 发送，Shift+Enter 换行)")

        # 创建自定义 keyPressEvent 处理
        original_key_press = self.chat_input.keyPressEvent

        def custom_key_press(event):
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                if event.modifiers() & Qt.ShiftModifier:
                    # Shift+Enter 换行
                    original_key_press(event)
                else:
                    # Enter 发送
                    self._on_send_chat_message()
            else:
                original_key_press(event)

        self.chat_input.keyPressEvent = custom_key_press

        input_layout.addWidget(self.chat_input)

        # 按钮行
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        send_btn = QPushButton("发送")
        send_btn.clicked.connect(self._on_send_chat_message)
        button_layout.addWidget(send_btn)

        input_layout.addLayout(button_layout)
        layout.addLayout(input_layout)

        self.pages["AI 对话"] = page
        self.content_stack.addWidget(page)

        # 检查提供商配置
        self._check_chat_provider()

        # 恢复上次的对话
        self._restore_last_conversation()

    def _restore_last_conversation(self):
        """恢复上次的对话"""
        try:
            config = config_service.get_config()
            last_id = config.last_conversation_id

            if last_id:
                # 获取对话信息
                conv = conversation_service.get_conversation(last_id)
                if conv:
                    self.chat_conversation_id = last_id
                    # 加载历史消息
                    messages = conversation_service.get_messages(last_id)

                    self.chat_area.clear()
                    self.chat_area.append(f"--- 恢复对话 (ID: {last_id}) ---")

                    # 显示历史消息
                    for msg in messages:
                        if msg.role == "user":
                            self.chat_area.append(f"\n[用户]: {msg.content}")
                        elif msg.role == "assistant":
                            if self._use_html:
                                html_content = format_chat_message(msg.content)
                                self.chat_area.append(html_content)
                            else:
                                self.chat_area.append(f"\n[AI]: {msg.content}")

                    # 显示系统消息
                    if self._use_html:
                        from PySide6.QtGui import QTextCursor
                        cursor = self.chat_area.textCursor()
                        cursor.movePosition(QTextCursor.End)
                        self.chat_area.setTextCursor(cursor)

                        system_info = """
**Claude Code 模式已启用**

可用工具:
- Read - 读取文件内容
- Write - 写入文件内容
- Bash - 执行系统命令
- Glob - 搜索文件
"""
                        html_content = format_chat_message(system_info.format(str(self.current_work_dir)))
                        self.chat_area.append(html_content)
                    else:
                        self.chat_area.append("[系统] Claude Code 模式已启用")
                        self.chat_area.append("[系统] 当前工作目录: " + str(self.current_work_dir))
                else:
                    # 对话不存在，创建新对话
                    self._on_new_chat()
            else:
                # 没有上次的对话，创建新对话
                self._on_new_chat()
        except Exception as e:
            print(f"恢复对话失败: {e}")
            self._on_new_chat()

    def _check_chat_provider(self):
        """检查聊天提供商配置"""
        try:
            provider = provider_manager.get_active_provider()
            if provider:
                has_valid_key = bool(provider.api_key and not provider.api_key.startswith("test"))
                if has_valid_key:
                    self.chat_status_label.setText(f"活动: {provider.name} ({provider.model})")
                    self.chat_status_label.setStyleSheet("color: green; font-size: 11px;")
                else:
                    self.chat_status_label.setText("API 密钥无效")
                    self.chat_status_label.setStyleSheet("color: orange; font-size: 11px;")
            else:
                self.chat_status_label.setText("未配置提供商")
                self.chat_status_label.setStyleSheet("color: orange; font-size: 11px;")
        except Exception as e:
            self.chat_status_label.setText(f"配置错误: {e}")
            self.chat_status_label.setStyleSheet("color: red; font-size: 11px;")

    def _on_new_chat(self):
        """新建对话"""
        try:
            self.chat_conversation_id = conversation_service.create_conversation(
                title="新对话",
                project_path=None,
            )
            self.chat_area.clear()
            self.chat_area.append(f"--- 新对话 (ID: {self.chat_conversation_id}) ---")

            # 使用 Markdown 渲染系统消息
            if self._use_html:
                from PySide6.QtGui import QTextCursor
                cursor = self.chat_area.textCursor()
                cursor.movePosition(QTextCursor.End)
                self.chat_area.setTextCursor(cursor)

                system_info = """
**Claude Code 模式已启用**

**可用工具:**
- `Read` - 读取文件内容
- `Write` - 写入文件内容
- `Bash` - 执行系统命令
- `Glob` - 搜索文件

**当前工作目录:** `{}`
"""
                html_content = format_chat_message(system_info.format(str(self.current_work_dir)))
                self.chat_area.insertHtml(html_content)
            else:
                self.chat_area.append("\n[系统] Claude Code 模式已启用")
                self.chat_area.append("[系统] 可用工具: Read(读取文件), Write(写入文件), Bash(执行命令), Glob(搜索文件)")
                self.chat_area.append("[系统] 当前工作目录: " + str(self.current_work_dir))
        except Exception as e:
            self.chat_area.append(f"\n[错误] 创建对话失败: {e}")

    def _on_send_chat_message(self):
        """发送聊天消息（带工具调用，实时流式输出）"""
        content = self.chat_input.toPlainText().strip()
        if not content:
            return

        # 检查提供商
        provider = provider_manager.get_active_provider()
        if not provider:
            self.chat_area.append("\n[错误] 请先在'提供商管理'页面配置 AI 提供商")
            return

        if not provider.api_key or provider.api_key.startswith("test"):
            self.chat_area.append(f"\n[错误] 提供商 '{provider.name}' 的 API 密钥无效")
            return

        # 确保有对话 ID
        if not hasattr(self, 'chat_conversation_id') or self.chat_conversation_id is None:
            self._on_new_chat()
            if not hasattr(self, 'chat_conversation_id') or self.chat_conversation_id is None:
                return

        # 显示用户消息
        self.chat_area.append(f"\n[用户]: {content}")

        # 清空输入
        self.chat_input.clear()

        # 禁用输入
        self.chat_input.setEnabled(False)

        # 添加 AI 响应开始标记
        self.chat_area.append("\n[AI]: ")
        # 保存当前位置，用于追加内容
        from PySide6.QtGui import QTextCursor
        cursor = self.chat_area.textCursor()
        cursor.movePosition(QTextCursor.End)
        self.chat_area.setTextCursor(cursor)

        # 使用 Python 标准库的 threading
        import threading
        import queue

        result_queue = queue.Queue()

        def send_in_thread():
            """在线程中发送消息（流式工具调用）"""
            import asyncio
            try:
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)

                async def send_with_tools_stream():
                    # 使用带工具调用的流式方法
                    full_response = ""
                    async for chunk in conversation_service.send_message_with_tools_stream(
                        self.chat_conversation_id, content, self.current_work_dir
                    ):
                        full_response += chunk
                        # 实时发送每个 chunk
                        result_queue.put(("chunk", chunk))
                    # 发送完成信号
                    result_queue.put(("done", full_response))

                loop.run_until_complete(send_with_tools_stream())
                loop.run_until_complete(loop.shutdown_asyncgens())
                loop.close()
            except Exception as e:
                import traceback
                traceback.print_exc()
                result_queue.put(("error", str(e)))

        # 启动线程
        thread = threading.Thread(target=send_in_thread, daemon=True)
        thread.start()

        # 使用 QTimer 定期检查结果
        from PySide6.QtCore import QTimer
        from PySide6.QtGui import QTextCursor

        # 保存流式输出的临时内容
        stream_buffer = []

        def check_result():
            """检查线程结果（在主线程中执行）"""
            try:
                result = result_queue.get_nowait()
                status, data = result

                if status == "chunk":
                    # 实时追加内容（流式模式）
                    stream_buffer.append(data)
                    cursor = self.chat_area.textCursor()
                    cursor.movePosition(QTextCursor.End)
                    self.chat_area.setTextCursor(cursor)
                    # 插入文本（保持滚动在底部）
                    self.chat_area.insertPlainText(data)
                    scrollbar = self.chat_area.verticalScrollBar()
                    scrollbar.setValue(scrollbar.maximum())
                    # 继续检查
                    QTimer.singleShot(10, check_result)
                elif status == "done":
                    # 完成，如果有 Markdown 支持，重新渲染整个响应
                    if self._use_html and stream_buffer:
                        full_response = ''.join(stream_buffer)
                        # 追加格式化的版本
                        self.chat_area.append("\n")
                        # 插入渲染后的 Markdown
                        html_content = format_chat_message(full_response)
                        self.chat_area.insertHtml(html_content)

                    # 确保启用输入框
                    self.chat_input.setEnabled(True)
                    self.chat_input.setFocus()
                elif status == "error":
                    # 错误
                    if "timeout" in str(data).lower() or "timed out" in str(data).lower():
                        self.chat_area.append(f"\n[错误] 请求超时，请检查网络连接或稍后重试")
                    elif "401" in str(data) or "authentication" in str(data).lower():
                        self.chat_area.append(f"\n[错误] API 密钥无效，请在'提供商管理'页面更新")
                    else:
                        self.chat_area.append(f"\n[错误] {str(data)[:300]}")
                    self.chat_input.setEnabled(True)
                    self.chat_input.setFocus()

            except queue.Empty:
                # 还没有结果，继续检查
                QTimer.singleShot(10, check_result)

        # 立即开始检查
        QTimer.singleShot(10, check_result)

    def create_history_page(self):
        """创建历史页面"""
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.addWidget(QLabel("代码修改历史"))

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "文件路径", "时间", "状态"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)

        self.pages["修改历史"] = page
        self.content_stack.addWidget(page)

    def create_bug_page(self):
        """创建 Bug 页面"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # 工具栏
        toolbar = QHBoxLayout()
        new_btn = QPushButton("新建 Bug")
        toolbar.addWidget(new_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Bug 列表
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "标题", "状态", "时间"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)

        self.pages["Bug 追踪"] = page
        self.content_stack.addWidget(page)

    def create_knowledge_page(self):
        """创建知识库页面"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # 搜索栏
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        search_input = QTextEdit()
        search_input.setMaximumHeight(25)
        search_input.setPlaceholderText("输入关键词...")
        search_layout.addWidget(search_input)

        search_btn = QPushButton("搜索")
        search_layout.addWidget(search_btn)

        layout.addLayout(search_layout)

        # 结果列表
        result_list = QListWidget()
        layout.addWidget(result_list)

        self.pages["知识库"] = page
        self.content_stack.addWidget(page)

    def create_provider_page(self):
        """创建提供商管理页面"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # 标题
        layout.addWidget(QLabel("提供商管理"))

        # 提供商列表
        self.provider_list_widget = QListWidget()
        layout.addWidget(QLabel("已配置的提供商:"))
        layout.addWidget(self.provider_list_widget)

        # 加载提供商
        self._load_providers_in_page()

        # 按钮区
        button_layout = QHBoxLayout()

        import_btn = QPushButton("从预设导入")
        import_btn.clicked.connect(self._on_import_provider)
        button_layout.addWidget(import_btn)

        edit_btn = QPushButton("编辑提供商")
        edit_btn.clicked.connect(self._on_edit_provider)
        button_layout.addWidget(edit_btn)

        switch_btn = QPushButton("切换提供商")
        switch_btn.clicked.connect(self._on_switch_provider)
        button_layout.addWidget(switch_btn)

        layout.addLayout(button_layout)

        # 快速更新 API Key 区
        quick_update_layout = QHBoxLayout()
        quick_update_layout.addWidget(QLabel("快速更新 API Key:"))

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("选中提供商后输入新 API 密钥")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        quick_update_layout.addWidget(self.api_key_input)

        update_key_btn = QPushButton("更新")
        update_key_btn.clicked.connect(self._on_quick_update_api_key)
        quick_update_layout.addWidget(update_key_btn)

        layout.addLayout(quick_update_layout)

        # 预设列表
        layout.addWidget(QLabel("可用的预设配置:"))

        preset_list = QListWidget()
        preset_list.setMaximumHeight(150)

        # 按类别分组显示预设
        categories = {}
        if PROVIDER_PRESETS:
            for preset in PROVIDER_PRESETS:
                if preset.category not in categories:
                    categories[preset.category] = []
                categories[preset.category].append(preset)

            for category, presets in categories.items():
                preset_list.addItem(f"--- {category.upper()} ---")
                for preset in presets:
                    preset_list.addItem(f"  {preset.name} ({preset.id})")
        else:
            preset_list.addItem("  (无可用预设)")

        layout.addWidget(preset_list)

        # 说明
        info = QLabel("提示: 点击 '从预设导入' 可以快速配置提供商")
        info.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(info)

        self.pages["提供商管理"] = page
        self.content_stack.addWidget(page)

    def _load_providers_in_page(self):
        """加载提供商列表"""
        try:
            self.provider_list_widget.clear()
            providers = provider_manager.get_providers()
            active = provider_manager.get_active_provider()

            for p in providers:
                is_active = " [活动中]" if active and p.id == active.id else ""
                self.provider_list_widget.addItem(f"{p.name} ({p.id}){is_active}")
        except Exception as e:
            self.provider_list_widget.addItem(f"加载失败: {e}")

    def _on_edit_provider(self):
        """编辑提供商"""
        current = self.provider_list_widget.currentItem()
        if not current:
            QMessageBox.warning(None, "提示", "请先选择要编辑的提供商")
            return

        text = current.text()
        # 解析提供商 ID
        try:
            provider_id = text.split("(")[1].split(")")[0]
        except IndexError:
            QMessageBox.warning(None, "错误", "无法解析提供商 ID")
            return

        providers = provider_manager.get_providers()
        provider = next((p for p in providers if p.id == provider_id), None)

        if provider:
            # 创建编辑对话框
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QFormLayout

            dialog = QDialog()
            dialog.setWindowTitle(f"编辑提供商: {provider.name}")
            dialog.setMinimumWidth(400)
            dialog_layout = QVBoxLayout(dialog)

            # 使用表单布局使界面更整洁
            form_layout = QFormLayout()

            # 名称
            name_edit = QLineEdit(provider.name)
            form_layout.addRow("名称:", name_edit)

            # API 端点（新增）
            endpoint_edit = QLineEdit(provider.api_endpoint)
            endpoint_edit.setPlaceholderText("https://api.example.com (可选)")
            form_layout.addRow("API 端点:", endpoint_edit)

            # 模型
            model_edit = QLineEdit(provider.model)
            form_layout.addRow("模型:", model_edit)

            # API 密钥
            api_key_edit = QLineEdit(provider.api_key)
            api_key_edit.setEchoMode(QLineEdit.Password)
            form_layout.addRow("API 密钥:", api_key_edit)

            # 添加说明
            endpoint_hint = QLabel("💡 提示: API 端点用于中转服务或自定义 API 地址")
            endpoint_hint.setStyleSheet("color: #888; font-size: 10px;")
            dialog_layout.addWidget(endpoint_hint)

            dialog_layout.addLayout(form_layout)

            # 按钮
            buttons = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            dialog_layout.addWidget(buttons)

            if dialog.exec() == QDialog.Accepted:
                # 更新配置
                from src.services.provider_service import ProviderConfig
                updated_config = ProviderConfig(
                    id=provider.id,
                    name=name_edit.text(),
                    provider_type=provider.provider_type,
                    api_key=api_key_edit.text(),
                    api_endpoint=endpoint_edit.text() or provider.api_endpoint,  # 允许为空
                    model=model_edit.text(),
                    temperature=provider.temperature,
                    max_tokens=provider.max_tokens,
                    top_p=provider.top_p,
                    proxy_url=provider.proxy_url,
                    proxy_enabled=provider.proxy_enabled,
                    is_enabled=provider.is_enabled,
                    custom_params=provider.custom_params,
                )

                if provider_manager.update_provider(provider_id, updated_config):
                    QMessageBox.information(
                        None,
                        "成功",
                        f"已更新提供商:\n"
                        f"名称: {updated_config.name}\n"
                        f"端点: {updated_config.api_endpoint or '(默认)'}\n"
                        f"模型: {updated_config.model}"
                    )
                    self._load_providers_in_page()
                else:
                    QMessageBox.warning(None, "失败", "更新提供商失败")

    def _on_quick_update_api_key(self):
        """快速更新 API Key"""
        current = self.provider_list_widget.currentItem()
        if not current:
            QMessageBox.warning(None, "提示", "请先选择要更新 API Key 的提供商")
            return

        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(None, "提示", "请输入新的 API 密码")
            return

        text = current.text()
        try:
            provider_id = text.split("(")[1].split(")")[0]
        except IndexError:
            QMessageBox.warning(None, "错误", "无法解析提供商 ID")
            return

        providers = provider_manager.get_providers()
        provider = next((p for p in providers if p.id == provider_id), None)

        if provider:
            # 更新 API Key
            from src.services.provider_service import ProviderConfig
            updated_config = ProviderConfig(
                id=provider.id,
                name=provider.name,
                provider_type=provider.provider_type,
                api_key=api_key,
                api_endpoint=provider.api_endpoint,
                model=provider.model,
                temperature=provider.temperature,
                max_tokens=provider.max_tokens,
                top_p=provider.top_p,
                proxy_url=provider.proxy_url,
                proxy_enabled=provider.proxy_enabled,
                is_enabled=provider.is_enabled,
                custom_params=provider.custom_params,
            )

            if provider_manager.update_provider(provider_id, updated_config):
                QMessageBox.information(None, "成功", f"已更新 {provider.name} 的 API 密码")
                self.api_key_input.clear()
            else:
                QMessageBox.warning(None, "失败", "更新 API 密码失败")

    def _on_import_provider(self):
        """导入提供商（简化版本）"""
        from PySide6.QtWidgets import QInputDialog, QMessageBox

        # 显示预设选择对话框
        presets = [f"{p.name} ({p.id})" for p in PROVIDER_PRESETS]

        result = QInputDialog.getItem(
            None, "选择预设", "选择一个预设配置:", presets, 0, False
        )

        # result 是一个元组 (ok, selection)
        if result and len(result) == 2:
            ok, selection = result
            if ok and selection and isinstance(selection, str):
                # 解析预设 ID
                try:
                    preset_id = selection.split("(")[1].split(")")[0]
                except IndexError:
                    QMessageBox.warning(None, "错误", "无法解析预设 ID")
                    return

                # 获取 API Key
                api_key_result = QInputDialog.getText(
                    None, "输入 API Key", "请输入 API 密钥:", QLineEdit.Password
                )

                if api_key_result and len(api_key_result) == 2:
                    ok, api_key = api_key_result
                    if ok and api_key:
                        try:
                            config = provider_manager.import_from_preset(preset_id, api_key)
                            if config and provider_manager.add_provider(config):
                                QMessageBox.information(None, "成功", f"已添加提供商: {config.name}")
                            else:
                                QMessageBox.warning(None, "失败", "添加提供商失败")
                        except Exception as e:
                            QMessageBox.critical(None, "错误", f"导入失败: {e}")

    def _on_switch_provider(self):
        """切换提供商（简化版本）"""
        from PySide6.QtWidgets import QInputDialog, QMessageBox

        providers = provider_manager.get_providers()
        if not providers:
            QMessageBox.warning(None, "提示", "没有配置任何提供商")
            return

        provider_names = [f"{p.name} ({p.id})" for p in providers]

        result = QInputDialog.getItem(
            None, "切换提供商", "选择要切换到的提供商:", provider_names, 0, False
        )

        # result 是一个元组 (ok, selection)
        if result and len(result) == 2:
            ok, selection = result
            if ok and selection and isinstance(selection, str):
                try:
                    provider_id = selection.split("(")[1].split(")")[0]
                except IndexError:
                    QMessageBox.warning(None, "错误", "无法解析提供商 ID")
                    return

                try:
                    if provider_manager.switch_provider(provider_id):
                        QMessageBox.information(None, "成功", f"已切换到: {selection}")
                    else:
                        QMessageBox.warning(None, "失败", "切换失败")
                except Exception as e:
                    QMessageBox.critical(None, "错误", f"切换失败: {e}")

    def _on_commit_code(self):
        """提交代码功能 - 支持 Git 和 SVN"""
        try:
            # 检测 VCS 类型
            vcs_type = self._detect_vcs()

            if vcs_type is None:
                QMessageBox.warning(
                    None,
                    "不是版本控制仓库",
                    f"当前目录不是 Git 或 SVN 仓库:\n{self.current_work_dir}\n\n请先初始化版本控制仓库。"
                )
                return

            # 根据 VCS 类型获取文件状态
            if vcs_type == "git":
                modified_files, untracked_files = self._get_git_status()
                vcs_name = "Git"
            else:  # svn
                modified_files, untracked_files = self._get_svn_status()
                vcs_name = "SVN"

            if not modified_files and not untracked_files:
                QMessageBox.information(
                    None,
                    "没有更改",
                    "当前工作目录没有需要提交的更改。"
                )
                return

            # 创建提交对话框
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QCheckBox, QDialogButtonBox, QScrollArea, QWidget

            dialog = QDialog()
            dialog.setWindowTitle(f"提交代码 ({vcs_name})")
            dialog.setMinimumWidth(700)
            dialog.setMinimumHeight(500)
            dialog_layout = QVBoxLayout(dialog)

            # 显示 VCS 类型
            dialog_layout.addWidget(QLabel(f"版本控制系统: {vcs_name}"))

            # 已修改文件
            if modified_files:
                dialog_layout.addWidget(QLabel("已修改的文件:"))
                modified_text = QTextEdit()
                modified_text.setMaximumHeight(100)
                modified_text.setReadOnly(True)
                modified_text.setText('\n'.join(modified_files))
                dialog_layout.addWidget(modified_text)

            # 新增文件（带勾选）
            if untracked_files:
                dialog_layout.addWidget(QLabel("新增文件 (勾选要添加的文件):"))

                # 创建滚动区域
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll.setMaximumHeight(200)

                checkbox_container = QWidget()
                checkbox_layout = QVBoxLayout(checkbox_container)

                self.untracked_checkboxes = []

                for file_path in untracked_files:
                    checkbox = QCheckBox(file_path)
                    checkbox.setChecked(True)  # 默认勾选
                    checkbox_layout.addWidget(checkbox)
                    self.untracked_checkboxes.append(checkbox)

                checkbox_layout.addStretch()
                scroll.setWidget(checkbox_container)
                dialog_layout.addWidget(scroll)

            # 提交消息输入
            dialog_layout.addWidget(QLabel("提交消息:"))
            commit_msg_edit = QTextEdit()
            commit_msg_edit.setMaximumHeight(60)
            commit_msg_edit.setPlaceholderText("输入提交消息，描述本次更改...")
            dialog_layout.addWidget(commit_msg_edit)

            # 推送/更新选项
            push_label = "提交后推送到远程仓库 (Git)" if vcs_type == "git" else "提交前更新代码 (SVN)"
            push_checkbox = QCheckBox(push_label)
            dialog_layout.addWidget(push_checkbox)

            # 自动提交选项
            try:
                cfg = config_service.get_config()
                auto_commit_default = cfg.auto_commit
            except:
                auto_commit_default = True
            auto_commit_checkbox = QCheckBox("记住选择，下次自动提交")
            auto_commit_checkbox.setChecked(auto_commit_default)
            auto_commit_checkbox.setToolTip("勾选后，下次修改代码时会自动提交（可随时在设置中更改）")
            dialog_layout.addWidget(auto_commit_checkbox)

            # 说明文字
            info_label = QLabel("提示: 可在「设置」页面中更改默认行为")
            info_label.setStyleSheet("color: #888; font-size: 9pt;")
            dialog_layout.addWidget(info_label)

            # 按钮
            buttons = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            dialog_layout.addWidget(buttons)

            if dialog.exec() != QDialog.Accepted:
                return

            # 保存自动提交配置
            try:
                config_service.update_app_config(auto_commit=auto_commit_checkbox.isChecked())
            except Exception as e:
                print(f"保存配置失败: {e}")

            commit_msg = commit_msg_edit.text().strip()
            if not commit_msg:
                QMessageBox.warning(None, "提示", "请输入提交消息")
                return

            # 执行提交
            if vcs_type == "git":
                self._commit_git(modified_files, untracked_files, commit_msg, push_checkbox.isChecked())
            else:  # svn
                self._commit_svn(modified_files, untracked_files, commit_msg, push_checkbox.isChecked())

        except FileNotFoundError:
            QMessageBox.warning(
                None,
                "版本控制工具未安装",
                "未找到 Git 或 SVN 命令。\n请安装相应的版本控制工具后再使用此功能。"
            )
        except Exception as e:
            QMessageBox.critical(
                None,
                "操作失败",
                f"提交代码时发生错误:\n{str(e)}"
            )

    def _detect_vcs(self):
        """检测当前目录的版本控制系统类型"""
        # 检查 Git
        git_result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            cwd=str(self.current_work_dir)
        )
        if git_result.returncode == 0:
            return "git"

        # 检查 SVN
        svn_result = subprocess.run(
            ["svn", "info"],
            capture_output=True,
            text=True,
            cwd=str(self.current_work_dir)
        )
        if svn_result.returncode == 0:
            return "svn"

        return None

    def _get_git_status(self):
        """获取 Git 状态"""
        # 获取已修改文件
        status_result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            cwd=str(self.current_work_dir)
        )
        modified_files = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []

        # 获取未跟踪文件
        untracked_result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            cwd=str(self.current_work_dir)
        )
        untracked_files = untracked_result.stdout.strip().split('\n') if untracked_result.stdout.strip() else []

        # 过滤掉空行
        modified_files = [f for f in modified_files if f]
        untracked_files = [f for f in untracked_files if f]

        return modified_files, untracked_files

    def _get_svn_status(self):
        """获取 SVN 状态"""
        status_result = subprocess.run(
            ["svn", "status"],
            capture_output=True,
            text=True,
            cwd=str(self.current_work_dir)
        )

        lines = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []
        modified_files = []
        untracked_files = []

        for line in lines:
            if not line:
                continue
            # SVN status 格式: "M       file.py" 或 "?       newfile.py"
            status = line[0] if line else ''
            file_path = line[8:] if len(line) > 8 else line  # 跳过状态字符和空格

            if status == 'M':  # 已修改
                modified_files.append(file_path)
            elif status == '?':  # 未跟踪
                untracked_files.append(file_path)
            elif status == 'A':  # 已添加（待提交）
                modified_files.append(f"{file_path} (已添加)")

        return modified_files, untracked_files

    def _commit_git(self, modified_files, untracked_files, commit_msg, push_after):
        """执行 Git 提交"""
        # 添加选中新增的文件
        selected_untracked = []
        if hasattr(self, 'untracked_checkboxes'):
            for checkbox in self.untracked_checkboxes:
                if checkbox.isChecked():
                    selected_untracked.append(checkbox.text())

        # 添加已修改的文件
        if modified_files:
            self.chat_area.append(f"\n[系统] 正在添加已修改的文件...")

        if selected_untracked:
            self.chat_area.append(f"[系统] 正在添加 {len(selected_untracked)} 个新增文件...")

        # 执行 git add
        all_files_to_add = modified_files + selected_untracked

        if all_files_to_add:
            # 逐个添加文件
            for file_path in all_files_to_add:
                # 提取文件名（去掉 Git 状态前缀）
                if ' ' in file_path:
                    file_path = file_path.split(' ', 1)[1]

                add_result = subprocess.run(
                    ["git", "add", file_path],
                    capture_output=True,
                    text=True,
                    cwd=str(self.current_work_dir)
                )

                if add_result.returncode != 0:
                    QMessageBox.critical(
                        None,
                        "添加文件失败",
                        f"无法添加文件 {file_path}:\n{add_result.stderr}"
                    )
                    return

        # 执行 git commit
        self.chat_area.append(f"[系统] 正在提交更改...")

        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            capture_output=True,
            text=True,
            cwd=str(self.current_work_dir)
        )

        if commit_result.returncode != 0:
            QMessageBox.critical(
                None,
                "提交失败",
                f"Git commit 失败:\n{commit_result.stderr}"
            )
            return

        self.chat_area.append(f"[系统] 提交成功！")
        self.chat_area.append(f"[系统] 提交消息: {commit_msg}")

        if len(selected_untracked) > 0:
            self.chat_area.append(f"[系统] 包含 {len(selected_untracked)} 个新增文件")

        # 检查是否需要推送
        if push_after:
            self.chat_area.append(f"[系统] 正在推送到远程仓库...")

            push_result = subprocess.run(
                ["git", "push"],
                capture_output=True,
                text=True,
                cwd=str(self.current_work_dir)
            )

            if push_result.returncode != 0:
                self.chat_area.append(f"[系统] 推送失败: {push_result.stderr}")
                QMessageBox.warning(
                    None,
                    "推送失败",
                    f"已提交到本地，但推送失败:\n{push_result.stderr}"
                )
            else:
                self.chat_area.append(f"[系统] 推送成功！")
                QMessageBox.information(
                    None,
                    "提交成功",
                    f"代码已提交并推送到远程仓库\n提交消息: {commit_msg}"
                )
        else:
            QMessageBox.information(
                None,
                "提交成功",
                f"代码已提交到本地仓库\n提交消息: {commit_msg}\n\n你可以稍后手动推送。"
            )

    def _commit_svn(self, modified_files, untracked_files, commit_msg, update_before):
        """执行 SVN 提交"""
        # 添加选中新增的文件
        selected_untracked = []
        if hasattr(self, 'untracked_checkboxes'):
            for checkbox in self.untracked_checkboxes:
                if checkbox.isChecked():
                    selected_untracked.append(checkbox.text())

        # 先更新（如果选择）
        if update_before:
            self.chat_area.append(f"\n[系统] 正在更新代码...")

            update_result = subprocess.run(
                ["svn", "update"],
                capture_output=True,
                text=True,
                cwd=str(self.current_work_dir)
            )

            if update_result.returncode != 0:
                self.chat_area.append(f"[系统] 更新失败: {update_result.stderr}")
                QMessageBox.warning(
                    None,
                    "更新失败",
                    f"更新失败，是否继续提交？\n{update_result.stderr}"
                )
            else:
                self.chat_area.append(f"[系统] 更新完成")

        # 添加新增的文件
        if selected_untracked:
            self.chat_area.append(f"[系统] 正在添加 {len(selected_untracked)} 个新增文件...")

            for file_path in selected_untracked:
                add_result = subprocess.run(
                    ["svn", "add", file_path],
                    capture_output=True,
                    text=True,
                    cwd=str(self.current_work_dir)
                )

                if add_result.returncode != 0:
                    QMessageBox.critical(
                        None,
                        "添加文件失败",
                        f"无法添加文件 {file_path}:\n{add_result.stderr}"
                    )
                    return

        # 执行 svn commit
        self.chat_area.append(f"[系统] 正在提交更改...")

        commit_result = subprocess.run(
            ["svn", "commit", "-m", commit_msg],
            capture_output=True,
            text=True,
            cwd=str(self.current_work_dir)
        )

        if commit_result.returncode != 0:
            QMessageBox.critical(
                None,
                "提交失败",
                f"SVN commit 失败:\n{commit_result.stderr}"
            )
            return

        self.chat_area.append(f"[系统] 提交成功！")
        self.chat_area.append(f"[系统] 提交消息: {commit_msg}")

        if len(selected_untracked) > 0:
            self.chat_area.append(f"[系统] 包含 {len(selected_untracked)} 个新增文件")

        QMessageBox.information(
            None,
            "提交成功",
            f"代码已提交到 SVN 仓库\n提交消息: {commit_msg}"
        )

    def create_settings_page(self):
        """创建设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.addWidget(QLabel("应用设置"))

        # 配置项
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)

        # 深色模式开关
        theme_layout = QHBoxLayout()
        theme_layout.addWidget(QLabel("界面主题:"))

        from PySide6.QtWidgets import QCheckBox
        self.dark_mode_checkbox = QCheckBox("深色模式")
        self.dark_mode_checkbox.setChecked(self._dark_mode)
        self.dark_mode_checkbox.stateChanged.connect(self._toggle_dark_mode)
        theme_layout.addWidget(self.dark_mode_checkbox)
        theme_layout.addStretch()
        config_layout.addLayout(theme_layout)

        # 快捷键提示
        shortcut_hint = QLabel("快捷键: Ctrl+D 切换深色模式")
        shortcut_hint.setStyleSheet("color: #888; font-size: 9pt;")
        config_layout.addWidget(shortcut_hint)

        # 自动提交开关
        auto_commit_layout = QHBoxLayout()
        auto_commit_layout.addWidget(QLabel("代码提交:"))

        self.auto_commit_checkbox = QCheckBox("自动提交代码（修改后自动提交到版本控制）")
        try:
            cfg = config_service.get_config()
            self.auto_commit_checkbox.setChecked(cfg.auto_commit)
        except:
            self.auto_commit_checkbox.setChecked(True)
        self.auto_commit_checkbox.stateChanged.connect(self._toggle_auto_commit)
        auto_commit_layout.addWidget(self.auto_commit_checkbox)
        auto_commit_layout.addStretch()
        config_layout.addLayout(auto_commit_layout)

        # 临时分支开关
        temp_branch_layout = QHBoxLayout()
        temp_branch_layout.addWidget(QLabel("版本控制:"))

        self.temp_branch_checkbox = QCheckBox("提交时创建临时分支")
        try:
            cfg = config_service.get_config()
            self.temp_branch_checkbox.setChecked(cfg.create_temp_branch)
        except:
            self.temp_branch_checkbox.setChecked(True)
        self.temp_branch_checkbox.stateChanged.connect(self._toggle_temp_branch)
        temp_branch_layout.addWidget(self.temp_branch_checkbox)
        temp_branch_layout.addStretch()
        config_layout.addLayout(temp_branch_layout)

        config_layout.addWidget(QLabel("---"))
        config_layout.addWidget(QLabel("AI 配置"))
        try:
            cfg = config_service.get_config()
            config_layout.addWidget(QLabel(f"提供商: {cfg.ai.provider}"))
            config_layout.addWidget(QLabel(f"模型: {cfg.ai.model}"))
            config_layout.addWidget(QLabel(f"温度: {cfg.ai.temperature}"))
        except:
            config_layout.addWidget(QLabel("无法加载配置"))

        config_layout.addStretch()
        layout.addWidget(config_widget)
        layout.addStretch()

        self.pages["设置"] = page
        self.content_stack.addWidget(page)

    def _toggle_dark_mode(self, state):
        """切换深色模式"""
        from PySide6.QtCore import Qt
        is_checked = (state == Qt.Checked.value)
        if is_checked != self._dark_mode:
            self._dark_mode = is_checked
            # 重新应用样式
            setup_app_style(QApplication.instance(), self._dark_mode)

    def _toggle_auto_commit(self, state):
        """切换自动提交选项"""
        from PySide6.QtCore import Qt
        is_checked = (state == Qt.Checked.value)
        config_service.update_app_config(auto_commit=is_checked)

    def _toggle_temp_branch(self, state):
        """切换临时分支选项"""
        from PySide6.QtCore import Qt
        is_checked = (state == Qt.Checked.value)
        config_service.update_app_config(create_temp_branch=is_checked)

    def keyPressEvent(self, event):
        """处理键盘事件"""
        from PySide6.QtGui import QKeySequence
        from PySide6.QtCore import Qt

        # Ctrl+D 切换深色模式
        if event.modifiers() & Qt.ControlModifier and event.key() == Qt.Key_D:
            self._dark_mode = not self._dark_mode
            self.dark_mode_checkbox.setChecked(self._dark_mode)
            setup_app_style(QApplication.instance(), self._dark_mode)
            return

        super().keyPressEvent(event)

    def show_page(self, row):
        """显示指定页面"""
        page_names = list(self.pages.keys())
        if 0 <= row < len(page_names):
            page_name = page_names[row]
            self.content_stack.setCurrentWidget(self.pages[page_name])

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 保存当前对话 ID
        if hasattr(self, 'chat_conversation_id') and self.chat_conversation_id:
            try:
                config_service.update_app_config(last_conversation_id=self.chat_conversation_id)
            except Exception as e:
                print(f"保存对话 ID 失败: {e}")

        # 等待所有活跃线程完成
        for thread in self._active_threads:
            if thread.isRunning():
                thread.quit()
                thread.wait(1000)  # 最多等待 1 秒
        event.accept()


# 创建并显示窗口
app = QApplication(sys.argv)

window = CodeTraceAIWindow()

# 设置应用样式和字体（传递深色模式参数）
setup_app_style(app, window._dark_mode)

window.show()

print("CodeTraceAI GUI 已启动！")

# 运行应用
sys.exit(app.exec())
