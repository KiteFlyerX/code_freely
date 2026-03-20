"""
知识库视图
代码知识库界面（带折叠功能）
"""
from typing import Optional, List
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QScrollArea, QLabel, QFrame, QSplitter
)
from qfluentwidgets import (
    CardWidget, PushButton, BodyLabel, StrongBodyLabel,
    InfoBar, InfoBarPosition, SearchLineEdit, ToolButton,
    FluentIcon, ScrollArea, TransparentToolButton,
    SubtitleLabel, PillPushButton, ComboBox, TreeWidget,
    TextEdit, SimpleCardWidget
)

from ...database.repositories import KnowledgeRepository
from ...models import KnowledgeEntry


class CollapsibleSection(CardWidget):
    """可折叠的知识库条目"""
    
    def __init__(self, entry: KnowledgeEntry, parent=None):
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
        
        # 类型标签
        type_badge = PillPushButton(self._get_type_label())
        type_badge.setEnabled(False)
        header_layout.addWidget(type_badge)
        
        # 标题
        title_label = StrongBodyLabel(self.entry.title)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # 内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 内容文本
        content_text = TextEdit()
        content_text.setPlainText(self.entry.content)
        content_text.setReadOnly(True)
        content_text.setFixedHeight(150)
        self.content_layout.addWidget(content_text)
        
        # 标签
        if self.entry.tags:
            tags_label = BodyLabel(f"标签: {self.entry.tags}")
            self.content_layout.addWidget(tags_label)
        
        # 来源信息
        if self.entry.source_type:
            source_label = BodyLabel(f"来源: {self.entry.source_type} #{self.entry.source_id}")
            self.content_layout.addWidget(source_label)
        
        self.content_widget.hide()
        layout.addWidget(self.content_widget)
    
    def _toggle(self):
        """切换折叠状态"""
        self._is_expanded = not self._is_expanded
        
        if self._is_expanded:
            self.toggle_btn.setIcon(FluentIcon.CARET_DOWN)
            self.content_widget.show()
        else:
            self.toggle_btn.setIcon(FluentIcon.CARET_RIGHT)
            self.content_widget.hide()
    
    def _get_type_label(self) -> str:
        """获取类型标签"""
        if self.entry.source_type:
            return self.entry.source_type.upper()
        return "GENERAL"


class KnowledgeView(QWidget):
    """
    知识库视图
    显示和管理知识库条目
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("knowledgeView")
        
        self.entries: List[KnowledgeEntry] = []
        self._setup_ui()
        self._load_entries()
    
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title = SubtitleLabel("知识库")
        layout.addWidget(title)
        
        # 工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # 主内容区域（使用分割器）
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：条目列表
        left_panel = QWidget()
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        
        list_label = StrongBodyLabel("条目列表")
        left_layout.addWidget(list_label)
        
        self.entries_scroll = ScrollArea()
        self.entries_scroll.setWidgetResizable(True)
        
        self.entries_container = QWidget()
        self.entries_layout = QVBoxLayout(self.entries_container)
        self.entries_layout.setAlignment(Qt.AlignTop)
        
        self.entries_scroll.setWidget(self.entries_container)
        left_layout.addWidget(self.entries_scroll)
        
        # 右侧：详细内容
        right_panel = QWidget()
        right_layout = QVBoxLayout(right_panel)
        right_layout.setContentsMargins(0, 0, 0, 0)
        
        detail_label = StrongBodyLabel("详细信息")
        right_layout.addWidget(detail_label)
        
        self.detail_card = SimpleCardWidget()
        detail_layout = QVBoxLayout(self.detail_card)
        
        self.detail_title = SubtitleLabel("选择一个条目")
        detail_layout.addWidget(self.detail_title)
        
        self.detail_content = TextEdit()
        self.detail_content.setReadOnly(True)
        detail_layout.addWidget(self.detail_content)
        
        right_layout.addWidget(self.detail_card)
        
        splitter.addWidget(left_panel)
        splitter.addWidget(right_panel)
        splitter.setStretchFactor(0, 2)
        splitter.setStretchFactor(1, 3)
        
        layout.addWidget(splitter)
    
    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 搜索框
        layout.addWidget(BodyLabel("搜索:"))
        self.search_edit = SearchLineEdit()
        self.search_edit.setPlaceholderText("搜索知识库...")
        self.search_edit.setFixedWidth(300)
        self.search_edit.textChanged.connect(self._on_search)
        layout.addWidget(self.search_edit)
        
        # 类型筛选
        layout.addWidget(BodyLabel("来源:"))
        self.source_combo = ComboBox()
        self.source_combo.addItems(["全部", "bug", "review", "conversation"])
        self.source_combo.setCurrentIndex(0)
        self.source_combo.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.source_combo)
        
        layout.addStretch()
        
        # 刷新按钮
        refresh_btn = PushButton("刷新")
        refresh_btn.setIcon(FluentIcon.SYNC)
        refresh_btn.clicked.connect(self._load_entries)
        layout.addWidget(refresh_btn)
        
        return toolbar
    
    def _load_entries(self):
        """加载知识库条目"""
        try:
            from ...database import get_db_session
            with get_db_session() as session:
                repo = KnowledgeRepository(session)
                self.entries = repo.get_all_entries()
            
            self._refresh_entries_list()
            
            InfoBar.success(
                title="加载成功",
                content=f"已加载 {len(self.entries)} 个条目",
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
    
    def _refresh_entries_list(self):
        """刷新条目列表"""
        # 清空现有列表
        while self.entries_layout.count():
            item = self.entries_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 获取筛选条件
        search_text = self.search_edit.text().lower()
        source_filter = self.source_combo.currentText()
        
        # 筛选并添加条目
        for entry in self.entries:
            # 应用筛选条件
            if source_filter != "全部":
                if entry.source_type != source_filter:
                    continue
            
            if search_text:
                match = False
                if search_text in entry.title.lower():
                    match = True
                if search_text in entry.content.lower():
                    match = True
                if entry.tags and search_text in entry.tags.lower():
                    match = True
                if not match:
                    continue
            
            section = CollapsibleSection(entry)
            self.entries_layout.addWidget(section)
    
    def _on_search(self, text: str):
        """搜索处理"""
        self._refresh_entries_list()
    
    def _on_filter_changed(self):
        """筛选条件改变"""
        self._refresh_entries_list()
