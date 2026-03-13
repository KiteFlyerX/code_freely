"""
代码审查视图
代码审查界面
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
    SpinBox
)
from PySide6.QtWidgets import QDialog, QLabel, QTextEdit

from ...services import review_service, ReviewCreateInfo, ReviewSubmitInfo, ReviewStatus


class ReviewView(QWidget):
    """代码审查视图"""

    reviewSubmitted = Signal(int)  # 审查提交信号

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_reviews()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = StrongBodyLabel("代码审查")
        layout.addWidget(title)

        # 工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)

        # 表格
        self.table = TableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "代码修改", "审查者", "状态", "创建时间", "操作"])
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
        self.search_edit.setPlaceholderText("搜索审查...")
        self.search_edit.setFixedWidth(200)
        self.search_edit.textChanged.connect(self._on_search)
        layout.addWidget(self.search_edit)

        # 状态筛选
        layout.addWidget(BodyLabel("状态:"))
        self.status_combo = ComboBox()
        self.status_combo.addItems(["全部", "待审查", "已批准", "需修改", "已合并"])
        self.status_combo.currentTextChanged.connect(self._on_filter_changed)
        layout.addWidget(self.status_combo)

        layout.addStretch()

        # 新建审查按钮
        create_btn = PrimaryPushButton("新建审查")
        create_btn.clicked.connect(self._create_review)
        layout.addWidget(create_btn)

        # 刷新按钮
        refresh_btn = PushButton("刷新")
        refresh_btn.clicked.connect(self._load_reviews)
        layout.addWidget(refresh_btn)

        return toolbar

    def _load_reviews(self):
        """加载审查列表"""
        reviews = review_service.get_pending_reviews(limit=100)
        self._populate_table(reviews)

    def _populate_table(self, reviews):
        """填充表格"""
        self.table.setRowCount(len(reviews))

        for row, review in enumerate(reviews):
            self.table.setItem(row, 0, QTableWidgetItem(str(review.id)))
            self.table.setItem(row, 1, QTableWidgetItem(
                review.file_path or f"修改 #{review.code_change_id}"
            ))
            self.table.setItem(row, 2, QTableWidgetItem(review.reviewer))
            self.table.setItem(row, 3, QTableWidgetItem(self._get_status_label(review.status)))
            self.table.setItem(row, 4, QTableWidgetItem(
                review.created_at.strftime("%Y-%m-%d %H:%M")
            ))

            # 操作按钮
            btn_widget = QWidget()
            btn_layout = QHBoxLayout(btn_widget)
            btn_layout.setContentsMargins(4, 4, 4, 4)

            # 提交审查按钮
            submit_btn = PushButton("审查")
            submit_btn.clicked.connect(lambda checked, r=review.id: self._submit_review(r))
            btn_layout.addWidget(submit_btn)

            self.table.setCellWidget(row, 5, btn_widget)

    def _get_status_label(self, status: ReviewStatus) -> str:
        """获取状态标签"""
        mapping = {
            ReviewStatus.PENDING: "待审查",
            ReviewStatus.APPROVED: "已批准",
            ReviewStatus.CHANGES_REQUESTED: "需修改",
            ReviewStatus.MERGED: "已合并",
        }
        return mapping.get(status, "未知")

    def _create_review(self):
        """创建审查"""
        dialog = CreateReviewDialog(self)
        if dialog.exec():
            info = dialog.get_review_info()
            try:
                review_id = review_service.create_review(info)
                self._load_reviews()

                InfoBar.success(
                    title="审查已创建",
                    content=f"审查 ID: {review_id}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )
            except Exception as e:
                InfoBar.error(
                    title="创建失败",
                    content=str(e),
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=5000,
                    parent=self
                )

    def _submit_review(self, review_id: int):
        """提交审查"""
        dialog = SubmitReviewDialog(review_id, self)
        if dialog.exec():
            info = dialog.get_submit_info()
            if review_service.submit_review(review_id, info):
                self.reviewSubmitted.emit(review_id)
                self._load_reviews()

                InfoBar.success(
                    title="审查已提交",
                    content="",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=2000,
                    parent=self
                )

    def _on_search(self, text: str):
        """搜索处理"""
        reviews = review_service.search_reviews(text, limit=100)
        self._populate_table(reviews)

    def _on_filter_changed(self):
        """筛选变化处理"""
        self._load_reviews()


class CreateReviewDialog(QDialog):
    """创建审查对话框"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("新建审查")
        self.setMinimumWidth(350)
        self._setup_content()

    def _setup_content(self):
        """设置内容"""
        from qfluentwidgets import LineEdit, SpinBox, PushButton

        layout = QVBoxLayout(self)

        # 代码修改 ID
        layout.addWidget(QLabel("代码修改 ID:"))
        self.code_change_spin = SpinBox()
        self.code_change_spin.setMinimum(1)
        self.code_change_spin.setMaximum(999999)
        layout.addWidget(self.code_change_spin)

        # 审查者
        layout.addWidget(QLabel("审查者:"))
        self.reviewer_edit = LineEdit()
        self.reviewer_edit.setPlaceholderText("你的名字...")
        layout.addWidget(self.reviewer_edit)

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

    def get_review_info(self) -> ReviewCreateInfo:
        """获取审查信息"""
        return ReviewCreateInfo(
            code_change_id=self.code_change_spin.value(),
            reviewer=self.reviewer_edit.text(),
        )


class SubmitReviewDialog(QDialog):
    """提交审查对话框"""

    def __init__(self, review_id: int, parent=None):
        super().__init__(parent)
        self.setWindowTitle("提交审查")
        self.setMinimumWidth(400)
        self.review_id = review_id
        self._setup_content()

    def _setup_content(self):
        """设置内容"""
        from qfluentwidgets import TextEdit, ComboBox, SpinBox, PushButton

        layout = QVBoxLayout(self)

        # 状态
        layout.addWidget(QLabel("审查结果:"))
        self.status_combo = ComboBox()
        self.status_combo.addItems(["批准", "请求修改"])
        layout.addWidget(self.status_combo)

        # 评论
        layout.addWidget(QLabel("评论:"))
        self.comment_edit = TextEdit()
        self.comment_edit.setPlaceholderText("审查意见...")
        self.comment_edit.setMaximumHeight(100)
        layout.addWidget(self.comment_edit)

        # 评分
        layout.addWidget(QLabel("评分 (1-5):"))
        self.rating_spin = SpinBox()
        self.rating_spin.setMinimum(1)
        self.rating_spin.setMaximum(5)
        self.rating_spin.setValue(5)
        layout.addWidget(self.rating_spin)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        ok_btn = PushButton("提交")
        ok_btn.clicked.connect(self.accept)
        button_layout.addWidget(ok_btn)

        cancel_btn = PushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        layout.addLayout(button_layout)

    def get_submit_info(self) -> ReviewSubmitInfo:
        """获取提交信息"""
        status = ReviewStatus.APPROVED if self.status_combo.currentText() == "批准" else ReviewStatus.CHANGES_REQUESTED
        return ReviewSubmitInfo(
            status=status,
            comment=self.comment_edit.toPlainText() or None,
            rating=self.rating_spin.value(),
        )
