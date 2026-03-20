"""
历史记录视图
操作历史界面（带折叠功能）
使用 Conversation 模型作为历史记录存储
"""
from typing import Optional, List
from datetime import datetime
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QLabel, QFrame
)
from qfluentwidgets import (
    CardWidget, PushButton, BodyLabel, StrongBodyLabel,
    InfoBar, InfoBarPosition, SearchLineEdit, ToolButton,
    FluentIcon, ScrollArea, TransparentToolButton,
    SubtitleLabel, ComboBox, DateEdit
)

from ...database.repositories import HistoryRepository
from ...models import Conversation  # 使用 Conversation 模型


class HistoryCard(CardWidget):
    """历史记录卡片"""

    def __init__(self, entry: Conversation, parent=None):
        super().__init__(parent)
        self.entry = entry
        self._is_expanded = False
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)

        # 标题栏
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)

        # 折叠按钮
        self.toggle_btn = TransparentToolButton(FluentIcon.CARET_RIGHT)
        self.toggle_btn.setFixedSize(32, 32)
        self.toggle_btn.clicked.connect(self._toggle)
        header_layout.addWidget(self.toggle_btn)

        # 操作类型（使用标题作为操作类型）
        type_badge = BodyLabel(f"[对话]")
        type_badge.setStyleSheet("color: #0078d4; font-weight: bold;")
        header_layout.addWidget(type_badge)

        # 时间
        time_str = self._format_time(self.entry.updated_at or self.entry.created_at)
        time_label = BodyLabel(time_str)
        time_label.setStyleSheet("color: #666; font-size: 12px;")
        header_layout.addWidget(time_label)

        header_layout.addStretch()

        layout.addWidget(header)

        # 简要信息
        brief_layout = QHBoxLayout()

        # 标题
        title_label = StrongBodyLabel(self.entry.title)
        title_label.setStyleSheet("color: #333;")
        brief_layout.addWidget(title_label)

        brief_layout.addStretch()
        layout.addLayout(brief_layout)

        # 详细内容容器（初始隐藏）
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 8, 0, 0)

        # 项目路径
        if self.entry.project_path:
            path_label = BodyLabel(f"项目: {self.entry.project_path}")
            path_label.setStyleSheet("color: #666; font-size: 11px;")
            self.content_layout.addWidget(path_label)

        # 创建时间
        created_label = BodyLabel(f"创建时间: {self._format_time(self.entry.created_at)}")
        created_label.setStyleSheet("color: #666; font-size: 11px;")
        self.content_layout.addWidget(created_label)

        # 更新时间
        if self.entry.updated_at:
            updated_label = BodyLabel(f"更新时间: {self._format_time(self.entry.updated_at)}")
            updated_label.setStyleSheet("color: #666; font-size: 11px;")
            self.content_layout.addWidget(updated_label)

        self.content_widget.hide()
        layout.addWidget(self.content_widget)

    def _format_time(self, timestamp: datetime) -> str:
        """格式化时间"""
        if timestamp is None:
            return "未知"
        return timestamp.strftime("%Y-%m-%d %H:%M:%S")

    def _shorten_path(self, path: str, max_length: int = 50) -> str:
        """缩短路径显示"""
        if len(path) > max_length:
            return "..." + path[-(max_length-3):]
        return path

    def _toggle(self):
        """切换折叠状态"""
        self._is_expanded = not self._is_expanded

        # 更新按钮图标
        if self._is_expanded:
            self.toggle_btn.setIcon(FluentIcon.CARET_DOWN)
            self.content_widget.show()
        else:
            self.toggle_btn.setIcon(FluentIcon.CARET_RIGHT)
            self.content_widget.hide()

    def is_expanded(self) -> bool:
        """是否展开"""
        return self._is_expanded

    def set_expanded(self, expanded: bool):
        """设置展开状态"""
        if self._is_expanded != expanded:
            self._toggle()


class HistoryView(QWidget):
    """
    历史记录视图
    显示操作历史（带折叠功能）
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("historyView")

        self.entries: List[Conversation] = []
        self._setup_ui()
        self._load_history()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = SubtitleLabel("对话历史")
        layout.addWidget(title)

        # 工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # 统计信息
        stats_card = self._create_stats_card()
        layout.addWidget(stats_card)

        # 历史记录列表
        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)

        self.history_container = QWidget()
        self.history_layout = QVBoxLayout(self.history_container)
        self.history_layout.setAlignment(Qt.AlignTop)
        self.history_layout.setSpacing(12)

        self.scroll_area.setWidget(self.history_container)
        layout.addWidget(self.scroll_area)

    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)

        # 搜索框
        layout.addWidget(BodyLabel("搜索:"))
        self.search_edit = SearchLineEdit()
        self.search_edit.setPlaceholderText("搜索对话标题...")
        self.search_edit.setFixedWidth(300)
        self.search_edit.textChanged.connect(self._on_search)
        layout.addWidget(self.search_edit)

        layout.addStretch()

        # 操作按钮
        expand_all_btn = PushButton("全部展开")
        expand_all_btn.clicked.connect(self._expand_all)
        layout.addWidget(expand_all_btn)

        collapse_all_btn = PushButton("全部折叠")
        collapse_all_btn.clicked.connect(self._collapse_all)
        layout.addWidget(collapse_all_btn)

        refresh_btn = PushButton("刷新")
        refresh_btn.setIcon(FluentIcon.SYNC)
        refresh_btn.clicked.connect(self._load_history)
        layout.addWidget(refresh_btn)

        return toolbar

    def _create_stats_card(self) -> CardWidget:
        """创建统计卡片"""
        card = CardWidget()
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)

        # 统计标签
        self.total_label = BodyLabel("总计: 0 条")
        layout.addWidget(self.total_label)

        layout.addStretch()

        self.today_label = BodyLabel("今日: 0 条")
        layout.addWidget(self.today_label)

        return card

    def _load_history(self):
        """加载历史记录"""
        try:
            from ...database import get_db_session
            with get_db_session() as session:
                repo = HistoryRepository(session)
                self.entries = repo.get_all_entries()

            self._refresh_history()
            self._update_stats()

            InfoBar.success(
                title="加载成功",
                content=f"已加载 {len(self.entries)} 条历史记录",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

        except Exception as e:
            InfoBar.error(
                title="加载失败",
                content=str(e),
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def _refresh_history(self):
        """刷新历史记录显示"""
        # 清空现有列表
        while self.history_layout.count():
            item = self.history_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()

        # 获取筛选条件
        search_text = self.search_edit.text().lower()

        # 筛选并添加历史记录卡片
        for entry in self.entries:
            # 应用筛选条件
            if search_text:
                match = False
                if entry.title and search_text in entry.title.lower():
                    match = True
                if entry.project_path and search_text in entry.project_path.lower():
                    match = True
                if not match:
                    continue

            history_card = HistoryCard(entry)
            self.history_layout.addWidget(history_card)

    def _update_stats(self):
        """更新统计信息"""
        total = len(self.entries)

        # 统计今日记录
        today = datetime.now().date()
        today_count = sum(
            1 for entry in self.entries
            if (entry.updated_at or entry.created_at).date() == today
        )

        self.total_label.setText(f"总计: {total} 条")
        self.today_label.setText(f"今日: {today_count} 条")

    def _on_search(self, text: str):
        """搜索处理"""
        self._refresh_history()

    def _on_filter_changed(self):
        """筛选条件改变"""
        self._refresh_history()

    def _expand_all(self):
        """展开所有卡片"""
        for i in range(self.history_layout.count()):
            item = self.history_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, HistoryCard):
                    widget.set_expanded(True)

    def _collapse_all(self):
        """折叠所有卡片"""
        for i in range(self.history_layout.count()):
            item = self.history_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, HistoryCard):
                    widget.set_expanded(False)
