"""
Bug 视图
Bug 追踪界面
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget,
    QTableWidgetItem, QHeaderView, QAbstractItemView
)
from qfluentwidgets import (
    PushButton, SearchLineEdit, ComboBox, PrimaryPushButton,
    BodyLabel, StrongBodyLabel, CardWidget,
    TableWidget, InfoBar, InfoBarPosition,
    MessageBox, FluentIcon
)

from ...services import bug_service, BugCreateInfo, BugStatus
from ...models import BugStatus as BugStatusEnum


class BugView(QWidget):
    """Bug 视图"""

    bugCreated = Signal(int)  # Bug 创建信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_bugs()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题和统计
        header = self._create_header()
        layout.addWidget(header)

        # 工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # 表格
        self.table = TableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "标题", "状态", "错误类型", "创建时间", "操作"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.setAlternatingRowColors(True)
        layout.addWidget(self.table)

    def _create_header(self) -> QWidget:
        """创建头部"""
        header = QWidget()
        layout = QHBoxLayout(header)
        layout.setContentsMargins(0, 0, 0, 0)

        title = StrongBodyLabel("Bug 追踪")
        layout.addWidget(title)

        layout.addStretch()

        # 统计标签
        self.stats_label = BodyLabel("总计: 0")
        layout.addWidget(self.stats_label)

        return header

    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)

        # 搜索框
        layout.addWidget(BodyLabel("搜索:"))
        self.search_edit = SearchLineEdit()
        self.search_edit.setPlaceholderText("搜索 Bug...")
        self.search_edit.setFixedWidth(200)
        self.search_edit.textChanged.connect(self._on_search)
        layout.addWidget(self.search_edit)

        # 状态筛选
        layout.addWidget(BodyLabel("状态:"))
        self.status_combo = ComboBox()
        self.status_combo.addItems(["全部", "待处理", "处理中", "已修复", "已关闭"])
        self.status_combo.currentTextChanged.connect(self._on_filter_changed)
        layout.addWidget(self.status_combo)

        layout.addStretch()

        # 新建 Bug 按钮
        create_btn = PrimaryPushButton("新建 Bug")
        create_btn.clicked.connect(self._create_bug)
        layout.addWidget(create_btn)

        # 刷新按钮
        refresh_btn = PushButton("刷新")
        refresh_btn.clicked.connect(self._load_bugs)
        layout.addWidget(refresh_btn)

        return toolbar

    def _load_bugs(self):
        """加载 Bug 列表"""
        # 获取筛选状态
        status_text = self.status_combo.currentText()
        status = self._get_status_filter(status_text)

        # 获取 Bug 列表
        bugs = bug_service.list_bugs(status=status, limit=100)

        self._populate_table(bugs)
        self._update_stats(bugs)

    def _populate_table(self, bugs):
        """填充表格"""
        self.table.setRowCount(len(bugs))

        for row, bug in enumerate(bugs):
            self.table.setItem(row, 0, QTableWidgetItem(str(bug.id)))
            self.table.setItem(row, 1, QTableWidgetItem(bug.title))
            self.table.setItem(row, 2, QTableWidgetItem(self._get_status_label(bug.status)))
            self.table.setItem(row, 3, QTableWidgetItem(bug.error_type or "-"))
            self.table.setItem(row, 4, QTableWidgetItem(
                bug.created_at.strftime("%Y-%m-%d %H:%M")
            ))

            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)

            # 标记修复按钮
            fix_btn = PushButton("修复")
            fix_btn.clicked.connect(lambda checked, b=bug.id: self._mark_fixed(b))
            btn_layout.addWidget(fix_btn)

            self.table.setCellWidget(row, 5, btn_widget)

    def _get_status_filter(self, text: str):
        """获取状态过滤器"""
        mapping = {
            "全部": None,
            "待处理": BugStatus.PENDING,
            "处理中": BugStatus.IN_PROGRESS,
            "已修复": BugStatus.FIXED,
            "已关闭": BugStatus.CLOSED,
        }
        return mapping.get(text)

    def _get_status_label(self, status: BugStatus) -> str:
        """获取状态标签"""
        mapping = {
            BugStatus.PENDING: "待处理",
            BugStatus.IN_PROGRESS: "处理中",
            BugStatus.FIXED: "已修复",
            BugStatus.CLOSED: "已关闭",
        }
        return mapping.get(status, "未知")

    def _update_stats(self, bugs):
        """更新统计"""
        self.stats_label.setText(f"总计: {len(bugs)}")

    def _create_bug(self):
        """创建 Bug"""
        dialog = CreateBugDialog(self)
        if dialog.exec():
            info = dialog.get_bug_info()
            bug_id = bug_service.create_bug(info)
            self.bugCreated.emit(bug_id)
            self._load_bugs()

            InfoBar.success(
                title="Bug 已创建",
                content=f"Bug ID: {bug_id}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

    def _mark_fixed(self, bug_id: int):
        """标记为已修复"""
        if bug_service.mark_fixed(bug_id):
            self._load_bugs()
            InfoBar.success(
                title="Bug 已标记为修复",
                content="",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )

    def _on_search(self, text: str):
        """搜索处理"""
        bugs = bug_service.search_bugs(text, limit=100)
        self._populate_table(bugs)

    def _on_filter_changed(self):
        """筛选变化处理"""
        self._load_bugs()


class CreateBugDialog(MessageBox):
    """创建 Bug 对话框"""

    def __init__(self, parent=None):
        super().__init__("新建 Bug", "", parent)
        self._setup_content()

    def _setup_content(self):
        """设置内容"""
        from qfluentwidgets import LineEdit, TextEdit

        content_widget = QWidget()
        layout = QVBoxLayout(content_widget)

        # 标题
        layout.addWidget(BodyLabel("标题:"))
        self.title_edit = LineEdit()
        self.title_edit.setPlaceholderText("Bug 标题...")
        layout.addWidget(self.title_edit)

        # 描述
        layout.addWidget(BodyLabel("描述:"))
        self.description_edit = TextEdit()
        self.description_edit.setPlaceholderText("详细描述...")
        self.description_edit.setMaximumHeight(100)
        layout.addWidget(self.description_edit)

        # 错误类型
        layout.addWidget(BodyLabel("错误类型:"))
        self.error_type_edit = LineEdit()
        self.error_type_edit.setPlaceholderText("如: ValueError, TypeError...")
        layout.addWidget(self.error_type_edit)

        self.contentLayout.addWidget(content_widget)

    def get_bug_info(self) -> BugCreateInfo:
        """获取 Bug 信息"""
        return BugCreateInfo(
            title=self.title_edit.text(),
            description=self.description_edit.toPlainText(),
            error_type=self.error_type_edit.text(),
        )
