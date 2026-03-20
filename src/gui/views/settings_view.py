# -*- coding: utf-8 -*-
"""
Settings View
Application settings interface
"""
from typing import Optional, Dict, Any
from PySide6.QtCore import Qt, Signal, QThread, QObject
from PySide6.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QPushButton, QLineEdit, QComboBox, QSpinBox,
    QTextEdit, QTabWidget, QFileDialog, QMessageBox,
    QGroupBox, QFormLayout, QCheckBox, QDoubleSpinBox
)
from qfluentwidgets import (
    PushButton, LineEdit, ComboBox, SpinBox,
    TextEdit, CheckBox, CardWidget, InfoBar,
    InfoBarPosition, FluentIcon, BodyLabel,
    StrongBodyLabel, SwitchButton, SubtitleLabel
)

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

        # Create tabs
        self.tabs = QTabWidget()

        # API Settings tab
        api_tab = self._create_api_tab()
        self.tabs.addTab(api_tab, "API Settings")

        # Code Analysis tab
        analysis_tab = self._create_analysis_tab()
        self.tabs.addTab(analysis_tab, "Code Analysis")

        # Display Settings tab
        display_tab = self._create_display_tab()
        self.tabs.addTab(display_tab, "Display")

        layout.addWidget(self.tabs)

        # Bottom buttons
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()

        self.save_btn = PushButton("Save")
        self.save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.save_btn)

        layout.addLayout(btn_layout)

    def _create_api_tab(self) -> QWidget:
        """Create API Settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # AI Provider selection
        provider_group = CardWidget()
        provider_layout = QVBoxLayout(provider_group)

        provider_label = StrongBodyLabel("AI Provider")
        provider_layout.addWidget(provider_label)

        provider_input_layout = QHBoxLayout()
        provider_label2 = BodyLabel("Provider:")
        self.provider_combo = ComboBox()
        self.provider_combo.addItems(["openai", "anthropic", "claude", "ollama", "deepseek", "openrouter"])
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_input_layout.addWidget(provider_label2)
        provider_input_layout.addWidget(self.provider_combo, 1)
        provider_layout.addLayout(provider_input_layout)

        layout.addWidget(provider_group)

        # API Key settings
        api_key_group = CardWidget()
        api_key_layout = QVBoxLayout(api_key_group)

        api_key_label = StrongBodyLabel("API Key")
        api_key_layout.addWidget(api_key_label)

        # API Key input
        api_key_input_layout = QHBoxLayout()
        api_key_label2 = BodyLabel("API Key:")
        self.api_key_input = LineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("Enter your API key...")
        api_key_input_layout.addWidget(api_key_label2)
        api_key_input_layout.addWidget(self.api_key_input, 1)
        api_key_layout.addLayout(api_key_input_layout)

        # Show/Hide button
        self.api_key_show_btn = PushButton("Show")
        self.api_key_show_btn.setCheckable(True)
        self.api_key_show_btn.clicked.connect(self._toggle_api_key_visibility)
        api_key_layout.addWidget(self.api_key_show_btn)

        # Validate button
        self.validate_btn = PushButton("Validate API Key")
        self.validate_btn.clicked.connect(self._validate_api_key)
        api_key_layout.addWidget(self.validate_btn)

        # Validation result display
        self.validation_result = BodyLabel()
        self.validation_result.setWordWrap(True)
        api_key_layout.addWidget(self.validation_result)

        layout.addWidget(api_key_group)

        # Base URL settings
        base_url_group = CardWidget()
        base_url_layout = QVBoxLayout(base_url_group)

        base_url_label = StrongBodyLabel("Base URL (Optional)")
        base_url_layout.addWidget(base_url_label)

        base_url_input_layout = QHBoxLayout()
        base_url_label2 = BodyLabel("Base URL:")
        self.base_url_input = LineEdit()
        self.base_url_input.setPlaceholderText("e.g.: http://localhost:11434/v1")
        base_url_input_layout.addWidget(base_url_label2)
        base_url_input_layout.addWidget(self.base_url_input, 1)
        base_url_layout.addLayout(base_url_input_layout)

        layout.addWidget(base_url_group)

        # Model settings
        model_group = CardWidget()
        model_layout = QVBoxLayout(model_group)

        model_label = StrongBodyLabel("Model Settings")
        model_layout.addWidget(model_label)

        # Model name
        model_input_layout = QHBoxLayout()
        model_label2 = BodyLabel("Model Name:")
        self.model_input = LineEdit()
        self.model_input.setPlaceholderText("e.g.: gpt-4, claude-3-opus-20240229")
        model_input_layout.addWidget(model_label2)
        model_input_layout.addWidget(self.model_input, 1)
        model_layout.addLayout(model_input_layout)

        # Max Tokens - use dropdown for common presets
        max_tokens_layout = QHBoxLayout()
        max_tokens_label = BodyLabel("Max Tokens:")
        self.max_tokens_combo = ComboBox()
        # Common presets: display text -> actual value
        self.max_tokens_options = {
            "2K (2048)": 2048,
            "4K (4096)": 4096,
            "8K (8192)": 8192,
            "16K (16384)": 16384,
            "32K (32768)": 32768,
            "64K (65536)": 65536,
            "128K (131072)": 131072
        }
        self.max_tokens_combo.addItems(list(self.max_tokens_options.keys()))
        self.max_tokens_combo.setCurrentIndex(1)  # Default to 4K
        max_tokens_layout.addWidget(max_tokens_label)
        max_tokens_layout.addWidget(self.max_tokens_combo, 1)
        model_layout.addLayout(max_tokens_layout)

        # Temperature
        temp_layout = QHBoxLayout()
        temp_label = BodyLabel("Temperature:")
        self.temperature_input = SpinBox()
        self.temperature_input.setRange(0, 20)  # 0.0 - 2.0, stored as 0-20
        self.temperature_input.setValue(7)  # 0.7
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.temperature_input, 1)
        model_layout.addLayout(temp_layout)

        layout.addWidget(model_group)
        layout.addStretch()
        return widget

    def _create_analysis_tab(self) -> QWidget:
        """Create Code Analysis tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Analysis scope settings
        scope_group = CardWidget()
        scope_layout = QVBoxLayout(scope_group)

        scope_label = StrongBodyLabel("Analysis Scope")
        scope_layout.addWidget(scope_label)

        # Max depth
        depth_layout = QHBoxLayout()
        depth_label = BodyLabel("Max Depth:")
        self.max_depth_input = SpinBox()
        self.max_depth_input.setRange(1, 10)
        self.max_depth_input.setValue(3)
        depth_layout.addWidget(depth_label)
        depth_layout.addWidget(self.max_depth_input, 1)
        scope_layout.addLayout(depth_layout)

        # Max files
        files_layout = QHBoxLayout()
        files_label = BodyLabel("Max Files:")
        self.max_files_input = SpinBox()
        self.max_files_input.setRange(10, 1000)
        self.max_files_input.setValue(100)
        files_layout.addWidget(files_label)
        files_layout.addWidget(self.max_files_input, 1)
        scope_layout.addLayout(files_layout)

        layout.addWidget(scope_group)

        # File filter settings
        filter_group = CardWidget()
        filter_layout = QVBoxLayout(filter_group)

        filter_label = StrongBodyLabel("File Filters")
        filter_layout.addWidget(filter_label)

        self.exclude_patterns_input = TextEdit()
        self.exclude_patterns_input.setPlaceholderText(
            "One pattern per line, e.g.:\n"
            "*.log\n"
            "node_modules/*\n"
            "*.min.js"
        )
        self.exclude_patterns_input.setMaximumHeight(100)
        filter_layout.addWidget(self.exclude_patterns_input)

        layout.addWidget(filter_group)

        # Analysis options
        options_group = CardWidget()
        options_layout = QVBoxLayout(options_group)

        options_label = StrongBodyLabel("Analysis Options")
        options_layout.addWidget(options_label)

        self.include_comments_cb = CheckBox("Include Comments")
        self.include_comments_cb.setChecked(True)
        options_layout.addWidget(self.include_comments_cb)

        self.analyze_tests_cb = CheckBox("Analyze Test Files")
        self.analyze_tests_cb.setChecked(True)
        options_layout.addWidget(self.analyze_tests_cb)

        self.follow_imports_cb = CheckBox("Follow Imports")
        self.follow_imports_cb.setChecked(True)
        options_layout.addWidget(self.follow_imports_cb)

        layout.addWidget(options_group)
        layout.addStretch()
        return widget

    def _create_display_tab(self) -> QWidget:
        """Create Display Settings tab"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)

        # Theme settings
        theme_group = CardWidget()
        theme_layout = QVBoxLayout(theme_group)

        theme_label = StrongBodyLabel("Theme")
        theme_layout.addWidget(theme_label)

        theme_input_layout = QHBoxLayout()
        theme_label2 = BodyLabel("Theme Mode:")
        self.theme_combo = ComboBox()
        self.theme_combo.addItems(["light", "dark", "auto"])
        theme_input_layout.addWidget(theme_label2)
        theme_input_layout.addWidget(self.theme_combo, 1)
        theme_layout.addLayout(theme_input_layout)

        layout.addWidget(theme_group)

        # Font settings
        font_group = CardWidget()
        font_layout = QVBoxLayout(font_group)

        font_label = StrongBodyLabel("Font")
        font_layout.addWidget(font_label)

        # Font family
        font_family_layout = QHBoxLayout()
        font_family_label = BodyLabel("Font Family:")
        self.font_family_input = LineEdit()
        self.font_family_input.setPlaceholderText("e.g.: Consolas, Monaco")
        font_family_layout.addWidget(font_family_label)
        font_family_layout.addWidget(self.font_family_input, 1)
        font_layout.addLayout(font_family_layout)

        # Font size
        font_size_layout = QHBoxLayout()
        font_size_label = BodyLabel("Font Size:")
        self.font_size_input = SpinBox()
        self.font_size_input.setRange(8, 24)
        self.font_size_input.setValue(12)
        font_size_layout.addWidget(font_size_label)
        font_size_layout.addWidget(self.font_size_input, 1)
        font_layout.addLayout(font_size_layout)

        layout.addWidget(font_group)

        # Window settings
        window_group = CardWidget()
        window_layout = QVBoxLayout(window_group)

        window_label = StrongBodyLabel("Window")
        window_layout.addWidget(window_label)

        self.remember_size_cb = CheckBox("Remember Window Size")
        self.remember_size_cb.setChecked(True)
        window_layout.addWidget(self.remember_size_cb)

        self.remember_pos_cb = CheckBox("Remember Window Position")
        self.remember_pos_cb.setChecked(True)
        window_layout.addWidget(self.remember_pos_cb)

        layout.addWidget(window_group)
        layout.addStretch()
        return widget

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
            self.base_url_input.setText(defaults[provider]["base_url"])

    def _toggle_api_key_visibility(self, checked: bool):
        """Toggle API key visibility"""
        if checked:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
            self.api_key_show_btn.setText("Hide")
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)
            self.api_key_show_btn.setText("Show")

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
        api_key = self.api_key_input.text().strip()
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
                temperature=self.temperature_input.value() / 10.0
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

    def _get_max_tokens_value(self) -> int:
        """Get max tokens value from dropdown"""
        current_text = self.max_tokens_combo.currentText()
        return self.max_tokens_options.get(current_text, 4096)

    def _set_max_tokens_value(self, value: int):
        """Set dropdown option based on value"""
        # Find closest preset
        closest_text = "4K (4096)"
        min_diff = float('inf')

        for text, tokens in self.max_tokens_options.items():
            diff = abs(tokens - value)
            if diff < min_diff:
                min_diff = diff
                closest_text = text

        self.max_tokens_combo.setCurrentText(closest_text)

    def _load_settings(self):
        """Load settings from AppConfig object"""
        try:
            # Load API settings from AppConfig.ai
            ai_config = self.config.ai
            self.provider_combo.setCurrentText(ai_config.provider)
            self.api_key_input.setText(ai_config.api_key)
            self.base_url_input.setText(ai_config.base_url)
            self.model_input.setText(ai_config.model)
            self._set_max_tokens_value(ai_config.max_tokens)
            self.temperature_input.setValue(int(ai_config.temperature * 10))

            # Load display settings from AppConfig
            self.theme_combo.setCurrentText(self.config.theme)
            
            # For analysis settings, use defaults since they're not in AppConfig
            # These can be stored separately if needed
            self.max_depth_input.setValue(3)
            self.max_files_input.setValue(100)
            self.exclude_patterns_input.setPlainText("")
            self.include_comments_cb.setChecked(True)
            self.analyze_tests_cb.setChecked(True)
            self.follow_imports_cb.setChecked(True)
            
            # Font settings (use defaults for now)
            self.font_family_input.setText("")
            self.font_size_input.setValue(12)
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

            # Build settings dictionary
            settings = {
                "api": {
                    "provider": self.provider_combo.currentText(),
                    "api_key": self.api_key_input.text(),
                    "base_url": self.base_url_input.text(),
                    "model": self.model_input.text(),
                    "max_tokens": self._get_max_tokens_value(),
                    "temperature": self.temperature_input.value() / 10.0
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
                    "theme": self.theme_combo.currentText(),
                    "font_family": self.font_family_input.text(),
                    "font_size": self.font_size_input.value(),
                    "remember_size": self.remember_size_cb.isChecked(),
                    "remember_position": self.remember_pos_cb.isChecked()
                }
            }

            # Save to config file (同步操作，通常很快)
            config_service.update_config(settings)

            # Sync to Provider system in background thread (异步操作，避免卡死UI)
            provider = self.provider_combo.currentText()
            
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
