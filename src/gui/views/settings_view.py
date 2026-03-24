# -*- coding: utf-8 -*-
"""
Settings View
Application settings interface
"""
from typing import Optional, Dict, Any
from PySide6.QtCore import Qt, Signal, QThread, QObject, QTimer
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QSpinBox,
    QTextEdit, QTabWidget, QFileDialog, QMessageBox,
    QGroupBox, QFormLayout, QCheckBox, QDoubleSpinBox
)
from qfluentwidgets import (
    PushButton, LineEdit, ComboBox, SpinBox,
    TextEdit, CheckBox, InfoBar,
    InfoBarPosition, FluentIcon, BodyLabel,
    StrongBodyLabel, SwitchButton, SubtitleLabel,
    CaptionLabel, setTheme, Theme, TabWidget, CardWidget, IconWidget
)
from qfluentwidgets.components.widgets.separator import HorizontalSeparator

import os
import json
import asyncio

from ...services import config_service, provider_manager
from ...services.provider_service import ProviderConfig, ProviderType
from ...services.ai_client_factory import create_ai_client
from ...ai.base import Message, MessageRole, AIRequestConfig


class ValidationWorker(QObject):
    """API验证工作线程"""

    finished = Signal(bool, str)  # (is_valid, message)

    def __init__(self, client):
        super().__init__()
        self.client = client

    def validate(self):
        """执行验证"""
        try:
            # 在新线程中创建事件循环
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)

            try:
                # Build test message
                messages = [
                    Message(role=MessageRole.USER, content="Hello")
                ]

                # Build request config
                config = AIRequestConfig(
                    max_tokens=10,
                    temperature=0.5
                )

                # Send chat request
                response = loop.run_until_complete(self.client.chat(messages, config))

                if response and response.content:
                    self.finished.emit(True, "API key validation successful")
                else:
                    self.finished.emit(False, "API returned empty response")

            finally:
                loop.close()

        except Exception as e:
            error_msg = str(e)
            # Extract key error information
            if "AuthenticationError" in error_msg or "401" in error_msg:
                self.finished.emit(False, "Invalid API key")
            elif "Connection" in error_msg or "Timeout" in error_msg:
                self.finished.emit(False, "Network connection failed")
            else:
                self.finished.emit(False, f"Validation failed: {error_msg}")


class SettingsSaveWorker(QObject):
    """设置保存工作线程 - 在后台执行数据库操作，避免UI卡死"""

    finished = Signal(bool, str)  # (success, message)

    def __init__(self, settings: dict, provider: str):
        super().__init__()
        self.settings = settings
        self.provider = provider

    def _get_provider_type(self, provider: str) -> ProviderType:
        """Convert provider string to ProviderType"""
        provider_map = {
            "claude": ProviderType.CLAUDE,
            "anthropic": ProviderType.CLAUDE,
            "openai": ProviderType.OPENAI,
            "deepseek": ProviderType.DEEPSEEK,
            "ollama": ProviderType.CUSTOM,
            "openrouter": ProviderType.CUSTOM
        }
        return provider_map.get(provider.lower(), ProviderType.CUSTOM)

    def run(self):
        """执行保存操作（在后台线程中）"""
        try:
            api_config = self.settings.get("api", {})
            provider = self.provider
            api_key = api_config.get("api_key", "")
            base_url = api_config.get("base_url", "")
            model = api_config.get("model", "")
            max_tokens = api_config.get("max_tokens", 4096)
            temperature = api_config.get("temperature", 0.7)

            # Don't update Provider system if no API key
            if not api_key:
                print("Warning: No API key provided, skipping Provider system sync")
                self.finished.emit(True, "Settings saved (no API key to sync)")
                return

            # Get or create default Provider
            provider_type = self._get_provider_type(provider)

            # Try to get existing default provider
            existing_providers = provider_manager.get_providers()
            default_provider = None

            # Find existing default provider (id is "default" or first one)
            for p in existing_providers:
                if p.id == "default":
                    default_provider = p
                    break

            # Build ProviderConfig
            provider_config = ProviderConfig(
                id=default_provider.id if default_provider else "default",
                name=f"{provider.upper()} (Default)",
                provider_type=provider_type,
                api_key=api_key,
                api_endpoint=base_url if base_url else "",
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                is_active=True,
                is_enabled=True
            )

            # Update or create Provider
            if default_provider:
                success = provider_manager.update_provider(provider_config.id, provider_config)
                if success:
                    print(f"Success: Updated default Provider: {provider_config.id}")
                    # Switch to this provider
                    provider_manager.switch_provider(provider_config.id)
                else:
                    print(f"Warning: Failed to update Provider")
            else:
                success = provider_manager.add_provider(provider_config)
                if success:
                    print(f"Success: Created default Provider: {provider_config.id}")
                    # Switch to this provider
                    provider_manager.switch_provider(provider_config.id)
                else:
                    print(f"Warning: Failed to create Provider")

            self.finished.emit(True, "Settings saved successfully")

        except Exception as e:
            error_msg = f"Failed to sync to Provider system: {str(e)}"
            print(f"Error: {error_msg}")
            import traceback
            traceback.print_exc()
            self.finished.emit(False, error_msg)


class SettingsView(QWidget):
    """Settings View"""

    # Signal definitions
    settings_changed = Signal()
    api_key_validated = Signal(bool, str)  # (is_valid, message)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = config_service.get_config()

        self._validation_thread = None
        self._validation_worker = None

        self._save_thread = None
        self._save_worker = None

        # 存储实际的 API Key（用于显示/隐藏切换）
        self._actual_api_key = ""
        # 标志：防止程序化设置文本时触发 textChanged
        self._is_setting_text_programmatically = False

        # API Key 自动保存定时器（防抖）
        self._auto_save_timer = QTimer(self)
        self._auto_save_timer.setSingleShot(True)
        self._auto_save_timer.timeout.connect(self._auto_save_api_key)

        self._init_ui()
        self._load_settings()

    def _init_ui(self):
        """Initialize UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)

        # Title
        title = SubtitleLabel("Settings")
        layout.addWidget(title)

        # Create tabs using qfluentwidgets TabWidget
        self.tabs = TabWidget()

        # API Settings tab
        api_tab = self._create_api_tab()
        self.tabs.addTab(api_tab, 'API Settings', FluentIcon.SETTING, 'api')

        # Code Analysis tab
        analysis_tab = self._create_analysis_tab()
        self.tabs.addTab(analysis_tab, 'Code Analysis', FluentIcon.EDIT, 'analysis')

        # Display Settings tab
        display_tab = self._create_display_tab()
        self.tabs.addTab(display_tab, 'Display', FluentIcon.BRIGHTNESS, 'display')

        layout.addWidget(self.tabs)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.save_btn = PushButton("Save")
        self.save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

        # 连接 API Key 输入框的文本变化信号
        self.api_key_input.textChanged.connect(self._on_api_key_changed)

    def _create_api_tab(self) -> QWidget:
        """Create API Settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # AI Provider card
        provider_card = CardWidget(widget)
        provider_layout = QVBoxLayout(provider_card)
        provider_layout.setContentsMargins(20, 16, 20, 16)

        # Header with icon and title
        provider_header = QHBoxLayout()
        provider_icon = IconWidget(FluentIcon.DEVELOPER_TOOLS, provider_card)
        provider_icon.setFixedSize(22, 22)
        provider_header.addWidget(provider_icon)
        provider_title = StrongBodyLabel("AI Provider")
        provider_header.addWidget(provider_title)
        provider_header.addStretch()
        provider_layout.addLayout(provider_header)

        # Content
        provider_input_layout = QHBoxLayout()
        provider_label = StrongBodyLabel("Provider:")
        self.provider_combo = ComboBox()
        self.provider_combo.addItems(["openai", "anthropic", "claude", "ollama", "deepseek", "openrouter"])
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_input_layout.addWidget(provider_label)
        provider_input_layout.addWidget(self.provider_combo, 1)
        provider_layout.addLayout(provider_input_layout)

        layout.addWidget(provider_card)

        # API Key card
        api_key_card = CardWidget(widget)
        api_key_layout = QVBoxLayout(api_key_card)
        api_key_layout.setContentsMargins(20, 16, 20, 16)

        # Header
        api_key_header = QHBoxLayout()
        api_key_icon = IconWidget(FluentIcon.FINGERPRINT, api_key_card)
        api_key_icon.setFixedSize(22, 22)
        api_key_header.addWidget(api_key_icon)
        api_key_title = StrongBodyLabel("API Key")
        api_key_header.addWidget(api_key_title)
        api_key_header.addStretch()
        api_key_layout.addLayout(api_key_header)

        # API Key input
        api_key_input_layout = QHBoxLayout()
        api_key_label = StrongBodyLabel("API Key:")
        self.api_key_input = LineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter your API key...")
        api_key_input_layout.addWidget(api_key_label)
        api_key_input_layout.addWidget(self.api_key_input, 1)
        api_key_layout.addLayout(api_key_input_layout)

        # Buttons
        btn_layout = QHBoxLayout()
        self.api_key_show_btn = PushButton("Show")
        self.api_key_show_btn.setCheckable(True)
        self.api_key_show_btn.clicked.connect(self._toggle_api_key_visibility)
        btn_layout.addWidget(self.api_key_show_btn)

        self.validate_btn = PushButton("Validate")
        self.validate_btn.clicked.connect(self._validate_api_key)
        btn_layout.addWidget(self.validate_btn)
        btn_layout.addStretch()
        api_key_layout.addLayout(btn_layout)

        # Validation result
        self.validation_result = StrongBodyLabel()
        self.validation_result.setWordWrap(True)
        api_key_layout.addWidget(self.validation_result)

        layout.addWidget(api_key_card)

        # Base URL card
        base_url_card = CardWidget(widget)
        base_url_layout = QVBoxLayout(base_url_card)
        base_url_layout.setContentsMargins(20, 16, 20, 16)

        # Header
        base_url_header = QHBoxLayout()
        base_url_icon = IconWidget(FluentIcon.LINK, base_url_card)
        base_url_icon.setFixedSize(22, 22)
        base_url_header.addWidget(base_url_icon)
        base_url_title = StrongBodyLabel("Base URL (Optional)")
        base_url_header.addWidget(base_url_title)
        base_url_header.addStretch()
        base_url_layout.addLayout(base_url_header)

        # Base URL input
        base_url_input_layout = QHBoxLayout()
        base_url_label = StrongBodyLabel("Base URL:")
        self.base_url_input = LineEdit()
        self.base_url_input.setPlaceholderText("https://api.example.com (leave empty for default)")
        base_url_input_layout.addWidget(base_url_label)
        base_url_input_layout.addWidget(self.base_url_input, 1)
        base_url_layout.addLayout(base_url_input_layout)

        layout.addWidget(base_url_card)

        # Model settings card
        model_card = CardWidget(widget)
        model_layout = QVBoxLayout(model_card)
        model_layout.setContentsMargins(20, 16, 20, 16)

        # Header
        model_header = QHBoxLayout()
        model_icon = IconWidget(FluentIcon.TAG, model_card)
        model_icon.setFixedSize(22, 22)
        model_header.addWidget(model_icon)
        model_title = StrongBodyLabel("Model Settings")
        model_header.addWidget(model_title)
        model_header.addStretch()
        model_layout.addLayout(model_header)

        # Model name
        model_input_layout = QHBoxLayout()
        model_label = StrongBodyLabel("Model Name:")
        self.model_input = LineEdit()
        self.model_input.setPlaceholderText("e.g.: gpt-4, claude-3-opus-20240229")
        model_input_layout.addWidget(model_label)
        model_input_layout.addWidget(self.model_input, 1)
        model_layout.addLayout(model_input_layout)

        # Max Tokens dropdown
        max_tokens_layout = QHBoxLayout()
        max_tokens_label = StrongBodyLabel("Max Tokens:")
        self.max_tokens_combo = ComboBox()
        self.max_tokens_combo.addItems([
            "2K (2048)",
            "4K (4096)",
            "8K (8192)",
            "16K (16384)",
            "32K (32768)",
            "64K (65536)"
        ])
        self.max_tokens_combo.setCurrentText("4K (4096)")
        max_tokens_layout.addWidget(max_tokens_label)
        max_tokens_layout.addWidget(self.max_tokens_combo, 1)
        model_layout.addLayout(max_tokens_layout)

        # Temperature input
        temp_layout = QHBoxLayout()
        temp_label = StrongBodyLabel("Temperature:")
        self.temperature_input = SpinBox()
        self.temperature_input.setRange(0, 20)
        self.temperature_input.setValue(7)
        self.temperature_input.setSingleStep(1)
        temp_hint = CaptionLabel("(0.0 - 2.0, enter as integer: 7 = 0.7)")
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.temperature_input, 1)
        temp_layout.addWidget(temp_hint)
        model_layout.addLayout(temp_layout)

        layout.addWidget(model_card)
        layout.addStretch()

        return widget

    def _create_analysis_tab(self) -> QWidget:
        """Create Code Analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Analysis Scope card
        scope_card = CardWidget(widget)
        scope_layout = QVBoxLayout(scope_card)
        scope_layout.setContentsMargins(20, 16, 20, 16)

        # Header
        scope_header = QHBoxLayout()
        scope_icon = IconWidget(FluentIcon.SEARCH, scope_card)
        scope_icon.setFixedSize(22, 22)
        scope_header.addWidget(scope_icon)
        scope_title = StrongBodyLabel("Analysis Scope")
        scope_header.addWidget(scope_title)
        scope_header.addStretch()
        scope_layout.addLayout(scope_header)

        # Max depth
        depth_layout = QHBoxLayout()
        depth_label = StrongBodyLabel("Max Depth:")
        self.max_depth_input = SpinBox()
        self.max_depth_input.setRange(1, 10)
        self.max_depth_input.setValue(3)
        depth_layout.addWidget(depth_label)
        depth_layout.addWidget(self.max_depth_input, 1)
        scope_layout.addLayout(depth_layout)

        # Max files
        files_layout = QHBoxLayout()
        files_label = StrongBodyLabel("Max Files:")
        self.max_files_input = SpinBox()
        self.max_files_input.setRange(10, 1000)
        self.max_files_input.setValue(100)
        files_layout.addWidget(files_label)
        files_layout.addWidget(self.max_files_input, 1)
        scope_layout.addLayout(files_layout)

        layout.addWidget(scope_card)

        # File Filters card
        filter_card = CardWidget(widget)
        filter_layout = QVBoxLayout(filter_card)
        filter_layout.setContentsMargins(20, 16, 20, 16)

        # Header
        filter_header = QHBoxLayout()
        filter_icon = IconWidget(FluentIcon.FILTER, filter_card)
        filter_icon.setFixedSize(22, 22)
        filter_header.addWidget(filter_icon)
        filter_title = StrongBodyLabel("File Filters")
        filter_header.addWidget(filter_title)
        filter_header.addStretch()
        filter_layout.addLayout(filter_header)

        self.exclude_patterns_input = TextEdit()
        self.exclude_patterns_input.setPlaceholderText(
            "One pattern per line, e.g.:\n"
            "*.log\n"
            "node_modules/*\n"
            "*.min.js"
        )
        self.exclude_patterns_input.setMaximumHeight(100)
        filter_layout.addWidget(self.exclude_patterns_input)

        layout.addWidget(filter_card)

        # Analysis Options card
        options_card = CardWidget(widget)
        options_layout = QVBoxLayout(options_card)
        options_layout.setContentsMargins(20, 16, 20, 16)

        # Header
        options_header = QHBoxLayout()
        options_icon = IconWidget(FluentIcon.SETTING, options_card)
        options_icon.setFixedSize(22, 22)
        options_header.addWidget(options_icon)
        options_title = StrongBodyLabel("Analysis Options")
        options_header.addWidget(options_title)
        options_header.addStretch()
        options_layout.addLayout(options_header)

        self.include_comments_cb = CheckBox("Include Comments")
        self.include_comments_cb.setChecked(True)
        options_layout.addWidget(self.include_comments_cb)

        self.analyze_tests_cb = CheckBox("Analyze Test Files")
        self.analyze_tests_cb.setChecked(True)
        options_layout.addWidget(self.analyze_tests_cb)

        self.follow_imports_cb = CheckBox("Follow Imports")
        self.follow_imports_cb.setChecked(True)
        options_layout.addWidget(self.follow_imports_cb)

        layout.addWidget(options_card)
        layout.addStretch()

        return widget

    def _create_display_tab(self) -> QWidget:
        """Create Display Settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        layout.setContentsMargins(20, 20, 20, 20)

        # Theme card
        theme_card = CardWidget(widget)
        theme_layout = QVBoxLayout(theme_card)
        theme_layout.setContentsMargins(20, 16, 20, 16)

        # Header
        theme_header = QHBoxLayout()
        theme_icon = IconWidget(FluentIcon.BRIGHTNESS, theme_card)
        theme_icon.setFixedSize(22, 22)
        theme_header.addWidget(theme_icon)
        theme_title = StrongBodyLabel("Theme")
        theme_header.addWidget(theme_title)
        theme_header.addStretch()
        theme_layout.addLayout(theme_header)

        self.follow_system_cb = CheckBox("Follow System Theme")
        self.follow_system_cb.setChecked(True)
        self.follow_system_cb.stateChanged.connect(self._on_follow_system_changed)
        theme_layout.addWidget(self.follow_system_cb)

        theme_mode_layout = QHBoxLayout()
        theme_label = StrongBodyLabel("Theme Mode:")
        self.theme_combo = ComboBox()
        self.theme_combo.addItems(["light", "dark"])
        self.theme_combo.setEnabled(False)
        theme_mode_layout.addWidget(theme_label)
        theme_mode_layout.addWidget(self.theme_combo, 1)
        theme_layout.addLayout(theme_mode_layout)

        layout.addWidget(theme_card)

        # Window card
        window_card = CardWidget(widget)
        window_layout = QVBoxLayout(window_card)
        window_layout.setContentsMargins(20, 16, 20, 16)

        # Header
        window_header = QHBoxLayout()
        window_icon = IconWidget(FluentIcon.FULL_SCREEN, window_card)
        window_icon.setFixedSize(22, 22)
        window_header.addWidget(window_icon)
        window_title = StrongBodyLabel("Window")
        window_header.addWidget(window_title)
        window_header.addStretch()
        window_layout.addLayout(window_header)

        self.remember_size_cb = CheckBox("Remember Window Size")
        self.remember_size_cb.setChecked(True)
        window_layout.addWidget(self.remember_size_cb)

        self.remember_pos_cb = CheckBox("Remember Window Position")
        self.remember_pos_cb.setChecked(True)
        window_layout.addWidget(self.remember_pos_cb)

        layout.addWidget(window_card)
        layout.addStretch()

        return widget

    def _on_follow_system_changed(self, state: int):
        """Handle follow system checkbox state change"""
        is_following = state == Qt.CheckState.Checked.value
        self.theme_combo.setEnabled(not is_following)

    def _on_theme_combo_changed(self, index: int):
        """Handle theme combo box change"""
        pass  # Theme will be saved when user clicks Save

    def _on_provider_changed(self, provider: str):
        """Handle provider change"""
        # Set default values based on provider
        defaults = {
            "openai": {
                "model": "gpt-4",
                "base_url": ""
            },
            "anthropic": {
                "model": "claude-3-opus-20240229",
                "base_url": ""
            },
            "claude": {
                "model": "claude-3-5-sonnet-20241022",
                "base_url": ""
            },
            "ollama": {
                "model": "llama2",
                "base_url": "http://localhost:11434/v1"
            },
            "deepseek": {
                "model": "deepseek-chat",
                "base_url": ""
            },
            "openrouter": {
                "model": "anthropic/claude-3-opus",
                "base_url": "https://openrouter.ai/api/v1"
            }
        }

        if provider in defaults:
            self.model_input.setText(defaults[provider]["model"])
            if hasattr(self, 'base_url_input'):
                current_base_url = self.base_url_input.text().strip()
                # Only set default if current value is empty
                if not current_base_url:
                    self.base_url_input.setText(defaults[provider]["base_url"])

    def _parse_max_tokens(self) -> int:
        """Parse max tokens from combo box text"""
        text = self.max_tokens_combo.currentText()
        # Extract number from text like "4K (4096)" or just "4096"
        import re
        match = re.search(r'\((\d+)\)|(\d+)', text)
        if match:
            return int(match.group(1) if match.group(1) else match.group(2))
        return 4096  # Default

    def _format_max_tokens(self, tokens: int) -> str:
        """Format max tokens to combo box text"""
        token_map = {
            2048: "2K (2048)",
            4096: "4K (4096)",
            8192: "8K (8192)",
            16384: "16K (16384)",
            32768: "32K (32768)",
            65536: "64K (65536)"
        }
        return token_map.get(tokens, f"Custom ({tokens})")

    def _parse_temperature(self) -> float:
        """Parse temperature from spin box (integer 0-20 represents 0.0-2.0)"""
        return self.temperature_input.value() / 10.0

    def _format_temperature(self, temp: float) -> int:
        """Format temperature to spin box value (float 0.0-2.0 to integer 0-20)"""
        return int(temp * 10)

    def _on_api_key_changed(self, text: str):
        """当用户修改 API Key 输入框时更新实际值"""
        # 如果是程序化设置文本，不处理
        if self._is_setting_text_programmatically:
            return
        # 如果用户输入的不是掩码，说明用户在修改，更新实际值
        if text != "********":
            old_key = self._actual_api_key
            self._actual_api_key = text
            # 如果 API Key 发生了实质性变化（从空到有值，或从有值变为不同值），延迟自动保存
            if (not old_key and text.strip()) or (old_key and text.strip() != old_key):
                # 停止之前的定时器，重新开始计时
                self._auto_save_timer.stop()
                self._auto_save_timer.start(1000)  # 1秒后自动保存

    def _auto_save_api_key(self):
        """自动保存 API Key（不显示通知）"""
        try:
            provider = self.provider_combo.currentText()
            settings = {
                "api": {
                    "provider": provider,
                    "api_key": self._actual_api_key,
                    "base_url": self.base_url_input.text(),
                    "model": self.model_input.text(),
                    "max_tokens": self._parse_max_tokens(),
                    "temperature": self._parse_temperature()
                },
                "display": {
                    "theme": "auto" if self.follow_system_cb.isChecked() else self.theme_combo.currentText(),
                    "remember_size": self.remember_size_cb.isChecked(),
                    "remember_position": self.remember_pos_cb.isChecked()
                }
            }
            config_service.update_config(settings)
        except Exception as e:
            # 静默失败，不影响用户体验
            pass

    def _toggle_api_key_visibility(self, checked: bool):
        """Toggle API key visibility"""
        self._is_setting_text_programmatically = True
        if checked:
            # 显示实际的 API Key
            self.api_key_input.setText(self._actual_api_key)
            self.api_key_input.setEchoMode(QLineEdit.Normal)
            self.api_key_show_btn.setText("Hide")
        else:
            # 隐藏时显示掩码（如果有实际值）
            if self._actual_api_key:
                self.api_key_input.setText("********")
            self.api_key_input.setEchoMode(QLineEdit.Password)
            self.api_key_show_btn.setText("Show")
        self._is_setting_text_programmatically = False

    def _get_provider_type(self, provider: str) -> ProviderType:
        """Convert provider string to ProviderType"""
        provider_map = {
            "claude": ProviderType.CLAUDE,
            "anthropic": ProviderType.CLAUDE,
            "openai": ProviderType.OPENAI,
            "deepseek": ProviderType.DEEPSEEK,
            "ollama": ProviderType.CUSTOM,
            "openrouter": ProviderType.CUSTOM
        }
        return provider_map.get(provider.lower(), ProviderType.CUSTOM)

    def _on_validation_finished(self, is_valid: bool, message: str):
        """验证完成回调（在主线程中执行）"""
        # 清理线程
        if self._validation_thread:
            self._validation_thread.quit()
            self._validation_thread.wait()
            self._validation_thread = None
            self._validation_worker = None

        # 恢复按钮状态
        self.validate_btn.setEnabled(True)
        self.api_key_input.setEnabled(True)

        if is_valid:
            self.validation_result.setText("Success: " + message)
            InfoBar.success(
                title="Validation Successful",
                content=message,
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.api_key_validated.emit(True, message)
        else:
            self.validation_result.setText("Error: " + message)
            InfoBar.error(
                title="Validation Failed",
                content=message,
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.api_key_validated.emit(False, message)

    def _validate_api_key(self):
        """Validate API key"""
        # 获取 API Key：如果输入框是掩码，使用实际保存的值
        current_input = self.api_key_input.text()
        api_key = current_input if current_input != "********" else self._actual_api_key

        api_key = api_key.strip()
        provider = self.provider_combo.currentText()
        base_url = self.base_url_input.text().strip()
        model = self.model_input.text().strip()

        if not api_key:
            self.validation_result.setText("Error: Please enter API key")
            InfoBar.error(
                title="Validation Failed",
                content="Please enter API key",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return

        if not model:
            self.validation_result.setText("Error: Please enter model name")
            InfoBar.error(
                title="Validation Failed",
                content="Please enter model name",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return

        self.validation_result.setText("Validating...")

        try:
            # Build ProviderConfig
            provider_type = self._get_provider_type(provider)

            config = ProviderConfig(
                id="temp_validation",
                name=f"{provider} (validation)",
                provider_type=provider_type,
                api_key=api_key,
                api_endpoint=base_url,
                model=model,
                max_tokens=10,  # Use small value for validation
                temperature=0.5
            )

            # Create client using factory
            client = create_ai_client(config)

            # 禁用按钮和输入，防止重复点击
            self.validate_btn.setEnabled(False)
            self.api_key_input.setEnabled(False)

            # 创建工作线程
            self._validation_thread = QThread()
            self._validation_worker = ValidationWorker(client)
            self._validation_worker.moveToThread(self._validation_thread)

            # 连接信号
            self._validation_thread.started.connect(self._validation_worker.validate)
            self._validation_worker.finished.connect(self._on_validation_finished)

            # 启动线程
            self._validation_thread.start()

        except Exception as e:
            error_msg = f"Initialization failed: {str(e)}"
            self.validation_result.setText(f"Error: {error_msg}")
            InfoBar.error(
                title="Initialization Failed",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.api_key_validated.emit(False, error_msg)
            # 恢复按钮状态
            self.validate_btn.setEnabled(True)
            self.api_key_input.setEnabled(True)

    def _load_settings(self):
        """Load settings from AppConfig object"""
        try:
            # Load API settings from AppConfig.ai
            ai_config = self.config.ai
            self.provider_combo.setCurrentText(ai_config.provider)

            # API Key 不直接显示，保存实际值到内部变量，显示掩码
            self._actual_api_key = ai_config.api_key
            self._is_setting_text_programmatically = True
            if self._actual_api_key:
                self.api_key_input.setText("********")  # 显示掩码
            else:
                self.api_key_input.setText("")
            self._is_setting_text_programmatically = False
            self.model_input.setText(ai_config.model)

            # Load base_url, max_tokens, temperature from config if available
            # These may be stored in a separate config section
            base_url = getattr(ai_config, 'base_url', '') or ""
            max_tokens = getattr(ai_config, 'max_tokens', 4096)
            temperature = getattr(ai_config, 'temperature', 0.7)

            self.base_url_input.setText(base_url)
            self.max_tokens_combo.setCurrentText(self._format_max_tokens(max_tokens))
            self.temperature_input.setValue(self._format_temperature(temperature))

            # Load display settings from AppConfig
            theme_value = self.config.theme
            if theme_value == "auto":
                # Follow system mode
                self.follow_system_cb.setChecked(True)
                self.theme_combo.setCurrentText("light")  # Default value when following system
            else:
                # Manual mode
                self.follow_system_cb.setChecked(False)
                self.theme_combo.setCurrentText(theme_value if theme_value in ["light", "dark"] else "light")

            # For analysis settings, use defaults since they're not in AppConfig
            # These can be stored separately if needed
            self.max_depth_input.setValue(3)
            self.max_files_input.setValue(100)
            self.exclude_patterns_input.setPlainText("")
            self.include_comments_cb.setChecked(True)
            self.analyze_tests_cb.setChecked(True)
            self.follow_imports_cb.setChecked(True)

            # Window settings
            self.remember_size_cb.setChecked(True)
            self.remember_pos_cb.setChecked(True)

        except Exception as e:
            InfoBar.error(
                title="Load Failed",
                content=f"Error loading settings: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP
            )

    def _on_save_finished(self, success: bool, message: str):
        """保存完成回调（在主线程中执行）"""
        # 清理线程
        if self._save_thread:
            self._save_thread.quit()
            self._save_thread.wait()
            self._save_thread = None
            self._save_worker = None

        # 恢复按钮状态
        self.save_btn.setEnabled(True)

        if success:
            # Emit settings changed event
            self.settings_changed.emit()

            # Show success message
            InfoBar.success(
                title="Save Successful",
                content=message,
                parent=self,
                position=InfoBarPosition.TOP
            )
        else:
            # Show error message
            InfoBar.error(
                title="Save Failed",
                content=message,
                parent=self,
                position=InfoBarPosition.TOP
            )

    def _save_settings(self):
        """Save settings - 使用后台线程避免UI卡死"""
        try:
            # 禁用保存按钮，防止重复点击
            self.save_btn.setEnabled(False)

            # 获取 API Key：如果输入框是掩码，使用实际保存的值
            current_input = self.api_key_input.text()
            api_key_to_save = current_input if current_input != "********" else self._actual_api_key

            provider = self.provider_combo.currentText()

            # Build settings dictionary
            settings = {
                "api": {
                    "provider": provider,
                    "api_key": api_key_to_save,
                    "base_url": self.base_url_input.text(),
                    "model": self.model_input.text(),
                    "max_tokens": self._parse_max_tokens(),
                    "temperature": self._parse_temperature()
                },
                "analysis": {
                    "max_depth": self.max_depth_input.value(),
                    "max_files": self.max_files_input.value(),
                    "exclude_patterns": [
                        p.strip() for p in self.exclude_patterns_input.toPlainText().split("\n")
                        if p.strip()
                    ],
                    "include_comments": self.include_comments_cb.isChecked(),
                    "analyze_tests": self.analyze_tests_cb.isChecked(),
                    "follow_imports": self.follow_imports_cb.isChecked()
                },
                "display": {
                    "theme": "auto" if self.follow_system_cb.isChecked() else self.theme_combo.currentText(),
                    "remember_size": self.remember_size_cb.isChecked(),
                    "remember_position": self.remember_pos_cb.isChecked()
                }
            }

            # Save to config file (同步操作，通常很快)
            config_service.update_config(settings)

            # Sync to Provider system in background thread (异步操作，避免卡死UI)

            # 创建工作线程
            self._save_thread = QThread()
            self._save_worker = SettingsSaveWorker(settings, provider)
            self._save_worker.moveToThread(self._save_thread)

            # 连接信号
            self._save_thread.started.connect(self._save_worker.run)
            self._save_worker.finished.connect(self._on_save_finished)

            # 启动线程
            self._save_thread.start()

        except Exception as e:
            # 恢复按钮状态
            self.save_btn.setEnabled(True)

            InfoBar.error(
                title="Save Failed",
                content=f"Error saving settings: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP
            )
