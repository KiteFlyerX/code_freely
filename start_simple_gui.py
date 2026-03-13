"""
CodeTraceAI GUI - 简化工作版本
基于成功运行的 test_minimal_gui.py 构建
"""
import sys
import os
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
    QHeaderView, QListWidget
)
from PySide6.QtCore import Qt

# 导入服务模块（这些不涉及 Qt）
try:
    from src.database import init_database
    from src.services import config_service, conversation_service
    from src.services.bug_service import bug_service, BugCreateInfo
    from src.services.knowledge_service import knowledge_service, KnowledgeCreateInfo
    init_database()
    print("Services loaded successfully")
except Exception as e:
    print(f"Warning: Some services failed to load: {e}")

# 简化的主窗口
class CodeTraceAIWindow(QMainWindow):
    """简化的主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CodeTraceAI - AI 编程辅助与知识沉淀工具")
        self.setMinimumSize(1000, 700)

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
        self.create_settings_page()

        # 添加到布局
        main_layout.addWidget(nav_list)
        main_layout.addWidget(self.content_stack)

    def create_chat_page(self):
        """创建聊天页面"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # 顶部工具栏
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("AI 对话"))
        toolbar.addStretch()
        new_btn = QPushButton("新建对话")
        toolbar.addWidget(new_btn)
        layout.addLayout(toolbar)

        # 聊天区域
        chat_area = QTextEdit()
        chat_area.setReadOnly(True)
        chat_area.setPlaceholderText("对话记录将显示在这里...")
        layout.addWidget(chat_area)

        # 输入区域
        input_layout = QHBoxLayout()
        input_field = QTextEdit()
        input_field.setMaximumHeight(80)
        input_field.setPlaceholderText("输入你的问题...")
        input_layout.addWidget(input_field)

        send_btn = QPushButton("发送")
        input_layout.addWidget(send_btn)

        layout.addLayout(input_layout)

        self.pages["AI 对话"] = page
        self.content_stack.addWidget(page)

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

    def create_settings_page(self):
        """创建设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.addWidget(QLabel("应用设置"))

        # 配置项
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)

        # AI 配置
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

    def show_page(self, row):
        """显示指定页面"""
        page_names = list(self.pages.keys())
        if 0 <= row < len(page_names):
            page_name = page_names[row]
            self.content_stack.setCurrentWidget(self.pages[page_name])


# 创建并显示窗口
app = QApplication(sys.argv)
window = CodeTraceAIWindow()
window.show()

print("CodeTraceAI GUI 已启动！")

# 运行应用
sys.exit(app.exec())
