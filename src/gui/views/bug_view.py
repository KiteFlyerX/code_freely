"""
Bug 视图
Bug 列表和详情界面（带折叠功能）
使用 BugReport 模型
"""
from typing import Optional, List
from PySide6.QtCore import Qt, Signal, QSize
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QScrollArea, QLabel, QFrame
)
from qfluentwidgets import (
    CardWidget, PushButton, BodyLabel, StrongBodyLabel,
    InfoBar, InfoBarPosition, SearchLineEdit, ToolButton,
    FluentIcon, ScrollArea, TransparentToolButton,
    SubtitleLabel, PillPushButton, ComboBox
)

from ...database.repositories import BugRepository
from ...models import BugReport, BugStatus


class CollapsibleCard(CardWidget):
    """可折叠的卡片"""
    
    def __init__(self, title: str, parent=None):
        super().__init__(parent)
        self._is_expanded = True
        self._setup_ui(title)
    
    def _setup_ui(self, title: str):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 12, 16, 12)
        layout.setSpacing(12)
        
        # 标题栏
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 0)
        
        # 折叠按钮
        self.toggle_btn = TransparentToolButton(FluentIcon.CARET_DOWN)
        self.toggle_btn.setFixedSize(32, 32)
        self.toggle_btn.clicked.connect(self._toggle)
        header_layout.addWidget(self.toggle_btn)
        
        # 标题
        self.title_label = StrongBodyLabel(title)
        header_layout.addWidget(self.title_label)
        
        header_layout.addStretch()
        
        layout.addWidget(header)
        
        # 内容容器
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 0, 0, 0)
        
        layout.addWidget(self.content_widget)
    
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
    
    def add_content(self, widget):
        """添加内容"""
        self.content_layout.addWidget(widget)
    
    def is_expanded(self) -> bool:
        """是否展开"""
        return self._is_expanded
    
    def set_expanded(self, expanded: bool):
        """设置展开状态"""
        if self._is_expanded != expanded:
            self._toggle()


class BugCard(CollapsibleCard):
    """Bug 卡片"""
    
    def __init__(self, bug: BugReport, parent=None):
        title = f"#{bug.id} - {bug.title}"
        super().__init__(title, parent)
        self.bug = bug
        self._setup_content()
    
    def _setup_content(self):
        """设置内容"""
        # 状态
        status_colors = {
            BugStatus.PENDING: "#666666",
            BugStatus.IN_PROGRESS: "#0078d4",
            BugStatus.FIXED: "#107c10",
            BugStatus.CLOSED: "#999999"
        }
        
        status_label = BodyLabel(f"状态: {self._get_status_display()}")
        status_label.setStyleSheet(f"color: {status_colors.get(self.bug.status, '#000')}; font-weight: bold;")
        self.add_content(status_label)
        
        # 描述
        if self.bug.description:
            desc_label = BodyLabel(f"描述: {self.bug.description}")
            desc_label.setWordWrap(True)
            self.add_content(desc_label)
        
        # 错误类型
        if self.bug.error_type:
            error_type_label = BodyLabel(f"错误类型: {self.bug.error_type}")
            error_type_label.setStyleSheet("color: #d13438;")
            self.add_content(error_type_label)
        
        # 修复描述
        if self.bug.fix_description:
            fix_label = BodyLabel(f"修复方案: {self.bug.fix_description}")
            fix_label.setWordWrap(True)
            fix_label.setStyleSheet("color: #107c10;")
            self.add_content(fix_label)
    
    def _get_status_display(self) -> str:
        """获取状态显示文本"""
        status_map = {
            BugStatus.PENDING: "待处理",
            BugStatus.IN_PROGRESS: "进行中",
            BugStatus.FIXED: "已修复",
            BugStatus.CLOSED: "已关闭"
        }
        return status_map.get(self.bug.status, self.bug.status.value)


class BugView(QWidget):
    """
    Bug 视图
    显示 Bug 列表和详情（带折叠功能）
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("bugView")
        
        self.bugs: List[BugReport] = []
        self._setup_ui()
        self._load_bugs()
    
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title = SubtitleLabel("Bug 追踪")
        layout.addWidget(title)
        
        # 工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # Bug 列表区域
        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.bugs_container = QWidget()
        self.bugs_layout = QVBoxLayout(self.bugs_container)
        self.bugs_layout.setAlignment(Qt.AlignTop)
        self.bugs_layout.setSpacing(12)
        
        self.scroll_area.setWidget(self.bugs_container)
        layout.addWidget(self.scroll_area)
    
    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 搜索框
        layout.addWidget(BodyLabel("搜索:"))
        self.search_edit = SearchLineEdit()
        self.search_edit.setPlaceholderText("搜索 Bug...")
        self.search_edit.setFixedWidth(300)
        self.search_edit.textChanged.connect(self._on_search)
        layout.addWidget(self.search_edit)
        
        # 筛选
        layout.addWidget(BodyLabel("状态:"))
        self.status_combo = ComboBox()
        self.status_combo.addItems(["全部", "待处理", "进行中", "已修复", "已关闭"])
        self.status_combo.setCurrentIndex(0)
        self.status_combo.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.status_combo)
        
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
        refresh_btn.clicked.connect(self._load_bugs)
        layout.addWidget(refresh_btn)
        
        return toolbar
    
    def _load_bugs(self):
        """加载 Bug 列表"""
        try:
            from ...database import get_db_session
            with get_db_session() as session:
                repo = BugRepository(session)
                self.bugs = repo.get_all_bugs()
            
            self._refresh_bug_list()
            
            InfoBar.success(
                title="加载成功",
                content=f"已加载 {len(self.bugs)} 个 Bug",
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
    
    def _refresh_bug_list(self):
        """刷新 Bug 列表显示"""
        # 清空现有列表
        while self.bugs_layout.count():
            item = self.bugs_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 获取筛选条件
        search_text = self.search_edit.text().lower()
        status_filter = self.status_combo.currentText()
        
        # 状态映射
        status_map = {
            "待处理": BugStatus.PENDING,
            "进行中": BugStatus.IN_PROGRESS,
            "已修复": BugStatus.FIXED,
            "已关闭": BugStatus.CLOSED
        }
        
        # 筛选并添加 Bug 卡片
        for bug in self.bugs:
            # 应用筛选条件
            if status_filter != "全部":
                filter_status = status_map.get(status_filter)
                if bug.status != filter_status:
                    continue
            
            if search_text:
                match = False
                if search_text in bug.title.lower():
                    match = True
                if bug.description and search_text in bug.description.lower():
                    match = True
                if not match:
                    continue
            
            bug_card = BugCard(bug)
            self.bugs_layout.addWidget(bug_card)
    
    def _on_search(self, text: str):
        """搜索处理"""
        self._refresh_bug_list()
    
    def _on_filter_changed(self):
        """筛选条件改变"""
        self._refresh_bug_list()
    
    def _expand_all(self):
        """展开所有卡片"""
        for i in range(self.bugs_layout.count()):
            item = self.bugs_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, BugCard):
                    widget.set_expanded(True)
    
    def _collapse_all(self):
        """折叠所有卡片"""
        for i in range(self.bugs_layout.count()):
            item = self.bugs_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, BugCard):
                    widget.set_expanded(False)
