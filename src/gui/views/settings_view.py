# -*- coding: utf-8 -*-
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

        # 提供商（使用 LineEdit 允许手动输入）
        grid.addWidget(BodyLabel("提供商:"), 0, 0)
        self.provider_edit = LineEdit()
        self.provider_edit.setPlaceholderText("输入提供商 (如: claude, openai, deepseek)...")
        self.provider_edit.textChanged.connect(self._on_provider_changed)
        grid.addWidget(self.provider_edit, 0, 1)

        # 请求地址（可选）- 设置默认值为 https://silkrelay.com/
        grid.addWidget(BodyLabel("请求地址:"), 1, 0)
        self.base_url_edit = LineEdit()
        self.base_url_edit.setPlaceholderText("自定义 API 地址（可选），如: https://api.example.com/v1")
        self.base_url_edit.setText("https://silkrelay.com/")  # 设置默认值
        grid.addWidget(self.base_url_edit, 1, 1)

        # 模型（使用 LineEdit 允许手动输入）
        grid.addWidget(BodyLabel("模型:"), 2, 0)
        self.model_edit = LineEdit()
        self.model_edit.setPlaceholderText("输入模型名称 (如: claude-3-5-sonnet-20241022)...")
        grid.addWidget(self.model_edit, 2, 1)

        # 常用模型快捷按钮
        model_buttons_layout = QHBoxLayout()
        common_models = [
            ("Claude 3.5 Sonnet", "claude-3-5-sonnet-20241022"),
            ("GPT-4o", "gpt-4o"),
            ("DeepSeek", "deepseek-chat"),
            ("Gemini Pro", "gemini-pro")
        ]
        for btn_text, model_name in common_models:
            btn = PushButton(btn_text)
            btn.clicked.connect(lambda checked, name=model_name: self.model_edit.setText(name))
            model_buttons_layout.addWidget(btn)
        model_buttons_layout.addStretch()
        grid.addLayout(model_buttons_layout, 3, 0, 1, 2)

        # API 密钥
        grid.addWidget(BodyLabel("API 密钥:"), 4, 0)
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

        grid.addWidget(api_key_widget, 4, 1)

        # 温度
        grid.addWidget(BodyLabel("温度:"), 5, 0)
        temperature_widget = QWidget()
        temperature_layout = QVBoxLayout(temperature_widget)
        temperature_layout.setContentsMargins(0, 0, 0, 0)
        temperature_layout.setSpacing(4)

        self.temperature_edit = LineEdit()
        self.temperature_edit.setPlaceholderText("0.0-1.0，默认 0.7")
        self.temperature_edit.setText("0.7")
        temperature_layout.addWidget(self.temperature_edit)

        # 温度说明
        temp_help = BodyLabel("💡 值越高输出越随机创新（0.8-1.0），值越低输出越确定精确（0.0-0.3）")
        temp_help.setStyleSheet("color: gray; font-size: 11px;")
        temperature_layout.addWidget(temp_help)

        grid.addWidget(temperature_widget, 5, 1)

        # 最大 Tokens
        grid.addWidget(BodyLabel("最大 Tokens:"), 6, 0)
        self.max_tokens_edit = LineEdit()
        self.max_tokens_edit.setPlaceholderText("默认 4096")
        self.max_tokens_edit.setText("4096")
        grid.addWidget(self.max_tokens_edit, 6, 1)

        # 常用 Token 快捷按钮
        token_buttons_layout = QHBoxLayout()
        for token_val in ["2048", "4096", "8192", "16384"]:
            btn = PushButton(token_val)
            btn.clicked.connect(lambda checked, val=token_val: self.max_tokens_edit.setText(val))
            token_buttons_layout.addWidget(btn)
        token_buttons_layout.addStretch()
        grid.addLayout(token_buttons_layout, 7, 0, 1, 2)

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

    def _on_provider_changed(self, text):
        """提供商改变时更新"""
        pass

    def _on_toggle_key_visibility(self):
        """切换 API 密钥可见性"""
        if self.show_key_btn.isChecked():
            self.api_key_edit.setEchoMode(LineEdit.Normal)
            self.show_key_btn.setText("隐藏")
        else:
            self.api_key_edit.setEchoMode(LineEdit.Password)
            self.show_key_btn.setText("显示")

    def _validate_api_key(self):
        """验证 API 密钥"""
        provider = self.provider_edit.text().strip()
        api_key = self.api_key_edit.text().strip()
        model = self.model_edit.text().strip()
        base_url = self.base_url_edit.text().strip()

        if not provider:
            InfoBar.warning(
                title="提示",
                content="请输入提供商",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        if not api_key:
            InfoBar.warning(
                title="提示",
                content="请输入 API 密钥",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # 临时保存配置以进行验证
        try:
            temperature = float(self.temperature_edit.text())
        except ValueError:
            temperature = 0.7

        try:
            max_tokens = int(self.max_tokens_edit.text())
        except ValueError:
            max_tokens = 4096

        # 验证 API 密钥
        is_valid, message = conversation_service.validate_api_key(
            provider=provider,
            api_key=api_key,
            model=model,
            base_url=base_url if base_url else None
        )

        if is_valid:
            InfoBar.success(
                title="验证成功",
                content=f"API 密钥有效，已连接到 {provider}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
        else:
            InfoBar.error(
                title="验证失败",
                content=f"API 密钥无效或连接失败: {message}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=5000,
                parent=self
            )

    def _load_config(self):
        """加载配置"""
        cfg = config_service.get_config()

        # AI 配置在 cfg.ai 中
        self.provider_edit.setText(cfg.ai.provider)
        self.model_edit.setText(cfg.ai.model)
        self.api_key_edit.setText(cfg.ai.api_key)
        
        # 如果配置中有 base_url，使用配置的值；否则使用默认值
        if cfg.ai.base_url:
            self.base_url_edit.setText(cfg.ai.base_url)
        # 如果配置为空，保持界面初始化时设置的默认值 https://silkrelay.com/
        
        self.temperature_edit.setText(str(cfg.ai.temperature))
        self.max_tokens_edit.setText(str(cfg.ai.max_tokens))

    def _save_config(self):
        """保存配置"""
        provider = self.provider_edit.text().strip()
        model = self.model_edit.text().strip()
        api_key = self.api_key_edit.text().strip()
        base_url = self.base_url_edit.text().strip()  # 获取请求地址

        if not provider:
            InfoBar.warning(
                title="提示",
                content="请输入提供商",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        if not model:
            InfoBar.warning(
                title="提示",
                content="请输入模型名称",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        if not api_key:
            InfoBar.warning(
                title="提示",
                content="请输入 API 密钥",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # 验证温度和最大 tokens
        try:
            temperature = float(self.temperature_edit.text())
            if not 0.0 <= temperature <= 1.0:
                raise ValueError("温度必须在 0.0-1.0 之间")
        except ValueError as e:
            InfoBar.warning(
                title="提示",
                content=f"温度值无效: {e}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        try:
            max_tokens = int(self.max_tokens_edit.text())
            if max_tokens < 1:
                raise ValueError("最大 tokens 必须大于 0")
        except ValueError as e:
            InfoBar.warning(
                title="提示",
                content=f"最大 tokens 无效: {e}",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        # 保存配置 - 使用 update_ai_config，包含 base_url
        config_service.update_ai_config(
            provider=provider,
            model=model,
            api_key=api_key,
            base_url=base_url,  # 保存请求地址
            temperature=temperature,
            max_tokens=max_tokens
        )

        InfoBar.success(
            title="配置已保存",
            content=f"提供商: {provider}, 模型: {model}" + (f", 地址: {base_url}" if base_url else ""),
            orient=Qt.Horizontal,
            isClosable=True,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )


class SettingsView(QWidget):
    """设置视图 - 使用标签页分离配置"""

    configChanged = Signal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # 标签页
        self.tab_widget = QTabWidget()
        self.tab_widget.setTabPosition(QTabWidget.North)

        # 基本信息标签页
        self.basic_info_view = BasicInfoView()
        self.tab_widget.addTab(self.basic_info_view, "基本信息")

        # AI 配置标签页
        self.ai_config_view = AIConfigView()
        self.tab_widget.addTab(self.ai_config_view, "AI 配置")

        layout.addWidget(self.tab_widget)

        # 连接信号
        self.basic_info_view.restart_application_signal = self.restart_application
        self.ai_config_view.config_changed_signal = self.configChanged

    def restart_application(self):
        """重启应用程序"""
        # 获取主窗口并调用重启方法
        parent = self.parent()
        while parent:
            if hasattr(parent, 'restart_app'):
                parent.restart_app()
                return
            parent = parent.parent()

        # 如果找不到主窗口，使用备用方法
        from PySide6.QtWidgets import QApplication
        app = QApplication.instance()
        app.closeAllWindows()
        app.exit(133)
