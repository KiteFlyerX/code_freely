"""
代码审查视图
代码审查界面（带折叠功能）
使用 CodeReview 模型
"""
from typing import Optional, List
from datetime import datetime
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QScrollArea, QLabel, QFrame, QSplitter
)
from qfluentwidgets import (
    CardWidget, PushButton, BodyLabel, StrongBodyLabel,
    InfoBar, InfoBarPosition, SearchLineEdit, ToolButton,
    FluentIcon, ScrollArea, TransparentToolButton,
    SubtitleLabel, ComboBox, TextEdit, SimpleCardWidget,
    PillPushButton, ProgressBar, SwitchButton
)

from ...database.repositories import ReviewRepository
from ...models import CodeReview, ReviewStatus


class ReviewCard(CardWidget):
    """审查记录卡片"""
    
    def __init__(self, review: CodeReview, parent=None):
        super().__init__(parent)
        self.review = review
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
        
        # 状态标签
        status_badge = PillPushButton(self._get_status_display())
        status_badge.setEnabled(False)
        status_badge.setStyleSheet(f"color: {self._get_status_color()}; font-weight: bold;")
        header_layout.addWidget(status_badge)
        
        # 审查者
        reviewer_label = BodyLabel(f"审查者: {self.review.reviewer}")
        header_layout.addWidget(reviewer_label)
        
        header_layout.addStretch()
        
        # 评分
        if self.review.rating is not None:
            rating_text = "⭐" * self.review.rating
            rating_label = BodyLabel(rating_text)
            rating_label.setStyleSheet("color: #ffaa00; font-size: 16px;")
            header_layout.addWidget(rating_label)
        
        layout.addWidget(header)
        
        # 详细内容容器（初始隐藏）
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 8, 0, 0)
        
        # 审查意见
        if self.review.comment:
            comment_card = SimpleCardWidget()
            comment_layout = QVBoxLayout(comment_card)
            comment_layout.setContentsMargins(12, 12, 12, 12)
            
            comment_title = StrongBodyLabel("审查意见:")
            comment_layout.addWidget(comment_title)
            
            comment_text = BodyLabel(self.review.comment)
            comment_text.setWordWrap(True)
            comment_layout.addWidget(comment_text)
            
            self.content_layout.addWidget(comment_card)
        
        # 行评论
        if self.review.line_comments:
            comments_card = SimpleCardWidget()
            comments_card.setStyleSheet("background-color: #f0f7ff;")
            comments_layout = QVBoxLayout(comments_card)
            comments_layout.setContentsMargins(12, 12, 12, 12)
            
            comments_title = StrongBodyLabel("行评论:")
            comments_layout.addWidget(comments_title)
            
            for line_num, comment in self.review.line_comments.items():
                line_label = BodyLabel(f"行 {line_num}: {comment}")
                line_label.setWordWrap(True)
                line_label.setStyleSheet("padding: 4px; margin: 2px 0;")
                comments_layout.addWidget(line_label)
            
            self.content_layout.addWidget(comments_card)
        
        # 时间信息
        time_card = SimpleCardWidget()
        time_layout = QHBoxLayout(time_card)
        time_layout.setContentsMargins(12, 8, 12, 8)
        
        created_label = BodyLabel(f"创建: {self._format_time(self.review.created_at)}")
        created_label.setStyleSheet("color: #666; font-size: 12px;")
        time_layout.addWidget(created_label)
        
        if self.review.reviewed_at:
            reviewed_label = BodyLabel(f"审查: {self._format_time(self.review.reviewed_at)}")
            reviewed_label.setStyleSheet("color: #666; font-size: 12px;")
            time_layout.addWidget(reviewed_label)
        
        time_layout.addStretch()
        self.content_layout.addWidget(time_card)
        
        self.content_widget.hide()
        layout.addWidget(self.content_widget)
    
    def _get_status_display(self) -> str:
        """获取状态显示文本"""
        status_map = {
            ReviewStatus.PENDING: "待审查",
            ReviewStatus.IN_PROGRESS: "审查中",
            ReviewStatus.APPROVED: "已通过",
            ReviewStatus.CHANGES_REQUESTED: "需修改",
            ReviewStatus.COMPLETED: "已完成"
        }
        return status_map.get(self.review.status, self.review.status.value)
    
    def _get_status_color(self) -> str:
        """获取状态颜色"""
        color_map = {
            ReviewStatus.PENDING: "#666666",
            ReviewStatus.IN_PROGRESS: "#0078d4",
            ReviewStatus.APPROVED: "#107c10",
            ReviewStatus.CHANGES_REQUESTED: "#ffaa00",
            ReviewStatus.COMPLETED: "#28a745"
        }
        return color_map.get(self.review.status, "#666")
    
    def _format_time(self, dt: datetime) -> str:
        """格式化时间"""
        return dt.strftime("%Y-%m-%d %H:%M")
    
    def _toggle(self):
        """切换折叠状态"""
        self._is_expanded = not self._is_expanded
        
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


class ReviewView(QWidget):
    """
    代码审查视图
    显示代码审查记录（带折叠功能）
    """
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("reviewView")
        
        self.reviews: List[CodeReview] = []
        self._setup_ui()
        self._load_reviews()
    
    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)
        
        # 标题
        title = SubtitleLabel("代码审查")
        layout.addWidget(title)
        
        # 工具栏
        toolbar = self._create_toolbar()
        layout.addWidget(toolbar)
        
        # 统计信息
        stats_card = self._create_stats_card()
        layout.addWidget(stats_card)
        
        # 审查列表
        self.scroll_area = ScrollArea()
        self.scroll_area.setWidgetResizable(True)
        
        self.reviews_container = QWidget()
        self.reviews_layout = QVBoxLayout(self.reviews_container)
        self.reviews_layout.setAlignment(Qt.AlignTop)
        self.reviews_layout.setSpacing(12)
        
        self.scroll_area.setWidget(self.reviews_container)
        layout.addWidget(self.scroll_area)
    
    def _create_toolbar(self) -> QWidget:
        """创建工具栏"""
        toolbar = QWidget()
        layout = QHBoxLayout(toolbar)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # 搜索框
        layout.addWidget(BodyLabel("搜索:"))
        self.search_edit = SearchLineEdit()
        self.search_edit.setPlaceholderText("搜索审查记录...")
        self.search_edit.setFixedWidth(300)
        self.search_edit.textChanged.connect(self._on_search)
        layout.addWidget(self.search_edit)
        
        # 状态筛选
        layout.addWidget(BodyLabel("状态:"))
        self.status_combo = ComboBox()
        self.status_combo.addItems(["全部", "待审查", "审查中", "已通过", "需修改", "已完成"])
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
        refresh_btn.clicked.connect(self._load_reviews)
        layout.addWidget(refresh_btn)
        
        return toolbar
    
    def _create_stats_card(self) -> CardWidget:
        """创建统计卡片"""
        card = CardWidget()
        layout = QHBoxLayout(card)
        layout.setContentsMargins(16, 12, 16, 12)
        
        # 统计标签
        self.total_reviews_label = BodyLabel("审查: 0 次")
        layout.addWidget(self.total_reviews_label)
        
        self.pending_reviews_label = BodyLabel("待审查: 0")
        self.pending_reviews_label.setStyleSheet("color: #ffaa00;")
        layout.addWidget(self.pending_reviews_label)
        
        self.approved_reviews_label = BodyLabel("已通过: 0")
        self.approved_reviews_label.setStyleSheet("color: #107c10;")
        layout.addWidget(self.approved_reviews_label)
        
        layout.addStretch()
        
        self.avg_rating_label = BodyLabel("平均评分: N/A")
        layout.addWidget(self.avg_rating_label)
        
        return card
    
    def _load_reviews(self):
        """加载审查记录"""
        try:
            from ...database import get_db_session
            with get_db_session() as session:
                repo = ReviewRepository(session)
                self.reviews = repo.get_all_reviews()
            
            self._refresh_reviews()
            self._update_stats()
            
            InfoBar.success(
                title="加载成功",
                content=f"已加载 {len(self.reviews)} 个审查记录",
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
    
    def _refresh_reviews(self):
        """刷新审查列表显示"""
        # 清空现有列表
        while self.reviews_layout.count():
            item = self.reviews_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # 获取筛选条件
        search_text = self.search_edit.text().lower()
        status_filter = self.status_combo.currentText()
        
        # 状态映射
        status_map = {
            "待审查": ReviewStatus.PENDING,
            "审查中": ReviewStatus.IN_PROGRESS,
            "已通过": ReviewStatus.APPROVED,
            "需修改": ReviewStatus.CHANGES_REQUESTED,
            "已完成": ReviewStatus.COMPLETED
        }
        
        # 筛选并添加审查记录
        for review in self.reviews:
            # 应用状态筛选
            if status_filter != "全部":
                filter_status = status_map.get(status_filter)
                if review.status != filter_status:
                    continue
            
            # 应用搜索筛选
            if search_text:
                match = False
                if review.comment and search_text in review.comment.lower():
                    match = True
                if review.reviewer and search_text in review.reviewer.lower():
                    match = True
                if not match:
                    continue
            
            review_card = ReviewCard(review)
            self.reviews_layout.addWidget(review_card)
    
    def _update_stats(self):
        """更新统计信息"""
        total_reviews = len(self.reviews)
        pending_count = sum(1 for r in self.reviews if r.status == ReviewStatus.PENDING)
        approved_count = sum(1 for r in self.reviews if r.status == ReviewStatus.APPROVED)
        
        # 计算平均评分
        ratings = [r.rating for r in self.reviews if r.rating is not None]
        avg_rating = sum(ratings) / len(ratings) if ratings else None
        
        self.total_reviews_label.setText(f"审查: {total_reviews} 次")
        self.pending_reviews_label.setText(f"待审查: {pending_count}")
        self.approved_reviews_label.setText(f"已通过: {approved_count}")
        
        if avg_rating is not None:
            self.avg_rating_label.setText(f"平均评分: {avg_rating:.1f} ⭐")
        else:
            self.avg_rating_label.setText("平均评分: N/A")
    
    def _on_search(self, text: str):
        """搜索处理"""
        self._refresh_reviews()
    
    def _on_filter_changed(self):
        """筛选条件改变"""
        self._refresh_reviews()
    
    def _expand_all(self):
        """展开所有条目"""
        for i in range(self.reviews_layout.count()):
            item = self.reviews_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, ReviewCard):
                    widget.set_expanded(True)
    
    def _collapse_all(self):
        """折叠所有条目"""
        for i in range(self.reviews_layout.count()):
            item = self.reviews_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, ReviewCard):
                    widget.set_expanded(False)
