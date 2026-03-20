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
from ...database.models import KnowledgeEntry, KnowledgeType


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
        self.title_label = StrongBodyLabel(self.entry.title or "无标题")
        self.title_label.setStyleSheet("font-size: 14px;")
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        # 摘要（折叠时显示）
        self.summary_label = BodyLabel(self._get_summary())
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("color: #666; font-size: 12px;")
        header_layout.addWidget(self.summary_label)
        
        layout.addWidget(header)
        
        # 内容容器（初始隐藏）
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        # 详细内容
        if self.entry.content:
            content_label = BodyLabel(self.entry.content)
            content_label.setWordWrap(True)
            self.content_layout.addWidget(content_label)
        
        # 代码片段
        if self.entry.code_snippet:
            code_card = SimpleCardWidget()
            code_layout = QVBoxLayout(code_card)
            code_layout.setContentsMargins(12, 12, 12, 12)
            
            code_title = StrongBodyLabel("代码片段:")
            code_layout.addWidget(code_title)
            
            code_text = TextEdit()
            code_text.setPlainText(self.entry.code_snippet)
            code_text.setReadOnly(True)
            code_text.setMaximumHeight(150)
            code_layout.addWidget(code_text)
            
            self.content_layout.addWidget(code_card)
        
        # 文件路径
        if self.entry.file_path:
            file_label = BodyLabel(f"📁 {self.entry.file_path}")
            file_label.setStyleSheet("color: #0078d4;")
            self.content_layout.addWidget(file_label)
        
        self.content_widget.hide()
        layout.addWidget(self.content_widget)
    
    def _get_type_label(self) -> str:
        """获取类型标签"""
        type_map = {
            KnowledgeType.CLASS: "类",
            KnowledgeType.FUNCTION: "函数",
            KnowledgeType.MODULE: "模块",
            KnowledgeType.VARIABLE: "变量",
            KnowledgeType.CONCEPT: "概念"
        }
        return type_map.get(self.entry.type, "其他")
    
    def _get_summary(self) -> str:
        """获取摘要"""
        if self.entry.summary:
            return self.entry.summary
        elif self.entry.content:
            # 截取前50个字符作为摘要
            return self.entry.content[:50] + "..." if len(self.entry.content) > 50 else self.entry.content
        return ""
    
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


class KnowledgeView(QWidget):
    """
    知识库视图
    显示代码知识库（带折叠功能）
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("knowledgeView")
        
        self.entries: List[KnowledgeEntry] = []
        self._setup_ui()
        self._load_knowledge()
    
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title = SubtitleLabel("代码知识库")
        layout.addWidget(title)
        
        # 工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # 主内容区域（使用分割器）
        splitter = QSplitter(Qt.Horizontal)
        
        # 左侧：树形结构
        left_panel = self._create_tree_panel()
        splitter.addWidget(left_panel)
        
        # 右侧：详细列表
        right_panel = self._create_list_panel()
        splitter.addWidget(right_panel)
        
        # 设置分割比例
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 2)
        
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
        layout.addWidget(BodyLabel("类型:"))
        self.type_combo = ComboBox()
        self.type_combo.addItems(["全部", "类", "函数", "模块", "变量", "概念"])
        self.type_combo.setCurrentIndex(0)
        self.type_combo.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.type_combo)
        
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
        refresh_btn.clicked.connect(self._load_knowledge)
        layout.addWidget(refresh_btn)
        
        return toolbar
    
    def _create_tree_panel(self) -> QWidget:
        """创建树形结构面板"""
        panel = CardWidget()
        layout = QVBoxLayout(panel)
        
        title = StrongBodyLabel("知识树")
        layout.addWidget(title)
        
        # 树形控件
        self.tree_widget = TreeWidget()
        self.tree_widget.setHeaderLabels(["名称", "类型"])
        self.tree_widget.itemClicked.connect(self._on_tree_item_clicked)
        layout.addWidget(self.tree_widget)
        
        return panel
    
    def _create_list_panel(self) -> QWidget:
        """创建列表面板"""
        panel = QWidget()
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 知识库条目列表
        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.entries_container = QWidget()
        self.entries_layout = QVBoxLayout(self.entries_container)
        self.entries_layout.setAlignment(Qt.AlignTop)
        self.entries_layout.setSpacing(12)
        
        self.scroll_area.setWidget(self.entries_container)
        layout.addWidget(self.scroll_area)
        
        return panel
    
    def _load_knowledge(self):
        """加载知识库"""
        try:
            from ...database import get_db_session
            with get_db_session() as session:
                repo = KnowledgeRepository(session)
                self.entries = repo.get_all_entries()
            
            self._refresh_tree()
            self._refresh_list()
            
            InfoBar.success(
                title="加载成功",
                content=f"已加载 {len(self.entries)} 个知识条目",
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
    
    def _refresh_tree(self):
        """刷新树形结构"""
        self.tree_widget.clear()
        
        # 按文件路径分组
        file_groups = {}
        for entry in self.entries:
            file_path = entry.file_path or "未分类"
            if file_path not in file_groups:
                file_groups[file_path] = []
            file_groups[file_path].append(entry)
        
        # 构建树
        for file_path, entries in file_groups.items():
            file_item = QTreeWidgetItem([file_path, "文件"])
            self.tree_widget.addTopLevelItem(file_item)
            
            for entry in entries:
                entry_item = QTreeWidgetItem([entry.title or "无标题", entry.type.value])
                file_item.addChild(entry_item)
        
        # 展开所有项
        self.tree_widget.expandAll()
    
    def _refresh_list(self):
        """刷新列表显示"""
        # 清空现有列表
        while self.entries_layout.count():
            item = self.entries_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 获取筛选条件
        search_text = self.search_edit.text().lower()
        type_filter = self.type_combo.currentText()
        
        # 筛选并添加条目
        for entry in self.entries:
            # 应用筛选条件
            if type_filter != "全部" and entry.type.value != type_filter:
                continue
            if search_text:
                if entry.title and search_text not in entry.title.lower():
                    if entry.content and search_text not in entry.content.lower():
                        continue
            
            section = CollapsibleSection(entry)
            self.entries_layout.addWidget(section)
    
    def _on_tree_item_clicked(self, item, column):
        """树形项目点击处理"""
        # 可以在这里实现点击树形项目后高亮对应的列表项
        pass
    
    def _on_search(self, text: str):
        """搜索处理"""
        self._refresh_list()
    
    def _on_filter_changed(self):
        """筛选条件改变"""
        self._refresh_list()
    
    def _expand_all(self):
        """展开所有条目"""
        for i in range(self.entries_layout.count()):
            item = self.entries_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, CollapsibleSection):
                    widget.set_expanded(True)
    
    def _collapse_all(self):
        """折叠所有条目"""
        for i in range(self.entries_layout.count()):
            item = self.entries_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, CollapsibleSection):
                    widget.set_expanded(False)
