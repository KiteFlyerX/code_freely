"""
代码审查视图
代码审查界面（带折叠功能）
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
from ...database.models import CodeReview, ReviewIssue, IssueSeverity


class IssueCard(CardWidget):
    """审查问题卡片"""
    
    def __init__(self, issue: ReviewIssue, parent=None):
        super().__init__(parent)
        self.issue = issue
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
        
        # 严重程度标签
        severity_badge = PillPushButton(self.issue.severity.value)
        severity_badge.setEnabled(False)
        
        # 根据严重程度设置颜色
        severity_colors = {
            IssueSeverity.CRITICAL: "#d13438",
            IssueSeverity.HIGH: "#ff6b35",
            IssueSeverity.MEDIUM: "#ffaa00",
            IssueSeverity.LOW: "#0078d4",
            IssueSeverity.INFO: "#60a5fa"
        }
        color = severity_colors.get(self.issue.severity, "#666")
        severity_badge.setStyleSheet(f"color: {color}; font-weight: bold;")
        header_layout.addWidget(severity_badge)
        
        # 问题类型
        type_label = BodyLabel(f"{self.issue.issue_type}")
        type_label.setStyleSheet("font-weight: bold;")
        header_layout.addWidget(type_label)
        
        header_layout.addStretch()
        
        # 位置信息
        if self.issue.line_number:
            location_label = BodyLabel(f"行 {self.issue.line_number}")
            location_label.setStyleSheet("color: #666; font-size: 12px;")
            header_layout.addWidget(location_label)
        
        layout.addWidget(header)
        
        # 问题描述（折叠时显示摘要）
        self.summary_label = BodyLabel(self._get_summary())
        self.summary_label.setWordWrap(True)
        self.summary_label.setStyleSheet("color: #333;")
        layout.addWidget(self.summary_label)
        
        # 详细内容容器（初始隐藏）
        self.content_widget = QWidget()
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setContentsMargins(0, 8, 0, 0)
        
        # 完整描述
        if self.issue.description:
            desc_label = BodyLabel(self.issue.description)
            desc_label.setWordWrap(True)
            desc_label.setStyleSheet("color: #555;")
            self.content_layout.addWidget(desc_label)
        
        # 建议修复
        if self.issue.suggested_fix:
            fix_card = SimpleCardWidget()
            fix_card.setStyleSheet("background-color: #e8f5e9;")
            fix_layout = QVBoxLayout(fix_card)
            fix_layout.setContentsMargins(12, 12, 12, 12)
            
            fix_title = StrongBodyLabel("💡 建议修复:")
            fix_layout.addWidget(fix_title)
            
            fix_text = BodyLabel(self.issue.suggested_fix)
            fix_text.setWordWrap(True)
            fix_layout.addWidget(fix_text)
            
            self.content_layout.addWidget(fix_card)
        
        # 代码片段
        if self.issue.code_snippet:
            code_card = SimpleCardWidget()
            code_layout = QVBoxLayout(code_card)
            code_layout.setContentsMargins(12, 12, 12, 12)
            
            code_title = StrongBodyLabel("代码片段:")
            code_layout.addWidget(code_title)
            
            code_text = TextEdit()
            code_text.setPlainText(self.issue.code_snippet)
            code_text.setReadOnly(True)
            code_text.setMaximumHeight(150)
            code_layout.addWidget(code_text)
            
            self.content_layout.addWidget(code_card)
        
        self.content_widget.hide()
        layout.addWidget(self.content_widget)
    
    def _get_summary(self) -> str:
        """获取摘要"""
        if self.issue.description:
            # 截取前80个字符作为摘要
            desc = self.issue.description
            return desc[:80] + "..." if len(desc) > 80 else desc
        return "无详细描述"
    
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


class ReviewSection(CardWidget):
    """审查条目区域"""
    
    def __init__(self, review: CodeReview, parent=None):
        super().__init__(parent)
        self.review = review
        self._is_expanded = True
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
        self.toggle_btn = TransparentToolButton(FluentIcon.CARET_DOWN)
        self.toggle_btn.setFixedSize(32, 32)
        self.toggle_btn.clicked.connect(self._toggle)
        header_layout.addWidget(self.toggle_btn)
        
        # 文件路径
        file_label = StrongBodyLabel(f"📄 {self.review.file_path}")
        file_label.setStyleSheet("font-size: 14px;")
        header_layout.addWidget(file_label)
        
        header_layout.addStretch()
        
        # 审查时间
        time_str = self.review.review_timestamp.strftime("%Y-%m-%d %H:%M")
        time_label = BodyLabel(time_str)
        time_label.setStyleSheet("color: #666; font-size: 12px;")
        header_layout.addWidget(time_label)
        
        # 总体评分
        if self.review.overall_score is not None:
            score_label = BodyLabel(f"评分: {self.review.overall_score:.1f}")
            score_color = self._get_score_color(self.review.overall_score)
            score_label.setStyleSheet(f"color: {score_color}; font-weight: bold; font-size: 14px;")
            header_layout.addWidget(score_label)
        
        layout.addWidget(header)
        
        # 问题列表容器
        self.issues_container = QWidget()
        self.issues_layout = QVBoxLayout(self.issues_container)
        self.issues_layout.setContentsMargins(0, 0, 0, 0)
        self.issues_layout.setSpacing(8)
        
        # 添加问题卡片
        if self.review.issues:
            for issue in self.review.issues:
                issue_card = IssueCard(issue)
                self.issues_layout.addWidget(issue_card)
        else:
            no_issues_label = BodyLabel("✅ 未发现问题")
            no_issues_label.setStyleSheet("color: green; font-style: italic; padding: 8px;")
            self.issues_layout.addWidget(no_issues_label)
        
        layout.addWidget(self.issues_container)
    
    def _get_score_color(self, score: float) -> str:
        """根据评分获取颜色"""
        if score >= 8:
            return "#28a745"
        elif score >= 6:
            return "#ffaa00"
        else:
            return "#d13438"
    
    def _toggle(self):
        """切换折叠状态"""
        self._is_expanded = not self._is_expanded
        
        # 更新按钮图标
        if self._is_expanded:
            self.toggle_btn.setIcon(FluentIcon.CARET_DOWN)
            self.issues_container.show()
        else:
            self.toggle_btn.setIcon(FluentIcon.CARET_RIGHT)
            self.issues_container.hide()
    
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
    显示代码审查结果（带折叠功能）
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
        self.reviews_layout.setSpacing(16)
        
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
        
        # 严重程度筛选
        layout.addWidget(BodyLabel("严重程度:"))
        self.severity_combo = ComboBox()
        self.severity_combo.addItems(["全部", "严重", "高", "中", "低", "信息"])
        self.severity_combo.setCurrentIndex(0)
        self.severity_combo.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.severity_combo)
        
        # 评分筛选
        layout.addWidget(BodyLabel("最低评分:"))
        self.min_score_combo = ComboBox()
        self.min_score_combo.addItems(["全部", "8.0 (优秀)", "6.0 (良好)", "4.0 (及格)"])
        self.min_score_combo.setCurrentIndex(0)
        self.min_score_combo.currentIndexChanged.connect(self._on_filter_changed)
        layout.addWidget(self.min_score_combo)
        
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
        
        self.total_issues_label = BodyLabel("问题: 0 个")
        layout.addWidget(self.total_issues_label)
        
        layout.addStretch()
        
        self.critical_issues_label = BodyLabel("严重: 0")
        self.critical_issues_label.setStyleSheet("color: #d13438; font-weight: bold;")
        layout.addWidget(self.critical_issues_label)
        
        self.avg_score_label = BodyLabel("平均分: N/A")
        layout.addWidget(self.avg_score_label)
        
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
        severity_filter = self.severity_combo.currentText()
        min_score = self._get_min_score()
        
        # 筛选并添加审查记录
        for review in self.reviews:
            # 应用评分筛选
            if min_score is not None and review.overall_score and review.overall_score < min_score:
                continue
            
            # 应用搜索筛选
            if search_text and search_text not in review.file_path.lower():
                continue
            
            # 应用严重程度筛选（检查是否有该严重程度的问题）
            if severity_filter != "全部":
                has_severity = any(
                    issue.severity.value == severity_filter
                    for issue in review.issues
                )
                if not has_severity:
                    continue
            
            review_section = ReviewSection(review)
            self.reviews_layout.addWidget(review_section)
    
    def _get_min_score(self) -> Optional[float]:
        """获取最低评分筛选"""
        index = self.min_score_combo.currentIndex()
        score_map = {
            1: 8.0,
            2: 6.0,
            3: 4.0
        }
        return score_map.get(index)
    
    def _update_stats(self):
        """更新统计信息"""
        total_reviews = len(self.reviews)
        total_issues = sum(len(review.issues) for review in self.reviews)
        critical_issues = sum(
            sum(1 for issue in review.issues if issue.severity == IssueSeverity.CRITICAL)
            for review in self.reviews
        )
        
        # 计算平均分
        scores = [review.overall_score for review in self.reviews if review.overall_score is not None]
        avg_score = sum(scores) / len(scores) if scores else None
        
        self.total_reviews_label.setText(f"审查: {total_reviews} 次")
        self.total_issues_label.setText(f"问题: {total_issues} 个")
        self.critical_issues_label.setText(f"严重: {critical_issues}")
        
        if avg_score is not None:
            self.avg_score_label.setText(f"平均分: {avg_score:.1f}")
        else:
            self.avg_score_label.setText("平均分: N/A")
    
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
                if isinstance(widget, ReviewSection):
                    widget.set_expanded(True)
    
    def _collapse_all(self):
        """折叠所有条目"""
        for i in range(self.reviews_layout.count()):
            item = self.reviews_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, ReviewSection):
                    widget.set_expanded(False)
