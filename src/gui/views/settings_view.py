from src.gui.styles import COLORS, FONTS
from src.services.conversation_service import ConversationService
from src.services.ai_client_factory import AIClientFactory
from src.services.ai_client_interface import AIClientInterface
from src.utils.logger import Logger
from src.utils.config_manager import ConfigManager
from src.utils.event_bus import EventBus, EventType

try:
    from PyQt5.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QLineEdit, QComboBox, QSpinBox,
        QTextEdit, QTabWidget, QFileDialog, QMessageBox,
        QGroupBox, QFormLayout, QCheckBox, QDoubleSpinBox
    )
    from PyQt5.QtCore import Qt, pyqtSignal
    from PyQt5.QtGui import QFont
except ImportError:
    from PyQt6.QtWidgets import (
        QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
        QPushButton, QLineEdit, QComboBox, QSpinBox,
        QTextEdit, QTabWidget, QFileDialog, QMessageBox,
        QGroupBox, QFormLayout, QCheckBox, QDoubleSpinBox
    )
    from PyQt6.QtCore import Qt, pyqtSignal
    from PyQt6.QtGui import QFont

import os
import json


class SettingsView(QWidget):
    """设置视图"""
    
    # 信号定义
    settings_changed = pyqtSignal()
    api_key_validated = pyqtSignal(bool, str)  # (is_valid, message)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = Logger.get_logger()
        self.config = ConfigManager.get_config()
        self.event_bus = EventBus.get_instance()
        
        self._init_ui()
        self._load_settings()
        
        # 监听设置变更事件
        self.event_bus.subscribe(EventType.CONFIG_UPDATED.value, self._on_config_updated)
    
    def _init_ui(self):
        """初始化UI"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(20, 20, 20, 20)
        layout.setSpacing(15)
        
        # 标题
        title = QLabel("设置")
        title.setFont(FONTS['title'])
        title.setStyleSheet(f"color: {COLORS['text']};")
        layout.addWidget(title)
        
        # 创建选项卡
        tabs = QTabWidget()
        tabs.setStyleSheet(self._get_tab_style())
        
        # API设置选项卡
        api_tab = self._create_api_tab()
        tabs.addTab(api_tab, "API 设置")
        
        # 代码分析选项卡
        analysis_tab = self._create_analysis_tab()
        tabs.addTab(analysis_tab, "代码分析")
        
        # 显示设置选项卡
        display_tab = self._create_display_tab()
        tabs.addTab(display_tab, "显示")
        
        # 日志选项卡
        log_tab = self._create_log_tab()
        tabs.addTab(log_tab, "日志")
        
        layout.addWidget(tabs)
        
        # 底部按钮
        btn_layout = QHBoxLayout()
        btn_layout.addStretch()
        
        self.save_btn = QPushButton("保存")
        self.save_btn.clicked.connect(self._save_settings)
        self.save_btn.setStyleSheet(self._get_button_style())
        btn_layout.addWidget(self.save_btn)
        
        layout.addLayout(btn_layout)
    
    def _create_api_tab(self) -> QWidget:
        """创建API设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # AI提供商选择
        provider_group = QGroupBox("AI 提供商")
        provider_layout = QFormLayout()
        
        self.provider_combo = QComboBox()
        self.provider_combo.addItems(["openai", "anthropic", "ollama", "deepseek", "openrouter"])
        self.provider_combo.currentTextChanged.connect(self._on_provider_changed)
        provider_layout.addRow("提供商:", self.provider_combo)
        
        provider_group.setLayout(provider_layout)
        layout.addWidget(provider_group)
        
        # API密钥设置
        api_key_group = QGroupBox("API 密钥")
        api_key_layout = QFormLayout()
        
        self.api_key_input = QLineEdit()
        self.api_key_input.setEchoMode(QLineEdit.Password)
        self.api_key_input.setPlaceholderText("输入您的 API 密钥...")
        api_key_layout.addRow("API 密钥:", self.api_key_input)
        
        self.api_key_show_btn = QPushButton("显示")
        self.api_key_show_btn.setCheckable(True)
        self.api_key_show_btn.clicked.connect(self._toggle_api_key_visibility)
        api_key_layout.addRow("", self.api_key_show_btn)
        
        # 验证按钮
        validate_btn = QPushButton("验证 API 密钥")
        validate_btn.clicked.connect(self._validate_api_key)
        api_key_layout.addRow("", validate_btn)
        
        # 验证结果显示
        self.validation_result = QLabel()
        self.validation_result.setWordWrap(True)
        self.validation_result.setStyleSheet("padding: 5px;")
        api_key_layout.addRow("", self.validation_result)
        
        api_key_group.setLayout(api_key_layout)
        layout.addWidget(api_key_group)
        
        # Base URL 设置（用于 Ollama 或自定义端点）
        base_url_group = QGroupBox("Base URL (可选)")
        base_url_layout = QFormLayout()
        
        self.base_url_input = QLineEdit()
        self.base_url_input.setPlaceholderText("例如: http://localhost:11434/v1")
        base_url_layout.addRow("Base URL:", self.base_url_input)
        
        base_url_group.setLayout(base_url_layout)
        layout.addWidget(base_url_group)
        
        # 模型设置
        model_group = QGroupBox("模型设置")
        model_layout = QFormLayout()
        
        self.model_input = QLineEdit()
        self.model_input.setPlaceholderText("例如: gpt-4, claude-3-opus-20240229")
        model_layout.addRow("模型名称:", self.model_input)
        
        self.max_tokens_input = QSpinBox()
        self.max_tokens_input.setRange(100, 128000)
        self.max_tokens_input.setValue(4096)
        self.max_tokens_input.setSuffix(" tokens")
        model_layout.addRow("最大 Tokens:", self.max_tokens_input)
        
        self.temperature_input = QDoubleSpinBox()
        self.temperature_input.setRange(0.0, 2.0)
        self.temperature_input.setSingleStep(0.1)
        self.temperature_input.setValue(0.7)
        model_layout.addRow("温度:", self.temperature_input)
        
        model_group.setLayout(model_layout)
        layout.addWidget(model_group)
        
        layout.addStretch()
        return widget
    
    def _create_analysis_tab(self) -> QWidget:
        """创建代码分析选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # 分析范围设置
        scope_group = QGroupBox("分析范围")
        scope_layout = QFormLayout()
        
        self.max_depth_input = QSpinBox()
        self.max_depth_input.setRange(1, 10)
        self.max_depth_input.setValue(3)
        scope_layout.addRow("最大深度:", self.max_depth_input)
        
        self.max_files_input = QSpinBox()
        self.max_files_input.setRange(10, 1000)
        self.max_files_input.setValue(100)
        scope_layout.addRow("最大文件数:", self.max_files_input)
        
        scope_group.setLayout(scope_layout)
        layout.addWidget(scope_group)
        
        # 文件过滤设置
        filter_group = QGroupBox("文件过滤")
        filter_layout = QVBoxLayout()
        
        self.exclude_patterns_input = QTextEdit()
        self.exclude_patterns_input.setPlaceholderText(
            "每行一个模式，例如:\n"
            "*.log\n"
            "node_modules/*\n"
            "*.min.js"
        )
        self.exclude_patterns_input.setMaximumHeight(100)
        filter_layout.addWidget(QLabel("排除模式:"))
        filter_layout.addWidget(self.exclude_patterns_input)
        
        filter_group.setLayout(filter_layout)
        layout.addWidget(filter_group)
        
        # 分析选项
        options_group = QGroupBox("分析选项")
        options_layout = QVBoxLayout()
        
        self.include_comments_cb = QCheckBox("包含注释")
        self.include_comments_cb.setChecked(True)
        options_layout.addWidget(self.include_comments_cb)
        
        self.analyze_tests_cb = QCheckBox("分析测试文件")
        self.analyze_tests_cb.setChecked(True)
        options_layout.addWidget(self.analyze_tests_cb)
        
        self.follow_imports_cb = QCheckBox("跟随导入")
        self.follow_imports_cb.setChecked(True)
        options_layout.addWidget(self.follow_imports_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
        layout.addStretch()
        return widget
    
    def _create_display_tab(self) -> QWidget:
        """创建显示设置选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # 主题设置
        theme_group = QGroupBox("主题")
        theme_layout = QFormLayout()
        
        self.theme_combo = QComboBox()
        self.theme_combo.addItems(["light", "dark", "auto"])
        theme_layout.addRow("主题模式:", self.theme_combo)
        
        theme_group.setLayout(theme_layout)
        layout.addWidget(theme_group)
        
        # 字体设置
        font_group = QGroupBox("字体")
        font_layout = QFormLayout()
        
        self.font_family_input = QLineEdit()
        self.font_family_input.setPlaceholderText("例如: Consolas, Monaco")
        font_layout.addRow("字体家族:", self.font_family_input)
        
        self.font_size_input = QSpinBox()
        self.font_size_input.setRange(8, 24)
        self.font_size_input.setValue(12)
        font_layout.addRow("字体大小:", self.font_size_input)
        
        font_group.setLayout(font_layout)
        layout.addWidget(font_group)
        
        # 窗口设置
        window_group = QGroupBox("窗口")
        window_layout = QVBoxLayout()
        
        self.remember_size_cb = QCheckBox("记住窗口大小")
        self.remember_size_cb.setChecked(True)
        window_layout.addWidget(self.remember_size_cb)
        
        self.remember_pos_cb = QCheckBox("记住窗口位置")
        self.remember_pos_cb.setChecked(True)
        window_layout.addWidget(self.remember_pos_cb)
        
        window_group.setLayout(window_layout)
        layout.addWidget(window_group)
        
        layout.addStretch()
        return widget
    
    def _create_log_tab(self) -> QWidget:
        """创建日志选项卡"""
        widget = QWidget()
        layout = QVBoxLayout(widget)
        layout.setSpacing(15)
        
        # 日志级别设置
        level_group = QGroupBox("日志级别")
        level_layout = QFormLayout()
        
        self.log_level_combo = QComboBox()
        self.log_level_combo.addItems(["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"])
        level_layout.addRow("日志级别:", self.log_level_combo)
        
        level_group.setLayout(level_layout)
        layout.addWidget(level_group)
        
        # 日志文件设置
        file_group = QGroupBox("日志文件")
        file_layout = QFormLayout()
        
        self.log_file_input = QLineEdit()
        file_layout.addRow("日志文件路径:", self.log_file_input)
        
        browse_btn = QPushButton("浏览...")
        browse_btn.clicked.connect(self._browse_log_file)
        file_layout.addRow("", browse_btn)
        
        self.max_log_size_input = QSpinBox()
        self.max_log_size_input.setRange(1, 100)
        self.max_log_size_input.setValue(10)
        self.max_log_size_input.setSuffix(" MB")
        file_layout.addRow("最大文件大小:", self.max_log_size_input)
        
        file_group.setLayout(file_layout)
        layout.addWidget(file_group)
        
        # 日志选项
        options_group = QGroupBox("日志选项")
        options_layout = QVBoxLayout()
        
        self.log_to_console_cb = QCheckBox("输出到控制台")
        self.log_to_console_cb.setChecked(True)
        options_layout.addWidget(self.log_to_console_cb)
        
        self.log_to_file_cb = QCheckBox("输出到文件")
        self.log_to_file_cb.setChecked(True)
        options_layout.addWidget(self.log_to_file_cb)
        
        self.include_timestamp_cb = QCheckBox("包含时间戳")
        self.include_timestamp_cb.setChecked(True)
        options_layout.addWidget(self.include_timestamp_cb)
        
        options_group.setLayout(options_layout)
        layout.addWidget(options_group)
        
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
    
    def _validate_api_key(self):
        """验证 API 密钥"""
        api_key = self.api_key_input.text().strip()
        provider = self.provider_combo.currentText()
        base_url = self.base_url_input.text().strip()
        
        if not api_key:
            self.validation_result.setText("❌ 请输入 API 密钥")
            self.validation_result.setStyleSheet(f"color: {COLORS['error']}; padding: 5px;")
            return
        
        self.validation_result.setText("⏳ 正在验证...")
        self.validation_result.setStyleSheet(f"color: {COLORS['warning']}; padding: 5px;")
        
        # 创建临时客户端进行验证
        try:
            from src.services.openai_client import OpenAIClient
            from src.services.anthropic_client import AnthropicClient
            from src.services.ollama_client import OllamaClient
            from src.services.deepseek_client import DeepSeekClient
            from src.services.openrouter_client import OpenRouterClient
            
            client_classes = {
                "openai": OpenAIClient,
                "anthropic": AnthropicClient,
                "ollama": OllamaClient,
                "deepseek": DeepSeekClient,
                "openrouter": OpenRouterClient
            }
            
            client_class = client_classes.get(provider)
            if not client_class:
                raise ValueError(f"不支持的提供商: {provider}")
            
            # 创建临时客户端配置
            temp_config = {
                "api_key": api_key,
                "model": self.model_input.text().strip() or "test",
                "max_tokens": 10,
                "temperature": 0.7
            }
            
            if base_url:
                temp_config["base_url"] = base_url
            
            # 创建临时客户端
            temp_client = client_class(temp_config)
            
            # 尝试发送测试请求
            try:
                # 发送一个简单的测试请求
                response = temp_client.send_message("Hello", [])
                
                if response and response.get("success"):
                    self.validation_result.setText("✅ API 密钥验证成功")
                    self.validation_result.setStyleSheet(f"color: {COLORS['success']}; padding: 5px;")
                    self.api_key_validated.emit(True, "API 密钥验证成功")
                    self.logger.info(f"API 密钥验证成功: {provider}")
                else:
                    error_msg = response.get("error", "未知错误") if response else "无响应"
                    self.validation_result.setText(f"❌ 验证失败: {error_msg}")
                    self.validation_result.setStyleSheet(f"color: {COLORS['error']}; padding: 5px;")
                    self.api_key_validated.emit(False, f"验证失败: {error_msg}")
                    self.logger.error(f"API 密钥验证失败: {provider} - {error_msg}")
            except Exception as e:
                self.validation_result.setText(f"❌ 验证失败: {str(e)}")
                self.validation_result.setStyleSheet(f"color: {COLORS['error']}; padding: 5px;")
                self.api_key_validated.emit(False, f"验证失败: {str(e)}")
                self.logger.error(f"API 密钥验证异常: {provider} - {str(e)}")
                
        except Exception as e:
            self.validation_result.setText(f"❌ 初始化失败: {str(e)}")
            self.validation_result.setStyleSheet(f"color: {COLORS['error']}; padding: 5px;")
            self.api_key_validated.emit(False, f"初始化失败: {str(e)}")
            self.logger.error(f"创建 AI 客户端失败: {str(e)}")
    
    def _browse_log_file(self):
        """浏览日志文件"""
        file_path, _ = QFileDialog.getSaveFileName(
            self,
            "选择日志文件",
            os.path.expanduser("~/codetrace.log"),
            "Log Files (*.log);;All Files (*)"
        )
        if file_path:
            self.log_file_input.setText(file_path)
    
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
                self.max_tokens_input.setValue(api_config["max_tokens"])
            if "temperature" in api_config:
                self.temperature_input.setValue(api_config["temperature"])
            
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
            
            # 加载日志设置
            log_config = self.config.get("logging", {})
            self.log_level_combo.setCurrentText(log_config.get("level", "INFO"))
            self.log_file_input.setText(log_config.get("file", ""))
            
            if "max_size_mb" in log_config:
                self.max_log_size_input.setValue(log_config["max_size_mb"])
            
            self.log_to_console_cb.setChecked(log_config.get("console", True))
            self.log_to_file_cb.setChecked(log_config.get("file_enabled", True))
            self.include_timestamp_cb.setChecked(log_config.get("timestamp", True))
            
            self.logger.info("设置加载成功")
            
        except Exception as e:
            self.logger.error(f"加载设置失败: {str(e)}")
            QMessageBox.warning(self, "加载失败", f"加载设置时出错:\n{str(e)}")
    
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
                    "max_tokens": self.max_tokens_input.value(),
                    "temperature": self.temperature_input.value()
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
                },
                "logging": {
                    "level": self.log_level_combo.currentText(),
                    "file": self.log_file_input.text(),
                    "max_size_mb": self.max_log_size_input.value(),
                    "console": self.log_to_console_cb.isChecked(),
                    "file_enabled": self.log_to_file_cb.isChecked(),
                    "timestamp": self.include_timestamp_cb.isChecked()
                }
            }
            
            # 保存到配置文件
            ConfigManager.update_config(settings)
            
            # 发送设置变更事件
            self.settings_changed.emit()
            
            # 显示成功消息
            QMessageBox.information(self, "保存成功", "设置已保存，部分设置可能需要重启应用后生效。")
            
            self.logger.info("设置保存成功")
            
        except Exception as e:
            self.logger.error(f"保存设置失败: {str(e)}")
            QMessageBox.critical(self, "保存失败", f"保存设置时出错:\n{str(e)}")
    
    def _on_config_updated(self, event_data):
        """配置更新事件处理"""
        self._load_settings()
    
    def _get_tab_style(self) -> str:
        """获取选项卡样式"""
        return f"""
            QTabWidget::pane {{
                border: 1px solid {COLORS['border']};
                background: {COLORS['background']};
            }}
            QTabBar::tab {{
                background: {COLORS['secondary']};
                color: {COLORS['text']};
                padding: 8px 16px;
                border: 1px solid {COLORS['border']};
                border-bottom: none;
            }}
            QTabBar::tab:selected {{
                background: {COLORS['background']};
                border-bottom: 2px solid {COLORS['accent']};
            }}
            QTabBar::tab:hover {{
                background: {COLORS['hover']};
            }}
        """
    
    def _get_button_style(self) -> str:
        """获取按钮样式"""
        return f"""
            QPushButton {{
                background: {COLORS['accent']};
                color: white;
                border: none;
                padding: 8px 16px;
                border-radius: 4px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background: {COLORS['hover']};
            }}
            QPushButton:pressed {{
                background: {COLORS['active']};
            }}
        """
