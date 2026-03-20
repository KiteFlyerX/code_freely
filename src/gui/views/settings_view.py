"""
设置视图
应用程序设置界面
"""
from typing import Optional, Dict, Any
from PySide6.QtCore import Qt, Signal
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
    StrongBodyLabel, SwitchButton
)

import os
import json
import asyncio

from ...services import config_service, provider_manager
from ...services.provider_service import ProviderConfig, ProviderType
from ...services.ai_client_factory import create_ai_client
from ...ai.base import Message, MessageRole, AIRequestConfig


class SettingsView(QWidget):
    """设置视图"""
    
    # 信号定义
    settings_changed = Signal()
    api_key_validated = Signal(bool, str)  # (is_valid, message)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.config = config_service.get_config()
        
        self._init_ui()
        self._load_settings()
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = StrongBodyLabel("设置")
        layout.addWidget(title)
        
        # 创建选项卡
        self.tabs = QTabWidget()
        
        # API设置选项卡
        api_tab = self._create_api_tab()
        self.tabs.addTab(api_tab, "API 设置")
        
        # 代码分析选项卡
        analysis_tab = self._create_analysis_tab()
        self.tabs.addTab(analysis_tab, "代码分析")
        
        # 显示设置选项卡
        display_tab = self._create_display_tab()
        self.tabs.addTab(display_tab, "显示")
        
        layout.addWidget(self.tabs)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.save_btn = PushButton("保存")
        self.save_btn.clicked.connect(self._save_settings)
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_api_tab(self) -> QWidget:
        """创建API设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # AI提供商选择
        provider_group = CardWidget()
        provider_layout = QVBoxLayout(provider_group)
        
        provider_label = StrongBodyLabel("AI 提供商")
        provider_layout.addWidget(provider_label)
        
        provider_input_layout = QHBoxLayout()
        provider_label2 = BodyLabel("提供商:")
        self.provider_combo = ComboBox()
        self.provider_combo.addItems(["openai", "anthropic", "claude", "ollama", "deepseek", "openrouter"])
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_input_layout.addWidget(provider_label2)
        provider_input_layout.addWidget(self.provider_combo, 1)
        provider_layout.addLayout(provider_input_layout)
        
        layout.addWidget(provider_group)
        
        # API密钥设置
        api_key_group = CardWidget()
        api_key_layout = QVBoxLayout(api_key_group)
        
        api_key_label = StrongBodyLabel("API 密钥")
        api_key_layout.addWidget(api_key_label)
        
        # API密钥输入
        api_key_input_layout = QHBoxLayout()
        api_key_label2 = BodyLabel("API 密钥:")
        self.api_key_input = LineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("输入您的 API 密钥...")
        api_key_input_layout.addWidget(api_key_label2)
        api_key_input_layout.addWidget(self.api_key_input, 1)
        api_key_layout.addLayout(api_key_input_layout)
        
        # 显示/隐藏按钮
        self.api_key_show_btn = PushButton("显示")
        self.api_key_show_btn.setCheckable(True)
        self.api_key_show_btn.clicked.connect(self._toggle_api_key_visibility)
        api_key_layout.addWidget(self.api_key_show_btn)
        
        # 验证按钮
        validate_btn = PushButton("验证 API 密钥")
        validate_btn.clicked.connect(self._validate_api_key)
        api_key_layout.addWidget(validate_btn)
        
        # 验证结果显示
        self.validation_result = BodyLabel()
        self.validation_result.setWordWrap(True)
        api_key_layout.addWidget(self.validation_result)
        
        layout.addWidget(api_key_group)
        
        # Base URL 设置
        base_url_group = CardWidget()
        base_url_layout = QVBoxLayout(base_url_group)
        
        base_url_label = StrongBodyLabel("Base URL (可选)")
        base_url_layout.addWidget(base_url_label)
        
        base_url_input_layout = QHBoxLayout()
        base_url_label2 = BodyLabel("Base URL:")
        self.base_url_input = LineEdit()
        self.base_url_input.setPlaceholderText("例如: http://localhost:11434/v1")
        base_url_input_layout.addWidget(base_url_label2)
        base_url_input_layout.addWidget(self.base_url_input, 1)
        base_url_layout.addLayout(base_url_input_layout)
        
        layout.addWidget(base_url_group)
        
        # 模型设置
        model_group = CardWidget()
        model_layout = QVBoxLayout(model_group)
        
        model_label = StrongBodyLabel("模型设置")
        model_layout.addWidget(model_label)
        
        # 模型名称
        model_input_layout = QHBoxLayout()
        model_label2 = BodyLabel("模型名称:")
        self.model_input = LineEdit()
        self.model_input.setPlaceholderText("例如: gpt-4, claude-3-opus-20240229")
        model_input_layout.addWidget(model_label2)
        model_input_layout.addWidget(self.model_input, 1)
        model_layout.addLayout(model_input_layout)
        
        # 最大Tokens - 使用下拉选择常用档位
        max_tokens_layout = QHBoxLayout()
        max_tokens_label = BodyLabel("最大 Tokens:")
        self.max_tokens_combo = ComboBox()
        # 常用档位：显示文本 -> 实际值
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
        self.max_tokens_combo.setCurrentIndex(1)  # 默认选中 4K
        max_tokens_layout.addWidget(max_tokens_label)
        max_tokens_layout.addWidget(self.max_tokens_combo, 1)
        model_layout.addLayout(max_tokens_layout)
        
        # 温度
        temp_layout = QHBoxLayout()
        temp_label = BodyLabel("温度:")
        self.temperature_input = SpinBox()
        self.temperature_input.setRange(0, 20)  # 0.0 - 2.0, 存储为0-20
        self.temperature_input.setValue(7)  # 0.7
        temp_layout.addWidget(temp_label)
        temp_layout.addWidget(self.temperature_input, 1)
        model_layout.addLayout(temp_layout)
        
        layout.addWidget(model_group)
        layout.addStretch()
        return widget
    
    def _create_analysis_tab(self) -> QWidget:
        """创建代码分析选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # 分析范围设置
        scope_group = CardWidget()
        scope_layout = QVBoxLayout(scope_group)
        
        scope_label = StrongBodyLabel("分析范围")
        scope_layout.addWidget(scope_label)
        
        # 最大深度
        depth_layout = QHBoxLayout()
        depth_label = BodyLabel("最大深度:")
        self.max_depth_input = SpinBox()
        self.max_depth_input.setRange(1, 10)
        self.max_depth_input.setValue(3)
        depth_layout.addWidget(depth_label)
        depth_layout.addWidget(self.max_depth_input, 1)
        scope_layout.addLayout(depth_layout)
        
        # 最大文件数
        files_layout = QHBoxLayout()
        files_label = BodyLabel("最大文件数:")
        self.max_files_input = SpinBox()
        self.max_files_input.setRange(10, 1000)
        self.max_files_input.setValue(100)
        files_layout.addWidget(files_label)
        files_layout.addWidget(self.max_files_input, 1)
        scope_layout.addLayout(files_layout)
        
        layout.addWidget(scope_group)
        
        # 文件过滤设置
        filter_group = CardWidget()
        filter_layout = QVBoxLayout(filter_group)
        
        filter_label = StrongBodyLabel("文件过滤")
        filter_layout.addWidget(filter_label)
        
        self.exclude_patterns_input = TextEdit()
        self.exclude_patterns_input.setPlaceholderText(
            "每行一个模式，例如:\n"
            "*.log\n"
            "node_modules/*\n"
            "*.min.js"
        )
        self.exclude_patterns_input.setMaximumHeight(100)
        filter_layout.addWidget(self.exclude_patterns_input)
        
        layout.addWidget(filter_group)
        
        # 分析选项
        options_group = CardWidget()
        options_layout = QVBoxLayout(options_group)
        
        options_label = StrongBodyLabel("分析选项")
        options_layout.addWidget(options_label)
        
        self.include_comments_cb = CheckBox("包含注释")
        self.include_comments_cb.setChecked(True)
        options_layout.addWidget(self.include_comments_cb)
        
        self.analyze_tests_cb = CheckBox("分析测试文件")
        self.analyze_tests_cb.setChecked(True)
        options_layout.addWidget(self.analyze_tests_cb)
        
        self.follow_imports_cb = CheckBox("跟随导入")
        self.follow_imports_cb.setChecked(True)
        options_layout.addWidget(self.follow_imports_cb)
        
        layout.addWidget(options_group)
        layout.addStretch()
        return widget
    
    def _create_display_tab(self) -> QWidget:
        """创建显示设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # 主题设置
        theme_group = CardWidget()
        theme_layout = QVBoxLayout(theme_group)
        
        theme_label = StrongBodyLabel("主题")
        theme_layout.addWidget(theme_label)
        
        theme_input_layout = QHBoxLayout()
        theme_label2 = BodyLabel("主题模式:")
        self.theme_combo = ComboBox()
        self.theme_combo.addItems(["light", "dark", "auto"])
        theme_input_layout.addWidget(theme_label2)
        theme_input_layout.addWidget(self.theme_combo, 1)
        theme_layout.addLayout(theme_input_layout)
        
        layout.addWidget(theme_group)
        
        # 字体设置
        font_group = CardWidget()
        font_layout = QVBoxLayout(font_group)
        
        font_label = StrongBodyLabel("字体")
        font_layout.addWidget(font_label)
        
        # 字体家族
        font_family_layout = QHBoxLayout()
        font_family_label = BodyLabel("字体家族:")
        self.font_family_input = LineEdit()
        self.font_family_input.setPlaceholderText("例如: Consolas, Monaco")
        font_family_layout.addWidget(font_family_label)
        font_family_layout.addWidget(self.font_family_input, 1)
        font_layout.addLayout(font_family_layout)
        
        # 字体大小
        font_size_layout = QHBoxLayout()
        font_size_label = BodyLabel("字体大小:")
        self.font_size_input = SpinBox()
        self.font_size_input.setRange(8, 24)
        self.font_size_input.setValue(12)
        font_size_layout.addWidget(font_size_label)
        font_size_layout.addWidget(self.font_size_input, 1)
        font_layout.addLayout(font_size_layout)
        
        layout.addWidget(font_group)
        
        # 窗口设置
        window_group = CardWidget()
        window_layout = QVBoxLayout(window_group)
        
        window_label = StrongBodyLabel("窗口")
        window_layout.addWidget(window_label)
        
        self.remember_size_cb = CheckBox("记住窗口大小")
        self.remember_size_cb.setChecked(True)
        window_layout.addWidget(self.remember_size_cb)
        
        self.remember_pos_cb = CheckBox("记住窗口位置")
        self.remember_pos_cb.setChecked(True)
        window_layout.addWidget(self.remember_pos_cb)
        
        layout.addWidget(window_group)
        layout.addStretch()
        return widget
    
    def _on_provider_changed(self, provider: str):
        """提供商改变时的处理"""
        # 根据提供商设置默认值
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
        """切换 API 密钥可见性"""
        if checked:
            self.api_key_input.setEchoMode(QLineEdit.Normal)
            self.api_key_show_btn.setText("隐藏")
        else:
            self.api_key_input.setEchoMode(QLineEdit.Password)
            self.api_key_show_btn.setText("显示")
    
    def _get_provider_type(self, provider: str) -> ProviderType:
        """将提供商字符串转换为 ProviderType"""
        provider_map = {
            "claude": ProviderType.CLAUDE,
            "anthropic": ProviderType.CLAUDE,
            "openai": ProviderType.OPENAI,
            "deepseek": ProviderType.DEEPSEEK,
            "ollama": ProviderType.CUSTOM,
            "openrouter": ProviderType.CUSTOM
        }
        return provider_map.get(provider.lower(), ProviderType.CUSTOM)
    
    async def _async_validate_api_key(self, client) -> tuple[bool, str]:
        """异步验证 API 密钥"""
        try:
            # 构建测试消息
            messages = [
                Message(role=MessageRole.USER, content="Hello")
            ]
            
            # 构建请求配置
            config = AIRequestConfig(
                max_tokens=10,
                temperature=0.5
            )
            
            # 发送聊天请求
            response = await client.chat(messages, config)
            
            if response and response.content:
                return True, "API 密钥验证成功"
            else:
                return False, "API 返回空响应"
                
        except Exception as e:
            error_msg = str(e)
            # 提取关键错误信息
            if "AuthenticationError" in error_msg or "401" in error_msg:
                return False, "API 密钥无效"
            elif "Connection" in error_msg or "Timeout" in error_msg:
                return False, "网络连接失败"
            else:
                return False, f"验证失败: {error_msg}"
    
    def _validate_api_key(self):
        """验证 API 密钥"""
        api_key = self.api_key_input.text().strip()
        provider = self.provider_combo.currentText()
        base_url = self.base_url_input.text().strip()
        model = self.model_input.text().strip()
        
        if not api_key:
            self.validation_result.setText("❌ 请输入 API 密钥")
            InfoBar.error(
                title="验证失败",
                content="请输入 API 密钥",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
        
        if not model:
            self.validation_result.setText("❌ 请输入模型名称")
            InfoBar.error(
                title="验证失败",
                content="请输入模型名称",
                parent=self,
                position=InfoBarPosition.TOP
            )
            return
        
        self.validation_result.setText("⏳ 正在验证...")
        
        try:
            # 构建 ProviderConfig
            provider_type = self._get_provider_type(provider)
            
            config = ProviderConfig(
                id="temp_validation",
                name=f"{provider} (验证)",
                provider_type=provider_type,
                api_key=api_key,
                api_endpoint=base_url,
                model=model,
                max_tokens=10,  # 验证时使用很小的值
                temperature=self.temperature_input.value() / 10.0
            )
            
            # 使用工厂创建客户端
            client = create_ai_client(config)
            
            # 运行异步验证
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                is_valid, message = loop.run_until_complete(self._async_validate_api_key(client))
                
                if is_valid:
                    self.validation_result.setText("✅ " + message)
                    InfoBar.success(
                        title="验证成功",
                        content=message,
                        parent=self,
                        position=InfoBarPosition.TOP
                    )
                    self.api_key_validated.emit(True, message)
                else:
                    self.validation_result.setText("❌ " + message)
                    InfoBar.error(
                        title="验证失败",
                        content=message,
                        parent=self,
                        position=InfoBarPosition.TOP
                    )
                    self.api_key_validated.emit(False, message)
            finally:
                loop.close()
                
        except Exception as e:
            error_msg = f"初始化失败: {str(e)}"
            self.validation_result.setText(f"❌ {error_msg}")
            InfoBar.error(
                title="初始化失败",
                content=str(e),
                parent=self,
                position=InfoBarPosition.TOP
            )
            self.api_key_validated.emit(False, error_msg)
    
    def _get_max_tokens_value(self) -> int:
        """从下拉框获取最大 Tokens 值"""
        current_text = self.max_tokens_combo.currentText()
        return self.max_tokens_options.get(current_text, 4096)
    
    def _set_max_tokens_value(self, value: int):
        """根据值设置下拉框选项"""
        # 找到最接近的档位
        closest_text = "4K (4096)"
        min_diff = float('inf')
        
        for text, tokens in self.max_tokens_options.items():
            diff = abs(tokens - value)
            if diff < min_diff:
                min_diff = diff
                closest_text = text
        
        self.max_tokens_combo.setCurrentText(closest_text)
    
    def _load_settings(self):
        """加载设置"""
        try:
            # 加载API设置
            api_config = self.config.get("api", {})
            self.provider_combo.setCurrentText(api_config.get("provider", "openai"))
            self.api_key_input.setText(api_config.get("api_key", ""))
            self.base_url_input.setText(api_config.get("base_url", ""))
            self.model_input.setText(api_config.get("model", ""))
            
            if "max_tokens" in api_config:
                self._set_max_tokens_value(api_config["max_tokens"])
            if "temperature" in api_config:
                # 转换为整数存储 (0.7 -> 7)
                self.temperature_input.setValue(int(api_config["temperature"] * 10))
            
            # 加载分析设置
            analysis_config = self.config.get("analysis", {})
            if "max_depth" in analysis_config:
                self.max_depth_input.setValue(analysis_config["max_depth"])
            if "max_files" in analysis_config:
                self.max_files_input.setValue(analysis_config["max_files"])
            
            exclude_patterns = analysis_config.get("exclude_patterns", [])
            self.exclude_patterns_input.setPlainText("\n".join(exclude_patterns))
            
            self.include_comments_cb.setChecked(analysis_config.get("include_comments", True))
            self.analyze_tests_cb.setChecked(analysis_config.get("analyze_tests", True))
            self.follow_imports_cb.setChecked(analysis_config.get("follow_imports", True))
            
            # 加载显示设置
            display_config = self.config.get("display", {})
            self.theme_combo.setCurrentText(display_config.get("theme", "light"))
            self.font_family_input.setText(display_config.get("font_family", ""))
            
            if "font_size" in display_config:
                self.font_size_input.setValue(display_config["font_size"])
            
            self.remember_size_cb.setChecked(display_config.get("remember_size", True))
            self.remember_pos_cb.setChecked(display_config.get("remember_position", True))
            
        except Exception as e:
            InfoBar.error(
                title="加载失败",
                content=f"加载设置时出错: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP
            )
    
    def _sync_to_provider_system(self, settings: dict):
        """同步设置到 Provider 系统"""
        try:
            api_config = settings.get("api", {})
            provider = api_config.get("provider", "openai")
            api_key = api_config.get("api_key", "")
            base_url = api_config.get("base_url", "")
            model = api_config.get("model", "")
            max_tokens = api_config.get("max_tokens", 4096)
            temperature = api_config.get("temperature", 0.7)
            
            # 如果没有 API 密钥，不更新 Provider 系统
            if not api_key:
                return
            
            # 获取或创建默认 Provider
            provider_type = self._get_provider_type(provider)
            
            # 尝试获取现有的默认 provider
            existing_providers = provider_manager.list_providers()
            default_provider = None
            
            for p in existing_providers:
                if p.is_default:
                    default_provider = p
                    break
            
            # 构建 ProviderConfig
            provider_config = ProviderConfig(
                id=default_provider.id if default_provider else "default",
                name=f"{provider.upper()} (默认)",
                provider_type=provider_type,
                api_key=api_key,
                api_endpoint=base_url if base_url else None,
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                is_default=True
            )
            
            # 更新或创建 Provider
            if default_provider:
                provider_manager.update_provider(provider_config.id, provider_config)
                print(f"✅ 已更新默认 Provider: {provider_config.id}")
            else:
                provider_manager.add_provider(provider_config)
                print(f"✅ 已创建默认 Provider: {provider_config.id}")
            
            # 重新加载 Provider 以确保更改生效
            provider_manager.reload_providers()
            
        except Exception as e:
            print(f"⚠️ 同步到 Provider 系统失败: {str(e)}")
            # 不抛出异常，避免影响主流程
    
    def _save_settings(self):
        """保存设置"""
        try:
            # 构建设置字典
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
            
            # 保存到配置文件
            config_service.update_config(settings)
            
            # 🔥 关键修复：同步更新到 Provider 系统
            self._sync_to_provider_system(settings)
            
            # 发送设置变更事件
            self.settings_changed.emit()
            
            # 显示成功消息
            InfoBar.success(
                title="保存成功",
                content="设置已保存，AI 配置已同步更新。",
                parent=self,
                position=InfoBarPosition.TOP
            )
            
        except Exception as e:
            InfoBar.error(
                title="保存失败",
                content=f"保存设置时出错: {str(e)}",
                parent=self,
                position=InfoBarPosition.TOP
            )
