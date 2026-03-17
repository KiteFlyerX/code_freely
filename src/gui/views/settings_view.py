"""
设置视图
应用配置界面
"""
from PySide6.QtCore import Qt, Signal
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGridLayout,
    QScrollArea, QFrame, QListWidget, QListWidgetItem,
    QDialog, QLabel
)
from qfluentwidgets import (
    PushButton, PrimaryPushButton, LineEdit,
    ComboBox, CheckBox, BodyLabel, StrongBodyLabel,
    SubtitleLabel, CardWidget, SimpleCardWidget,
    InfoBar, InfoBarPosition, FluentIcon,
    MessageBox
)

from ...services import (
    config_service, conversation_service,
    provider_manager, PROVIDER_PRESETS,
    ProviderConfig, ProviderType
)
from ...services.provider_service import ProviderPreset
from ...database import init_database


class ProviderConfigDialog(QDialog):
    """提供商配置对话框 - 使用标准 QDialog 避免 qfluentwidgets API 兼容问题"""

    def __init__(self, preset: ProviderPreset = None, parent=None):
        super().__init__(parent)
        self.preset = preset
        self._is_edit_mode = False  # 标记是否为编辑模式
        self._setup_ui()
        self._load_preset()

    def _setup_ui(self):
        """设置界面"""
        self.setWindowTitle("配置提供商")
        self.setMinimumWidth(600)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 网格布局
        grid = QGridLayout()
        grid.setSpacing(12)

        # 名称
        grid.addWidget(BodyLabel("名称:"), 0, 0)
        self.name_edit = LineEdit()
        self.name_edit.setPlaceholderText("提供商名称")
        grid.addWidget(self.name_edit, 0, 1)

        # ID (编辑时禁用)
        grid.addWidget(BodyLabel("ID:"), 1, 0)
        self.id_edit = LineEdit()
        self.id_edit.setPlaceholderText("唯一标识符")
        self.id_edit.setEnabled(False)  # ID 不允许修改
        grid.addWidget(self.id_edit, 1, 1)

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

        # 端点
        grid.addWidget(BodyLabel("API 端点:"), 3, 0)
        self.endpoint_edit = LineEdit()
        self.endpoint_edit.setPlaceholderText("https://api.example.com (可选，留空使用默认)")
        grid.addWidget(self.endpoint_edit, 3, 1)

        # 添加提示标签
        endpoint_hint = BodyLabel("自定义 API 请求地址（用于中转服务）")
        endpoint_hint.setStyleSheet("color: #888; font-size: 10px;")
        grid.addWidget(endpoint_hint, 4, 1)

        # 模型
        grid.addWidget(BodyLabel("模型:"), 5, 0)
        self.model_edit = LineEdit()
        self.model_edit.setPlaceholderText("模型名称")
        grid.addWidget(self.model_edit, 5, 1)

        # 温度
        grid.addWidget(BodyLabel("温度:"), 6, 0)
        self.temp_combo = ComboBox()
        self.temp_combo.addItems(["0.0", "0.3", "0.5", "0.7", "1.0"])
        self.temp_combo.setCurrentText("0.7")
        grid.addWidget(self.temp_combo, 6, 1)

        # 最大 Tokens
        grid.addWidget(BodyLabel("最大 Tokens:"), 7, 0)
        self.max_tokens_combo = ComboBox()
        self.max_tokens_combo.addItems(["1024", "2048", "4096", "8192", "16384"])
        self.max_tokens_combo.setCurrentText("4096")
        grid.addWidget(self.max_tokens_combo, 7, 1)

        layout.addLayout(grid)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = PushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        self.save_btn = PrimaryPushButton("保存")
        self.save_btn.clicked.connect(self._on_save)
        button_layout.addWidget(self.save_btn)

        layout.addLayout(button_layout)

    def _load_preset(self):
        """加载预设配置"""
        if self.preset:
            self.name_edit.setText(self.preset.name)
            self.id_edit.setText(self.preset.id)
            self.endpoint_edit.setText(self.preset.config.api_endpoint)
            self.model_edit.setText(self.preset.config.model)
            self.temp_combo.setCurrentText(str(self.preset.config.temperature))
            self.max_tokens_combo.setCurrentText(str(self.preset.config.max_tokens))

    def set_config(self, config: ProviderConfig):
        """设置现有配置（编辑模式）"""
        self._is_edit_mode = True
        self.name_edit.setText(config.name)
        self.id_edit.setText(config.id)
        self.api_key_edit.setText(config.api_key)
        self.endpoint_edit.setText(config.api_endpoint)
        self.model_edit.setText(config.model)
        self.temp_combo.setCurrentText(str(config.temperature))
        self.max_tokens_combo.setCurrentText(str(config.max_tokens))

        # 编辑模式下提示 ID 不可修改
        self.setWindowTitle("编辑提供商配置")

    def _on_toggle_key_visibility(self, checked: bool):
        """切换密钥可见性"""
        if checked:
            self.api_key_edit.setEchoMode(LineEdit.Normal)
            self.show_key_btn.setText("隐藏")
        else:
            self.api_key_edit.setEchoMode(LineEdit.Password)
            self.show_key_btn.setText("显示")

    def _on_save(self):
        """保存配置"""
        if not self.name_edit.text():
            InfoBar.error(
                title="错误",
                content="请输入提供商名称",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        if not self.id_edit.text():
            InfoBar.error(
                title="错误",
                content="请输入提供商 ID",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        if not self.api_key_edit.text():
            InfoBar.error(
                title="错误",
                content="请输入 API 密钥",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        if not self.model_edit.text():
            InfoBar.error(
                title="错误",
                content="请输入模型名称",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            return

        self.accept()

    def get_config(self) -> ProviderConfig:
        """获取配置"""
        return ProviderConfig(
            id=self.id_edit.text(),
            name=self.name_edit.text(),
            provider_type=self.preset.config.provider_type if self.preset else ProviderType.CUSTOM,
            api_key=self.api_key_edit.text(),
            api_endpoint=self.endpoint_edit.text(),
            model=self.model_edit.text(),
            temperature=float(self.temp_combo.currentText()),
            max_tokens=int(self.max_tokens_combo.currentText()),
        )


class PresetImportDialog(QDialog):
    """预设导入对话框 - 使用标准 QDialog 避免 qfluentwidgets API 兼容问题"""

    preset_selected = Signal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("从预设导入")
        self.setMinimumWidth(500)
        self._setup_ui()

    def _setup_ui(self):
        """设置界面"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(12)

        # 说明
        layout.addWidget(BodyLabel("选择一个预设配置，然后点击导入"))

        # 预设列表
        self.preset_list = QListWidget()
        self._load_presets()
        layout.addWidget(self.preset_list)

        # 按钮
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        cancel_btn = PushButton("取消")
        cancel_btn.clicked.connect(self.reject)
        button_layout.addWidget(cancel_btn)

        import_btn = PrimaryPushButton("导入")
        import_btn.clicked.connect(self._on_import)
        button_layout.addWidget(import_btn)

        layout.addLayout(button_layout)

    def _load_presets(self):
        """加载预设列表"""
        # 按类别分组
        categories = {}
        for preset in PROVIDER_PRESETS:
            if preset.category not in categories:
                categories[preset.category] = []
            categories[preset.category].append(preset)

        # 添加到列表
        for category, presets in categories.items():
            # 添加类别标题
            category_item = QListWidgetItem(f"--- {category.upper()} ---")
            category_item.setFlags(Qt.NoItemFlags)
            self.preset_list.addItem(category_item)

            # 添加预设
            for preset in presets:
                item = QListWidgetItem(f"{preset.name} ({preset.id})")
                item.setData(Qt.UserRole, preset.id)
                self.preset_list.addItem(item)

    def _on_import(self):
        """导入预设"""
        current = self.preset_list.currentItem()
        if current and current.data(Qt.UserRole):
            preset_id = current.data(Qt.UserRole)
            self.preset_selected.emit(preset_id)
            self.accept()


class SettingsView(QWidget):
    """设置视图"""

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
        title = SubtitleLabel("设置")
        layout.addWidget(title)

        # 滚动区域
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setFrameShape(QFrame.NoFrame)

        container = QWidget()
        container_layout = QVBoxLayout(container)
        container_layout.setSpacing(16)

        # 提供商管理卡片
        provider_card = self._create_provider_card()
        container_layout.addWidget(provider_card)

        # AI 配置卡片
        ai_card = self._create_ai_config_card()
        container_layout.addWidget(ai_card)

        # 应用配置卡片
        app_card = self._create_app_config_card()
        container_layout.addWidget(app_card)

        # 关于卡片
        about_card = self._create_about_card()
        container_layout.addWidget(about_card)

        container_layout.addStretch()

        scroll.setWidget(container)
        layout.addWidget(scroll)

    def _create_provider_card(self) -> CardWidget:
        """创建提供商管理卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题和操作按钮
        title_layout = QHBoxLayout()
        title = StrongBodyLabel("提供商管理")
        title_layout.addWidget(title)
        title_layout.addStretch()

        # 操作按钮
        import_btn = PushButton("从预设导入")
        import_btn.clicked.connect(self._on_import_preset)
        title_layout.addWidget(import_btn)

        add_btn = PushButton("手动添加")
        add_btn.clicked.connect(self._on_add_provider)
        title_layout.addWidget(add_btn)

        export_btn = PushButton("导出配置")
        export_btn.clicked.connect(self._on_export)
        title_layout.addWidget(export_btn)

        layout.addLayout(title_layout)

        # 提供商列表
        self.provider_list = QListWidget()
        self.provider_list.itemDoubleClicked.connect(self._on_provider_double_clicked)
        self.provider_list.itemClicked.connect(self._on_provider_selected)
        layout.addWidget(self.provider_list)

        # 提供商详情
        detail_layout = QHBoxLayout()

        self.detail_info = BodyLabel("请从上方列表选择一个提供商")
        detail_layout.addWidget(self.detail_info)
        detail_layout.addStretch()

        # 操作按钮
        self.switch_btn = PrimaryPushButton("设为活动")
        self.switch_btn.clicked.connect(self._on_switch_provider)
        self.switch_btn.setEnabled(False)
        detail_layout.addWidget(self.switch_btn)

        self.edit_btn = PushButton("编辑")
        self.edit_btn.clicked.connect(self._on_edit_provider)
        self.edit_btn.setEnabled(False)
        detail_layout.addWidget(self.edit_btn)

        self.delete_btn = PushButton("删除")
        self.delete_btn.clicked.connect(self._on_delete_provider)
        self.delete_btn.setEnabled(False)
        detail_layout.addWidget(self.delete_btn)

        layout.addLayout(detail_layout)

        return card

    def _create_ai_config_card(self) -> CardWidget:
        """创建 AI 配置卡片"""
        card = CardWidget()
        layout = QVBoxLayout(card)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # 标题
        title = StrongBodyLabel("快速 AI 配置")
        layout.addWidget(title)

        # 说明
        layout.addWidget(BodyLabel("注意：此处的配置仅用于快速测试，建议使用上方的提供商管理功能"))

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
        self.max_tokens_spin.addItems(["1024", "2048", "4096", "8192"])
        self.max_tokens_spin.setCurrentText("4096")
        grid.addWidget(self.max_tokens_spin, 4, 1)

        layout.addLayout(grid)

        # 验证按钮
        validate_btn = PushButton("验证 API 密钥")
        validate_btn.clicked.connect(self._validate_api_key)
        layout.addWidget(validate_btn)

        return card

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

        # 添加重启按钮
        restart_btn = PushButton("重启应用")
        restart_btn.clicked.connect(self._restart_application)
        button_layout.addWidget(restart_btn)

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

        # 应用配置
        self.auto_commit_switch.setChecked(cfg.auto_commit)
        self.temp_branch_switch.setChecked(cfg.create_temp_branch)
        self.theme_combo.setCurrentText(cfg.theme)

        # 加载提供商列表
        self._load_providers()

    def _load_providers(self):
        """加载提供商列表"""
        try:
            init_database()
        except Exception as e:
            print(f"数据库初始化警告: {e}")

        self.provider_list.clear()

        try:
            providers = provider_manager.get_providers()
            active = provider_manager.get_active_provider()

            for provider in providers:
                is_active = " [活动中]" if active and provider.id == active.id else ""
                item = QListWidgetItem(f"{provider.name} ({provider.id}){is_active}")
                item.setData(Qt.UserRole, provider.id)
                self.provider_list.addItem(item)
        except Exception as e:
            print(f"加载提供商失败: {e}")

    def _save_config(self):
        """保存配置"""
        # AI 配置
        config_service.update_ai_config(
            provider=self.provider_combo.currentText(),
            model=self.model_combo.currentText(),
            api_key=self.api_key_edit.text(),
            temperature=float(self.temperature_spin.currentText()),
            max_tokens=int(self.max_tokens_spin.currentText()),
        )

        # 应用配置
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
        from PySide6.QtWidgets import QApplication
        import sys

        # 显示提示信息
        InfoBar.info(
            title="正在重启",
            content="应用即将关闭并重新启动...",
            orient=Qt.Horizontal,
            isClosable=False,
            position=InfoBarPosition.TOP,
            duration=2000,
            parent=self
        )

        # 延迟执行重启，让提示信息显示出来
        from PySide6.QtCore import QTimer
        QTimer.singleShot(1000, self._perform_restart)

    def _perform_restart(self):
        """执行重启操作"""
        from PySide6.QtWidgets import QApplication
        import sys
        import os

        # 获取当前应用程序实例
        app = QApplication.instance()

        # 关闭所有窗口
        app.closeAllWindows()

        # 保存配置
        self._save_config()

        # 退出应用（返回码 133 表示需要重启）
        app.exit(133)

    # === 提供商管理相关方法 ===

    def _on_provider_selected(self, item):
        """提供商选择处理（单击）"""
        provider_id = item.data(Qt.UserRole)
        if not provider_id:
            return

        providers = provider_manager.get_providers()
        provider = next((p for p in providers if p.id == provider_id), None)

        if provider:
            # 显示详情
            info_text = f"ID: {provider.id} | 类型: {provider.provider_type.value} | 模型: {provider.model}"

            masked_key = provider.api_key[:8] + "..." if len(provider.api_key) > 8 else "***"
            info_text += f" | API密钥: {masked_key}"

            self.detail_info.setText(info_text)

            # 启用按钮
            self.switch_btn.setEnabled(not provider.is_active)
            self.edit_btn.setEnabled(True)
            self.delete_btn.setEnabled(not provider.is_active)

    def _on_provider_double_clicked(self, item):
        """提供商双击处理（双击直接编辑）"""
        provider_id = item.data(Qt.UserRole)
        if not provider_id:
            return

        providers = provider_manager.get_providers()
        provider = next((p for p in providers if p.id == provider_id), None)

        if provider:
            # 创建预设对象以重用对话框
            preset = ProviderPreset(
                id=provider.id,
                name=provider.name,
                description="",
                category=provider.provider_type.value,
                config=provider
            )

            dialog = ProviderConfigDialog(preset, self)
            # 使用 set_config 方法填充所有字段
            dialog.set_config(provider)

            if dialog.exec() == QDialog.Accepted:
                config = dialog.get_config()
                if provider_manager.update_provider(provider_id, config):
                    InfoBar.success(
                        title="成功",
                        content=f"已更新提供商: {config.name}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                    self._load_providers()
                    # 更新详情显示
                    self._on_provider_selected(self.provider_list.currentItem())
                else:
                    InfoBar.error(
                        title="失败",
                        content="更新提供商失败",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )

    def _on_import_preset(self):
        """导入预设"""
        dialog = PresetImportDialog(self)
        dialog.preset_selected.connect(self._show_config_dialog_for_preset)
        dialog.exec()

    def _show_config_dialog_for_preset(self, preset_id: str):
        """显示预设配置对话框"""
        preset = next((p for p in PROVIDER_PRESETS if p.id == preset_id), None)
        if preset:
            dialog = ProviderConfigDialog(preset, self)
            if dialog.exec() == QDialog.Accepted:
                config = dialog.get_config()
                if provider_manager.add_provider(config):
                    InfoBar.success(
                        title="成功",
                        content=f"已添加提供商: {config.name}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                    self._load_providers()
                else:
                    InfoBar.error(
                        title="失败",
                        content="添加提供商失败",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )

    def _on_add_provider(self):
        """手动添加提供商"""
        dialog = ProviderConfigDialog(parent=self)
        if dialog.exec() == QDialog.Accepted:
            config = dialog.get_config()
            if provider_manager.add_provider(config):
                InfoBar.success(
                    title="成功",
                    content=f"已添加提供商: {config.name}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                self._load_providers()
            else:
                InfoBar.error(
                    title="失败",
                    content="添加提供商失败",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )

    def _on_edit_provider(self):
        """编辑提供商"""
        current = self.provider_list.currentItem()
        if not current:
            InfoBar.warning(
                title="提示",
                content="请先选择要编辑的提供商",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=2000,
                parent=self
            )
            return

        provider_id = current.data(Qt.UserRole)
        providers = provider_manager.get_providers()
        provider = next((p for p in providers if p.id == provider_id), None)

        if provider:
            # 创建预设对象以重用对话框
            preset = ProviderPreset(
                id=provider.id,
                name=provider.name,
                description="",
                category=provider.provider_type.value,
                config=provider
            )

            dialog = ProviderConfigDialog(preset, self)
            # 使用 set_config 方法填充所有字段
            dialog.set_config(provider)

            if dialog.exec() == QDialog.Accepted:
                config = dialog.get_config()
                if provider_manager.update_provider(provider_id, config):
                    InfoBar.success(
                        title="成功",
                        content=f"已更新提供商: {config.name}",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )
                    self._load_providers()
                    # 更新详情显示
                    self._on_provider_selected(self.provider_list.currentItem())
                else:
                    InfoBar.error(
                        title="失败",
                        content="更新提供商失败",
                        orient=Qt.Horizontal,
                        isClosable=True,
                        position=InfoBarPosition.TOP,
                        duration=3000,
                        parent=self
                    )

    def _on_delete_provider(self):
        """删除提供商"""
        current = self.provider_list.currentItem()
        if not current:
            return

        provider_id = current.data(Qt.UserRole)

        # 确认对话框
        msg_box = MessageBox("确认删除", "确定要删除此提供商吗？", self)
        if msg_box.exec():
            if provider_manager.delete_provider(provider_id):
                InfoBar.success(
                    title="成功",
                    content="提供商已删除",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
                self._load_providers()
                self.detail_info.setText("请从上方列表选择一个提供商")
                self.switch_btn.setEnabled(False)
                self.edit_btn.setEnabled(False)
                self.delete_btn.setEnabled(False)
            else:
                InfoBar.error(
                    title="失败",
                    content="删除提供商失败",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )

    def _on_switch_provider(self):
        """切换提供商"""
        current = self.provider_list.currentItem()
        if not current:
            return

        provider_id = current.data(Qt.UserRole)

        if provider_manager.switch_provider(provider_id):
            InfoBar.success(
                title="成功",
                content="已切换提供商",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )
            self._load_providers()
            self.switch_btn.setEnabled(False)
        else:
            InfoBar.error(
                title="失败",
                content="切换提供商失败",
                orient=Qt.Horizontal,
                isClosable=True,
                position=InfoBarPosition.TOP,
                duration=3000,
                parent=self
            )

    def _on_export(self):
        """导出配置"""
        import json

        json_data = provider_manager.export_providers()

        from PySide6.QtWidgets import QFileDialog
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "导出提供商配置",
            "providers.json",
            "JSON Files (*.json)"
        )

        if file_path:
            try:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(json_data)
                InfoBar.success(
                    title="成功",
                    content=f"已导出到: {file_path}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )
            except Exception as e:
                InfoBar.error(
                    title="失败",
                    content=f"导出失败: {e}",
                    orient=Qt.Horizontal,
                    isClosable=True,
                    position=InfoBarPosition.TOP,
                    duration=3000,
                    parent=self
                )

    # === 快速 AI 配置相关方法 ===

    def _on_provider_changed(self, provider: str):
        """提供商变化处理"""
        # 根据提供商更新模型列表
        self.model_combo.clear()

        if provider == "claude":
            models = ["claude-opus-4-6", "claude-sonnet-4-6", "claude-haiku-4-5-20251001"]
        elif provider == "openai":
            models = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-3.5-turbo"]
        else:  # deepseek
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
        # 临时保存当前密钥
        current_key = self.api_key_edit.text()
        if current_key:
            config_service.save_api_key(
                self.provider_combo.currentText(),
                current_key
            )

        # 验证
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
