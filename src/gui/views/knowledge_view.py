"""
知识库视图
知识库浏览和搜索界面
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView,
    QTabWidget
)
from qfluentwidgets import (
    PushButton, SearchLineEdit, ComboBox, PrimaryPushButton,
    BodyLabel, StrongBodyLabel, CardWidget, SubtitleLabel,
    TableWidget, InfoBar, InfoBarPosition, ScrollArea,
    SimpleCardWidget, PillPushButton
)
from PySide6.QtWidgets import QDialog, QLabel

from ...services import knowledge_service, KnowledgeCreateInfo


class KnowledgeView(QWidget):
    """知识库视图"""

    entryCreated = Signal(int)  # 条目创建信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_knowledge()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题和工具栏
        header = self._create_header()
        layout.addWidget(header)

        # 标签页
        self.tabs = QTabWidget()
        self.tabs.addTab(self._create_browse_tab(), "浏览")
        self.tabs.addTab(self._create_search_tab(), "搜索")
        self.tabs.addTab(self._create_stats_tab(), "统计")
        layout.addWidget(self.tabs)

    def _create_header(self) -> QWidget:
        """创建头部"""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        title = StrongBodyLabel("知识库")
        layout.addWidget(title)

        layout.addStretch()

        # 新建条目按钮
        create_btn = PrimaryPushButton("新建条目")
        create_btn.clicked.connect(self._create_entry)
        layout.addWidget(create_btn)

        # 刷新按钮
        refresh_btn = PushButton("刷新")
        refresh_btn.clicked.connect(self._load_knowledge)
        layout.addWidget(refresh_btn)

        return header

    def _create_browse_tab(self) -> QWidget:
        """创建浏览标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)

        # 分类选择
        toolbar = QWidget()
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(0, 0, 0, 0)

        toolbar_layout.addWidget(BodyLabel("分类:"))
        self.category_combo = ComboBox()
        self.category_combo.addItems(["全部"] + knowledge_service.get_categories())
        self.category_combo.currentTextChanged.connect(self._on_category_changed)
        toolbar_layout.addWidget(self.category_combo)

        toolbar_layout.addStretch()

        layout.addWidget(toolbar)

        # 条目列表
        self.browse_table = TableWidget()
        self.browse_table.setColumnCount(4)
        self.browse_table.setHorizontalHeaderLabels(["标题", "分类", "访问次数", "创建时间"])
        self.browse_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.browse_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.browse_table.setAlternatingRowColors(True)
        self.browse_table.cellDoubleClicked.connect(self._show_entry_detail)
        layout.addWidget(self.browse_table)

        return tab

    def _create_search_tab(self) -> QWidget:
        """创建搜索标签页"""
        tab = QWidget()
        layout = QVBoxLayout(tab)
        layout.setContentsMargins(0, 0, 0, 0)

        # 搜索栏
        search_bar = QWidget()
        search_layout = QHBoxLayout(search_bar)
        search_layout.setContentsMargins(0, 0, 0, 0)

        self.search_edit = SearchLineEdit()
        self.search_edit.setPlaceholderText("搜索知识库...")
        self.search_edit.textChanged.connect(self._on_search)
        search_layout.addWidget(self.search_edit)

        search_btn = PushButton("搜索")
        search_btn.clicked.connect(self._on_search_button)
        search_layout.addWidget(search_btn)

        layout.addWidget(search_bar)

        # 搜索结果
        self.search_table = TableWidget()
        self.search_table.setColumnCount(4)
        self.search_table.setHorizontalHeaderLabels(["标题", "分类", "匹配度", "操作"])
        self.search_table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.search_table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.search_table.setAlternatingRowColors(True)
        layout.addWidget(self.search_table)

        return tab

    def _create_stats_tab(self) -> QWidget:
        """创建统计标签页"""
        tab = ScrollArea()
        tab.setWidgetResizable(True)

        container = QWidget()
        layout = QVBoxLayout(container)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 统计卡片
        self.stats_cards = []
        for i in range(4):
            card = SimpleCardWidget()
            card_layout = QVBoxLayout(card)
            title = BodyLabel(f"统计 {i+1}")
            value = SubtitleLabel("0")
            card_layout.addWidget(title)
            card_layout.addWidget(value)
            self.stats_cards.append((title, value))
            layout.addWidget(card)

        layout.addStretch()

        tab.setWidget(container)
        return tab

    def _load_knowledge(self):
        """加载知识库"""
        # 加载浏览列表
        category = self.category_combo.currentText()
        if category == "全部":
            category = None

        entries = knowledge_service.get_by_category(category, limit=100)
        self._populate_browse_table(entries)

        # 加载统计
        self._load_statistics()

    def _populate_browse_table(self, entries):
        """填充浏览表格"""
        self.browse_table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            self.browse_table.setItem(row, 0, QTableWidgetItem(entry.title))
            self.browse_table.setItem(row, 1, QTableWidgetItem(entry.category or "-"))
            self.browse_table.setItem(row, 2, QTableWidgetItem(str(entry.access_count)))
            self.browse_table.setItem(row, 3, QTableWidgetItem(
                entry.created_at.strftime("%Y-%m-%d")
            ))

    def _load_statistics(self):
        """加载统计信息"""
        stats = knowledge_service.get_statistics()

        # 更新统计卡片
        labels = [
            ("总条目数", f"{stats.total_entries}"),
            ("最多访问", f"{stats.most_accessed[0].title if stats.most_accessed else '-'}"),
            ("最新条目", f"{stats.recent_entries[0].title if stats.recent_entries else '-'}"),
            ("热门标签", f"{', '.join(t[0] for t in stats.top_tags[:3])}"),
        ]

        for i, (title, value) in enumerate(labels):
            if i < len(self.stats_cards):
                title_widget, value_widget = self.stats_cards[i]
                title_widget.setText(title)
                value_widget.setText(value)

    def _on_category_changed(self):
        """分类变化处理"""
        self._load_knowledge()

    def _on_search(self):
        """搜索处理"""
        keyword = self.search_edit.text()
        if len(keyword) < 2:
            return

        results = knowledge_service.search(keyword, limit=50)
        self._populate_search_table(results, keyword)

    def _on_search_button(self):
        """搜索按钮处理"""
        self._on_search()

    def _populate_search_table(self, entries, keyword: str):
        """填充搜索结果表格"""
        self.search_table.setRowCount(len(entries))

        for row, entry in enumerate(entries):
            # 计算简单的匹配度
            match_score = 0
            if keyword.lower() in entry.title.lower():
                match_score += 50
            if keyword.lower() in entry.content.lower():
                match_score += 30
            if any(keyword.lower() in tag.lower() for tag in entry.tags):
                match_score += 20

            self.search_table.setItem(row, 0, QTableWidgetItem(entry.title))
            self.search_table.setItem(row, 1, QTableWidgetItem(entry.category or "-"))
            self.search_table.setItem(row, 2, QTableWidgetItem(f"{match_score}%"))

            # 查看按钮
            btn = PillPushButton("查看")
            btn.clicked.connect(lambda checked, e=entry: self._show_entry_detail_by_id(e.id))
            self.search_table.setCellWidget(row, 3, btn)

    def _create_entry(self):
        """创建条目"""
        dialog = CreateEntryDialog(self)
        if dialog.exec():
            info = dialog.get_entry_info()
            entry_id = knowledge_service.create_entry(info)
            self.entryCreated.emit(entry_id)
            self._load_knowledge()

            InfoBar.success(
                title="知识条目已创建",
                content=f"条目 ID: {entry_id}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

    def _show_entry_detail(self, row: int, column: int):
        """显示条目详情"""
        entry_id = int(self.browse_table.item(row, 0).data(Qt.UserRole) or 0)
        if entry_id:
            self._show_entry_detail_by_id(entry_id)

    def _show_entry_detail_by_id(self, entry_id: int):
        """通过 ID 显示条目详情"""
        entry = knowledge_service.get_entry(entry_id)
        if entry:
            dialog = EntryDetailDialog(entry, self)
            dialog.exec()


class CreateEntryDialog(QDialog):
    """创建条目对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建知识条目")
        self.setMinimumWidth(450)
        self._setup_content()

    def _setup_content(self):
        """设置内容"""
        from qfluentwidgets import LineEdit, TextEdit, ComboBox, PushButton

        layout = QVBoxLayout(self)

        # 标题
        layout.addWidget(QLabel("标题:"))
        self.title_edit = LineEdit()
        self.title_edit.setPlaceholderText("条目标题...")
        layout.addWidget(self.title_edit)

        # 分类
        layout.addWidget(QLabel("分类:"))
        self.category_combo = ComboBox()
        self.category_combo.addItems(knowledge_service.get_categories())
        layout.addWidget(self.category_combo)

        # 内容
        layout.addWidget(QLabel("内容:"))
        self.content_edit = TextEdit()
        self.content_edit.setPlaceholderText("支持 Markdown 格式...")
        self.content_edit.setMaximumHeight(150)
        layout.addWidget(self.content_edit)

        # 标签
        layout.addWidget(QLabel("标签 (逗号分隔):"))
        self.tags_edit = LineEdit()
        self.tags_edit.setPlaceholderText("python, 最佳实践, 示例...")
        layout.addWidget(self.tags_edit)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_btn = PushButton("创建")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = PushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def get_entry_info(self) -> KnowledgeCreateInfo:
        """获取条目信息"""
        tags = [t.strip() for t in self.tags_edit.text().split(",") if t.strip()]
        return KnowledgeCreateInfo(
            title=self.title_edit.text(),
            content=self.content_edit.toPlainText(),
            category=self.category_combo.currentText(),
            tags=tags,
        )


class EntryDetailDialog(QDialog):
    """条目详情对话框"""

    def __init__(self, entry, parent=None):
        super().__init__(parent)
        self.setWindowTitle(entry.title)
        self.setMinimumWidth(500)
        self.entry = entry
        self._setup_content()

        # 标记为已访问
        knowledge_service.mark_helpful(entry.id)

    def _setup_content(self):
        """设置内容"""
        from qfluentwidgets import TextEdit, PushButton

        layout = QVBoxLayout(self)

        # 分类和标签
        info_text = f"分类: {self.entry.category or '-'}"
        if self.entry.tags:
            info_text += f"  |  标签: {', '.join(self.entry.tags)}"
        info_text += f"  |  访问: {self.entry.access_count} 次"

        layout.addWidget(QLabel(info_text))

        # 内容
        content_display = TextEdit()
        content_display.setPlainText(self.entry.content)
        content_display.setReadOnly(True)
        content_display.setMaximumHeight(300)
        layout.addWidget(content_display)

        # 关闭按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        close_btn = PushButton("关闭")
        close_btn.clicked.connect(self.accept)
        button_layout.addWidget(close_btn)

        layout.addLayout(button_layout)
