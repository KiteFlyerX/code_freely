"""
历史视图
代码修改历史界面
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from qfluentwidgets import (
    PushButton, SearchLineEdit, ComboBox,
    BodyLabel, StrongBodyLabel, CardWidget,
    TableWidget, InfoBar, InfoBarPosition
)

from ...services import conversation_service
from ...database.repositories import CodeChangeRepository
from ...database import get_db_session


class HistoryView(QWidget):
    """历史视图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_history()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = StrongBodyLabel("代码修改历史")
        layout.addWidget(title)

        # 工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # 表格
        self.table = TableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "文件路径", "项目", "修改时间", "状态"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)

        # 搜索框
        layout.addWidget(BodyLabel("搜索:"))
        self.search_edit = SearchLineEdit()
        self.search_edit.setPlaceholderText("搜索文件路径...")
        self.search_edit.setFixedWidth(250)
        self.search_edit.textChanged.connect(self._on_search)
        layout.addWidget(self.search_edit)

        # 项目筛选
        layout.addWidget(BodyLabel("项目:"))
        self.project_combo = ComboBox()
        self.project_combo.setMinimumWidth(150)
        self.project_combo.addItem("全部项目")
        layout.addWidget(self.project_combo)

        layout.addStretch()

        # 刷新按钮
        refresh_btn = PushButton("刷新")
        refresh_btn.clicked.connect(self._load_history)
        layout.addWidget(refresh_btn)

        return toolbar

    def _load_history(self):
        """加载历史记录"""
        code_change_repo = CodeChangeRepository(get_db_session())

        # 获取最近100条记录
        changes = code_change_repo.list_by_project(
            project_path=None,
            limit=100
        )

        self._populate_table(changes)

    def _populate_table(self, changes):
        """填充表格"""
        self.table.setRowCount(len(changes))

        for row, change in enumerate(changes):
            self.table.setItem(row, 0, QTableWidgetItem(str(change.id)))
            self.table.setItem(row, 1, QTableWidgetItem(change.file_path))
            self.table.setItem(row, 2, QTableWidgetItem(change.project_path))
            self.table.setItem(row, 3, QTableWidgetItem(
                change.created_at.strftime("%Y-%m-%d %H:%M")
            ))
            self.table.setItem(row, 4, QTableWidgetItem(
                "已应用" if change.is_applied else "未应用"
            ))

    def _on_search(self, text: str):
        """搜索处理"""
        # 根据搜索框内容筛选表格
        for row in range(self.table.rowCount()):
            file_path = self.table.item(row, 1).text()
            match = text.lower() in file_path.lower()
            self.table.setRowHidden(row, not match)
