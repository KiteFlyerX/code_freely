"""
设置视图
应用配置界面 - 使用标签页分离基本信息和 AI 配置
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QScrollArea, QFrame, QDialog, QLabel, QTabWidget
)
from qfluentwidgets import (
    PushButton, PrimaryPushButton, LineEdit,
    ComboBox, CheckBox, BodyLabel, StrongBodyLabel,
    SubtitleLabel, CardWidget, SimpleCardWidget,
    InfoBar, InfoBarPosition, FluentIcon,
    MessageBox, PillPushButton, SegmentedWidget
)

from ...services import (
    config_service, conversation_service
)


class BasicInfoView(QWidget):
    """基本信息视图"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_config()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = SubtitleLabel("基本信息")
        layout.addWidget(title)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(16)

        # 应用配置卡片
        app_card = self._create_app_config_card()
        container_layout.addWidget(app_card)

        # 关于卡片
        about_card = self._create_about_card()
        container_layout.addWidget(about_card)

        container_layout.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _create_app_config_card(self) -> CardWidget:
        """创建应用配置卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题
        title = StrongBodyLabel("应用配置")
        layout.addWidget(title)

        # 网格布局
        grid = QGridLayout()
        grid.setSpacing(12)

        # 自动提交
        grid.addWidget(BodyLabel("自动提交:"), 0, 0)
        self.auto_commit_switch = CheckBox()
        grid.addWidget(self.auto_commit_switch, 0, 1)

        # 创建临时分支
        grid.addWidget(BodyLabel("创建临时分支:"), 1, 0)
        self.temp_branch_switch = CheckBox()
        grid.addWidget(self.temp_branch_switch, 1, 1)

        # 主题
        grid.addWidget(BodyLabel("主题:"), 2, 0)
        self.theme_combo = ComboBox()
        self.theme_combo.addItems(["auto", "light", "dark"])
        grid.addWidget(self.theme_combo, 2, 1)

        layout.addLayout(grid)

        return card

    def _create_about_card(self) -> CardWidget:
        """创建关于卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(8)

        # 标题
        title = StrongBodyLabel("关于 CodeTraceAI")
        layout.addWidget(title)

        # 版本信息
        layout.addWidget(BodyLabel("版本: 0.1.0"))
        layout.addWidget(BodyLabel("AI 编程辅助与知识沉淀工具"))

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        save_btn = PrimaryPushButton("保存设置")
        save_btn.clicked.connect(self._save_config)
        button_layout.addWidget(save_btn)

        restart_btn = PushButton("重启应用")
        restart_btn.clicked.connect(self._restart_application)
        button_layout.addWidget(restart_btn)

        layout.addLayout(button_layout)

        return card

    def _load_config(self):
        """加载配置"""
        cfg = config_service.get_config()
        self.auto_commit_switch.setChecked(cfg.auto_commit)
        self.temp_branch_switch.setChecked(cfg.create_temp_branch)
        self.theme_combo.setCurrentText(cfg.theme)

    def _save_config(self):
        """保存配置"""
        config_service.update_app_config(
            auto_commit=self.auto_commit_switch.isChecked(),
            create_temp_branch=self.temp_branch_switch.isChecked(),
            theme=self.theme_combo.currentText(),
        )

        InfoBar.success(
            title="设置已保存",
            content="配置已更新",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def _restart_application(self):
        """重启应用程序"""
        InfoBar.info(
            title="正在重启",
            content="应用即将关闭并重新启动...",
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

        from PySide6.QtCore import QTimer
        QTimer.singleShot(1000, self._perform_restart)

    def _perform_restart(self):
        """执行重启操作"""
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        app.closeAllWindows()
        self._save_config()
        app.exit(133)


class AIConfigView(QWidget):
    """AI 配置视图 - 快速配置"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()
        self._load_config()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = SubtitleLabel("AI 配置")
        layout.addWidget(title)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(16)

        # AI 配置卡片
        ai_card = self._create_ai_config_card()
        container_layout.addWidget(ai_card)

        container_layout.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _create_ai_config_card(self) -> CardWidget:
        """创建 AI 配置卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题
        title = StrongBodyLabel("AI 配置")
        layout.addWidget(title)

        # 说明
        layout.addWidget(BodyLabel("配置 AI 提供商和模型参数"))

        # 网格布局
        grid = QGridLayout()
        grid.setSpacing(12)

        # 提供商
        grid.addWidget(BodyLabel("提供商:"), 0, 0)
        self.provider_combo = ComboBox()
        self.provider_combo.addItems(["claude", "openai", "deepseek"])
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        grid.addWidget(self.provider_combo, 0, 1)

        # 模型
        grid.addWidget(BodyLabel("模型:"), 1, 0)
        self.model_combo = ComboBox()
        self.model_combo.addItems([
            "claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001",
            "gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo",
            "deepseek-chat", "deepseek-coder"
        ])
        grid.addWidget(self.model_combo, 1, 1)

        # API 密钥
        grid.addWidget(BodyLabel("API 密钥:"), 2, 0)
        api_key_widget = QWidget()
        api_key_layout = QHBoxLayout(api_key_widget)
        api_key_layout.setContentsMargins(0, 0, 0, 0)

        self.api_key_edit = LineEdit()
        self.api_key_edit.setPlaceholderText("输入 API 密钥...")
        self.api_key_edit.setEchoMode(LineEdit.Password)
        api_key_layout.addWidget(self.api_key_edit)

        self.show_key_btn = PushButton("显示")
        self.show_key_btn.setCheckable(True)
        self.show_key_btn.clicked.connect(self._on_toggle_key_visibility)
        api_key_layout.addWidget(self.show_key_btn)

        grid.addWidget(api_key_widget, 2, 1)

        # 温度
        grid.addWidget(BodyLabel("温度:"), 3, 0)
        self.temperature_spin = ComboBox()
        self.temperature_spin.addItems(["0.0", "0.3", "0.5", "0.7", "1.0"])
        self.temperature_spin.setCurrentText("0.7")
        grid.addWidget(self.temperature_spin, 3, 1)

        # 最大 Tokens
        grid.addWidget(BodyLabel("最大 Tokens:"), 4, 0)
        self.max_tokens_spin = ComboBox()
        self.max_tokens_spin.addItems(["1024", "2048", "4096", "8192", "16384"])
        self.max_tokens_spin.setCurrentText("4096")
        grid.addWidget(self.max_tokens_spin, 4, 1)

        layout.addLayout(grid)

        # 按钮布局
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        validate_btn = PushButton("验证 API 密钥")
        validate_btn.clicked.connect(self._validate_api_key)
        button_layout.addWidget(validate_btn)

        save_btn = PrimaryPushButton("保存配置")
        save_btn.clicked.connect(self._save_config)
        button_layout.addWidget(save_btn)

        layout.addLayout(button_layout)

        return card

    def _load_config(self):
        """加载配置"""
        cfg = config_service.get_config()

        # AI 配置
        self.provider_combo.setCurrentText(cfg.ai.provider)
        self.model_combo.setCurrentText(cfg.ai.model)
        self.api_key_edit.setText(cfg.ai.api_key)
        self.temperature_spin.setCurrentText(str(cfg.ai.temperature))
        self.max_tokens_spin.setCurrentText(str(cfg.ai.max_tokens))

    def _save_config(self):
        """保存配置"""
        config_service.update_ai_config(
            provider=self.provider_combo.currentText(),
            model=self.model_combo.currentText(),
            api_key=self.api_key_edit.text(),
            temperature=float(self.temperature_spin.currentText()),
            max_tokens=int(self.max_tokens_spin.currentText()),
        )

        InfoBar.success(
            title="设置已保存",
            content="AI 配置已更新",
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

    def _on_provider_changed(self, provider: str):
        """提供商变化处理"""
        self.model_combo.clear()

        if provider == "claude":
            models = ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"]
        elif provider == "openai":
            models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
        else:
            models = ["deepseek-chat", "deepseek-coder", "deepseek-reasoner"]

        self.model_combo.addItems(models)

    def _on_toggle_key_visibility(self, checked: bool):
        """切换密钥可见性"""
        if checked:
            self.api_key_edit.setEchoMode(LineEdit.Normal)
            self.show_key_btn.setText("隐藏")
        else:
            self.api_key_edit.setEchoMode(LineEdit.Password)
            self.show_key_btn.setText("显示")

    def _validate_api_key(self):
        """验证 API 密钥"""
        current_key = self.api_key_edit.text()
        if current_key:
            config_service.save_api_key(
                self.provider_combo.currentText(),
                current_key
            )

        is_valid = conversation_service.validate_api_key()

        if is_valid:
            InfoBar.success(
                title="API 密钥有效",
                content="密钥验证成功",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            InfoBar.error(
                title="API 密钥无效",
                content="请检查密钥是否正确",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )


class SettingsView(QWidget):
    """设置视图 - 使用标签页分离基本信息和 AI 配置"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(16)

        # 标题
        title = SubtitleLabel("设置")
        layout.addWidget(title)

        # 使用 SegmentedWidget 作为标签切换器
        self.segmented_widget = SegmentedWidget()
        self.segmented_widget.addItem("basic", "基本信息")
        self.segmented_widget.addItem("ai", "AI 配置")
        self.segmented_widget.setCurrentItem("basic")
        self.segmented_widget.currentItemChanged.connect(self._on_tab_changed)
        layout.addWidget(self.segmented_widget)

        # 内容区域
        self.content_stack = QTabWidget()
        self.content_stack.setTabBarAutoHide(True)
        self.content_stack.tabBar().hide()  # 隐藏默认的标签栏

        # 创建两个视图
        self.basic_info_view = BasicInfoView()
        self.ai_config_view = AIConfigView()

        self.content_stack.addTab(self.basic_info_view, "基本信息")
        self.content_stack.addTab(self.ai_config_view, "AI 配置")

        # 默认显示第一个标签
        self.content_stack.setCurrentIndex(0)

        layout.addWidget(self.content_stack)

    def _on_tab_changed(self, item_key: str):
        """标签切换处理"""
        if item_key == "basic":
            self.content_stack.setCurrentIndex(0)
        elif item_key == "ai":
            self.content_stack.setCurrentIndex(1)
