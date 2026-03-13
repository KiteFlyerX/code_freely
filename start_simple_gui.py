"""
CodeTraceAI GUI - 简化工作版本
基于成功运行的 test_minimal_gui.py 构建
"""
import sys
import os
import subprocess
from pathlib import Path

# 设置路径
script_dir = Path(__file__).parent.absolute()
os.chdir(script_dir)
sys.path.insert(0, str(script_dir))

# 创建应用
from PySide6.QtWidgets import (
    QApplication, QMainWindow, QWidget, QVBoxLayout,
    QHBoxLayout, QLabel, QPushButton, QTextEdit,
    QTabWidget, QTableWidget, QTableWidgetItem,
    QHeaderView, QListWidget, QStackedWidget,
    QInputDialog, QMessageBox, QLineEdit, QFileDialog, QSplitter, QStatusBar
)
from PySide6.QtCore import Qt

# 导入服务模块（这些不涉及 Qt）
try:
    from src.database import init_database
    from src.services import (
        config_service, conversation_service,
        provider_manager, PROVIDER_PRESETS, ProviderConfig, ProviderType
    )
    from src.services.bug_service import bug_service, BugCreateInfo
    from src.services.knowledge_service import knowledge_service, KnowledgeCreateInfo
    init_database()
    print("Services loaded successfully")
except Exception as e:
    print(f"Warning: Some services failed to load: {e}")

# 简化的主窗口
class CodeTraceAIWindow(QMainWindow):
    """简化的主窗口"""

    def __init__(self):
        super().__init__()
        self.setWindowTitle("CodeTraceAI - AI 编程辅助与知识沉淀工具")
        self.setMinimumSize(1000, 700)

        # 当前工作目录
        self.current_work_dir = Path.cwd()

        # 活跃的线程列表
        self._active_threads = []

        # 创建中心部件
        central_widget = QWidget()
        self.setCentralWidget(central_widget)

        # 主布局
        main_layout = QHBoxLayout(central_widget)

        # 左侧导航
        nav_list = QListWidget()
        nav_list.addItems([
            "AI 对话",
            "修改历史",
            "Bug 追踪",
            "知识库",
            "提供商管理",
            "设置"
        ])
        nav_list.setMaximumWidth(150)
        nav_list.currentRowChanged.connect(self.show_page)

        # 右侧内容区
        self.content_stack = QStackedWidget()
        self.pages = {}

        # 创建各个页面
        self.create_chat_page()
        self.create_history_page()
        self.create_bug_page()
        self.create_knowledge_page()
        self.create_provider_page()
        self.create_settings_page()

        # 添加到布局
        main_layout.addWidget(nav_list)
        main_layout.addWidget(self.content_stack)

        # 创建状态栏显示工作目录
        self.statusBar = QStatusBar()
        self.setStatusBar(self.statusBar)
        self._update_work_dir_display()

        # 添加切换目录按钮到状态栏
        change_dir_btn = QPushButton("切换目录")
        change_dir_btn.setMaximumWidth(80)
        change_dir_btn.clicked.connect(self._change_work_directory)
        self.statusBar.addPermanentWidget(change_dir_btn)

    def _update_work_dir_display(self):
        """更新工作目录显示"""
        try:
            # 显示相对路径（如果可能）
            from pathlib import Path
            cwd = Path.cwd()
            home = Path.home()

            if cwd.is_relative_to(home):
                # 显示为 ~/path 格式
                display_path = f"~/{cwd.relative_to(home)}"
            else:
                display_path = str(cwd)

            # 限制显示长度
            if len(display_path) > 50:
                display_path = "..." + display_path[-47:]

            self.statusBar.showMessage(f"工作目录: {display_path}")
        except Exception as e:
            self.statusBar.showMessage(f"工作目录: {str(self.current_work_dir)}")

        # 同时更新聊天页面的显示
        self._update_chat_work_dir_display()

    def _update_chat_work_dir_display(self):
        """更新聊天页面的工作目录显示"""
        try:
            if hasattr(self, 'chat_work_dir_label'):
                from pathlib import Path
                cwd = Path.cwd()
                home = Path.home()

                if cwd.is_relative_to(home):
                    display_path = f"~/{cwd.relative_to(home)}"
                else:
                    display_path = str(cwd)

                # 限制显示长度
                if len(display_path) > 35:
                    display_path = "..." + display_path[-32:]

                self.chat_work_dir_label.setText(f"📁 {display_path}")
                self.chat_work_dir_label.setToolTip(str(cwd))
        except Exception:
            pass

    def _change_work_directory(self):
        """切换工作目录"""
        from pathlib import Path

        # 使用文件对话框选择目录
        new_dir = QFileDialog.getExistingDirectory(
            self,
            "选择工作目录",
            str(self.current_work_dir)
        )

        if new_dir:
            try:
                new_path = Path(new_dir)
                os.chdir(new_path)
                self.current_work_dir = new_path

                self._update_work_dir_display()

                QMessageBox.information(
                    self,
                    "目录已切换",
                    f"工作目录已切换到:\n{new_path}"
                )
            except Exception as e:
                QMessageBox.warning(
                    self,
                    "切换失败",
                    f"无法切换到目录 {new_dir}:\n{str(e)}"
                )

    def create_chat_page(self):
        """创建聊天页面"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # 顶部工具栏
        toolbar = QHBoxLayout()
        toolbar.addWidget(QLabel("AI 对话"))

        # 工作目录显示
        toolbar.addWidget(QLabel("|"))
        self.chat_work_dir_label = QLabel()
        self.chat_work_dir_label.setStyleSheet("color: #666; font-size: 10px;")
        self.chat_work_dir_label.setMaximumWidth(300)
        self.chat_work_dir_label.setToolTip("当前工作目录")
        toolbar.addWidget(self.chat_work_dir_label)

        change_dir_small_btn = QPushButton("📁")
        change_dir_small_btn.setMaximumWidth(30)
        change_dir_small_btn.setToolTip("切换工作目录")
        change_dir_small_btn.clicked.connect(self._change_work_directory)
        toolbar.addWidget(change_dir_small_btn)

        # 提供商状态
        toolbar.addWidget(QLabel("|"))
        self.chat_status_label = QLabel("未配置提供商")
        self.chat_status_label.setStyleSheet("color: orange; font-size: 11px;")
        toolbar.addWidget(self.chat_status_label)

        toolbar.addStretch()

        new_btn = QPushButton("新建对话")
        new_btn.clicked.connect(self._on_new_chat)
        toolbar.addWidget(new_btn)

        commit_btn = QPushButton("提交代码")
        commit_btn.setToolTip("提交当前目录的代码更改")
        commit_btn.clicked.connect(self._on_commit_code)
        toolbar.addWidget(commit_btn)

        layout.addLayout(toolbar)

        # 初始化工作目录显示
        self._update_chat_work_dir_display()

        # 聊天区域
        self.chat_area = QTextEdit()
        self.chat_area.setReadOnly(True)
        self.chat_area.setPlaceholderText("对话记录将显示在这里...")
        layout.addWidget(self.chat_area)

        # 输入区域
        input_layout = QVBoxLayout()

        # 自定义输入框，支持回车发送
        self.chat_input = QTextEdit()
        self.chat_input.setMaximumHeight(80)
        self.chat_input.setPlaceholderText("输入你的问题... (按 Enter 发送，Shift+Enter 换行)")

        # 创建自定义 keyPressEvent 处理
        original_key_press = self.chat_input.keyPressEvent

        def custom_key_press(event):
            if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
                if event.modifiers() & Qt.ShiftModifier:
                    # Shift+Enter 换行
                    original_key_press(event)
                else:
                    # Enter 发送
                    self._on_send_chat_message()
            else:
                original_key_press(event)

        self.chat_input.keyPressEvent = custom_key_press

        input_layout.addWidget(self.chat_input)

        # 按钮行
        button_layout = QHBoxLayout()
        button_layout.addStretch()

        send_btn = QPushButton("发送")
        send_btn.clicked.connect(self._on_send_chat_message)
        button_layout.addWidget(send_btn)

        input_layout.addLayout(button_layout)
        layout.addLayout(input_layout)

        self.pages["AI 对话"] = page
        self.content_stack.addWidget(page)

        # 检查提供商配置
        self._check_chat_provider()

    def _check_chat_provider(self):
        """检查聊天提供商配置"""
        try:
            provider = provider_manager.get_active_provider()
            if provider:
                has_valid_key = bool(provider.api_key and not provider.api_key.startswith("test"))
                if has_valid_key:
                    self.chat_status_label.setText(f"活动: {provider.name} ({provider.model})")
                    self.chat_status_label.setStyleSheet("color: green; font-size: 11px;")
                else:
                    self.chat_status_label.setText("API 密钥无效")
                    self.chat_status_label.setStyleSheet("color: orange; font-size: 11px;")
            else:
                self.chat_status_label.setText("未配置提供商")
                self.chat_status_label.setStyleSheet("color: orange; font-size: 11px;")
        except Exception as e:
            self.chat_status_label.setText(f"配置错误: {e}")
            self.chat_status_label.setStyleSheet("color: red; font-size: 11px;")

    def _on_new_chat(self):
        """新建对话"""
        try:
            self.chat_conversation_id = conversation_service.create_conversation(
                title="新对话",
                project_path=None,
            )
            self.chat_area.clear()
            self.chat_area.append(f"--- 新对话 (ID: {self.chat_conversation_id}) ---")
        except Exception as e:
            self.chat_area.append(f"\n[错误] 创建对话失败: {e}")

    def _on_send_chat_message(self):
        """发送聊天消息"""
        content = self.chat_input.toPlainText().strip()
        if not content:
            return

        # 检查提供商
        provider = provider_manager.get_active_provider()
        if not provider:
            self.chat_area.append("\n[错误] 请先在'提供商管理'页面配置 AI 提供商")
            return

        if not provider.api_key or provider.api_key.startswith("test"):
            self.chat_area.append(f"\n[错误] 提供商 '{provider.name}' 的 API 密钥无效")
            return

        # 确保有对话 ID
        if not hasattr(self, 'chat_conversation_id') or self.chat_conversation_id is None:
            self._on_new_chat()
            if not hasattr(self, 'chat_conversation_id') or self.chat_conversation_id is None:
                return

        # 显示用户消息
        self.chat_area.append(f"\n[用户]: {content}")

        # 清空输入
        self.chat_input.clear()

        # 禁用输入
        self.chat_input.setEnabled(False)
        self.chat_area.append("\n[系统] 正在思考...")

        # 保存"正在思考"的位置，用于移除
        thinking_marker = f"__THINKING_{len(content)}__"

        # 使用 QThread 在后台发送消息
        from PySide6.QtCore import QThread, QObject, Signal, QTimer

        class ChatWorker(QObject):
            finished = Signal(str)
            error = Signal(str)

            def __init__(self, conversation_id, content):
                super().__init__()
                self.conversation_id = conversation_id
                self.content = content

            def run(self):
                import asyncio
                try:
                    loop = asyncio.new_event_loop()
                    asyncio.set_event_loop(loop)

                    async def send_with_retry():
                        # 重试机制
                        max_retries = 3
                        for attempt in range(max_retries):
                            try:
                                message = await conversation_service.send_message(
                                    self.conversation_id, self.content
                                )
                                return message.content
                            except Exception as e:
                                if attempt < max_retries - 1:
                                    print(f"[重试] 第 {attempt + 1} 次失败，{2**attempt}秒后重试...")
                                    await asyncio.sleep(2**attempt)
                                else:
                                    raise

                    response = loop.run_until_complete(send_with_retry())
                    loop.run_until_complete(loop.shutdown_asyncgens())
                    loop.close()
                    self.finished.emit(response)
                except Exception as e:
                    import traceback
                    traceback.print_exc()
                    self.error.emit(str(e))

        # 创建并启动线程
        thread = QThread()
        thread.setObjectName("ChatWorkerThread")
        worker = ChatWorker(self.chat_conversation_id, content)
        worker.moveToThread(thread)

        # 保存线程引用
        self._active_threads.append(thread)

        # 注意：所有回调都是在主线程中执行的（通过信号槽机制）
        def on_finished(response):
            # 在主线程中安全地更新 GUI
            import re
            text = self.chat_area.toPlainText()
            # 移除"正在思考"文本
            text = re.sub(r'\n\[系统\] 正在思考\.\.\.', '', text)
            self.chat_area.setPlainText(text)
            # 移动光标到末尾
            cursor = self.chat_area.textCursor()
            cursor.movePosition(cursor.End)
            self.chat_area.setTextCursor(cursor)

            self.chat_area.append(f"\n[AI]: {response}")
            self.chat_input.setEnabled(True)
            self.chat_input.setFocus()

            # 清理线程
            if thread in self._active_threads:
                self._active_threads.remove(thread)
            thread.quit()
            thread.wait(3000)
            thread.deleteLater()

        def on_error(error_msg):
            # 在主线程中安全地更新 GUI
            import re
            text = self.chat_area.toPlainText()
            # 移除"正在思考"文本
            text = re.sub(r'\n\[系统\] 正在思考\.\.\.', '', text)
            self.chat_area.setPlainText(text)
            # 移动光标到末尾
            cursor = self.chat_area.textCursor()
            cursor.movePosition(cursor.End)
            self.chat_area.setTextCursor(cursor)

            if "timeout" in error_msg.lower() or "timed out" in error_msg.lower():
                self.chat_area.append(f"\n[错误] 请求超时，请检查网络连接或稍后重试")
            elif "401" in error_msg or "authentication" in error_msg.lower():
                self.chat_area.append(f"\n[错误] API 密钥无效，请在'提供商管理'页面更新")
            else:
                self.chat_area.append(f"\n[错误] {error_msg[:200]}")
            self.chat_input.setEnabled(True)
            self.chat_input.setFocus()

            # 清理线程
            if thread in self._active_threads:
                self._active_threads.remove(thread)
            thread.quit()
            thread.wait(3000)
            thread.deleteLater()

        # 使用 QTimer 延迟调用，确保线程事件循环已启动
        def start_worker():
            QTimer.singleShot(50, worker.run)

        thread.started.connect(start_worker)
        worker.finished.connect(on_finished)
        worker.error.connect(on_error)
        thread.start()

    def create_history_page(self):
        """创建历史页面"""
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.addWidget(QLabel("代码修改历史"))

        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "文件路径", "时间", "状态"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)

        self.pages["修改历史"] = page
        self.content_stack.addWidget(page)

    def create_bug_page(self):
        """创建 Bug 页面"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # 工具栏
        toolbar = QHBoxLayout()
        new_btn = QPushButton("新建 Bug")
        toolbar.addWidget(new_btn)
        toolbar.addStretch()
        layout.addLayout(toolbar)

        # Bug 列表
        table = QTableWidget()
        table.setColumnCount(4)
        table.setHorizontalHeaderLabels(["ID", "标题", "状态", "时间"])
        table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        layout.addWidget(table)

        self.pages["Bug 追踪"] = page
        self.content_stack.addWidget(page)

    def create_knowledge_page(self):
        """创建知识库页面"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # 搜索栏
        search_layout = QHBoxLayout()
        search_layout.addWidget(QLabel("搜索:"))
        search_input = QTextEdit()
        search_input.setMaximumHeight(25)
        search_input.setPlaceholderText("输入关键词...")
        search_layout.addWidget(search_input)

        search_btn = QPushButton("搜索")
        search_layout.addWidget(search_btn)

        layout.addLayout(search_layout)

        # 结果列表
        result_list = QListWidget()
        layout.addWidget(result_list)

        self.pages["知识库"] = page
        self.content_stack.addWidget(page)

    def create_provider_page(self):
        """创建提供商管理页面"""
        page = QWidget()
        layout = QVBoxLayout(page)

        # 标题
        layout.addWidget(QLabel("提供商管理"))

        # 提供商列表
        self.provider_list_widget = QListWidget()
        layout.addWidget(QLabel("已配置的提供商:"))
        layout.addWidget(self.provider_list_widget)

        # 加载提供商
        self._load_providers_in_page()

        # 按钮区
        button_layout = QHBoxLayout()

        import_btn = QPushButton("从预设导入")
        import_btn.clicked.connect(self._on_import_provider)
        button_layout.addWidget(import_btn)

        edit_btn = QPushButton("编辑提供商")
        edit_btn.clicked.connect(self._on_edit_provider)
        button_layout.addWidget(edit_btn)

        switch_btn = QPushButton("切换提供商")
        switch_btn.clicked.connect(self._on_switch_provider)
        button_layout.addWidget(switch_btn)

        layout.addLayout(button_layout)

        # 快速更新 API Key 区
        quick_update_layout = QHBoxLayout()
        quick_update_layout.addWidget(QLabel("快速更新 API Key:"))

        self.api_key_input = QLineEdit()
        self.api_key_input.setPlaceholderText("选中提供商后输入新 API 密钥")
        self.api_key_input.setEchoMode(QLineEdit.Password)
        quick_update_layout.addWidget(self.api_key_input)

        update_key_btn = QPushButton("更新")
        update_key_btn.clicked.connect(self._on_quick_update_api_key)
        quick_update_layout.addWidget(update_key_btn)

        layout.addLayout(quick_update_layout)

        # 预设列表
        layout.addWidget(QLabel("可用的预设配置:"))

        preset_list = QListWidget()
        preset_list.setMaximumHeight(150)

        # 按类别分组显示预设
        categories = {}
        for preset in PROVIDER_PRESETS:
            if preset.category not in categories:
                categories[preset.category] = []
            categories[preset.category].append(preset)

        for category, presets in categories.items():
            preset_list.addItem(f"--- {category.upper()} ---")
            for preset in presets:
                preset_list.addItem(f"  {preset.name} ({preset.id})")

        layout.addWidget(preset_list)

        # 说明
        info = QLabel("提示: 点击 '从预设导入' 可以快速配置提供商")
        info.setStyleSheet("color: gray; font-size: 11px;")
        layout.addWidget(info)

        self.pages["提供商管理"] = page
        self.content_stack.addWidget(page)

    def _load_providers_in_page(self):
        """加载提供商列表"""
        try:
            self.provider_list_widget.clear()
            providers = provider_manager.get_providers()
            active = provider_manager.get_active_provider()

            for p in providers:
                is_active = " [活动中]" if active and p.id == active.id else ""
                self.provider_list_widget.addItem(f"{p.name} ({p.id}){is_active}")
        except Exception as e:
            self.provider_list_widget.addItem(f"加载失败: {e}")

    def _on_edit_provider(self):
        """编辑提供商"""
        current = self.provider_list_widget.currentItem()
        if not current:
            QMessageBox.warning(None, "提示", "请先选择要编辑的提供商")
            return

        text = current.text()
        # 解析提供商 ID
        try:
            provider_id = text.split("(")[1].split(")")[0]
        except IndexError:
            QMessageBox.warning(None, "错误", "无法解析提供商 ID")
            return

        providers = provider_manager.get_providers()
        provider = next((p for p in providers if p.id == provider_id), None)

        if provider:
            # 创建编辑对话框
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QLineEdit, QDialogButtonBox, QFormLayout

            dialog = QDialog()
            dialog.setWindowTitle(f"编辑提供商: {provider.name}")
            dialog.setMinimumWidth(400)
            dialog_layout = QVBoxLayout(dialog)

            # 使用表单布局使界面更整洁
            form_layout = QFormLayout()

            # 名称
            name_edit = QLineEdit(provider.name)
            form_layout.addRow("名称:", name_edit)

            # API 端点（新增）
            endpoint_edit = QLineEdit(provider.api_endpoint)
            endpoint_edit.setPlaceholderText("https://api.example.com (可选)")
            form_layout.addRow("API 端点:", endpoint_edit)

            # 模型
            model_edit = QLineEdit(provider.model)
            form_layout.addRow("模型:", model_edit)

            # API 密钥
            api_key_edit = QLineEdit(provider.api_key)
            api_key_edit.setEchoMode(QLineEdit.Password)
            form_layout.addRow("API 密钥:", api_key_edit)

            # 添加说明
            endpoint_hint = QLabel("💡 提示: API 端点用于中转服务或自定义 API 地址")
            endpoint_hint.setStyleSheet("color: #888; font-size: 10px;")
            dialog_layout.addWidget(endpoint_hint)

            dialog_layout.addLayout(form_layout)

            # 按钮
            buttons = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            dialog_layout.addWidget(buttons)

            if dialog.exec() == QDialog.Accepted:
                # 更新配置
                from src.services.provider_service import ProviderConfig
                updated_config = ProviderConfig(
                    id=provider.id,
                    name=name_edit.text(),
                    provider_type=provider.provider_type,
                    api_key=api_key_edit.text(),
                    api_endpoint=endpoint_edit.text() or provider.api_endpoint,  # 允许为空
                    model=model_edit.text(),
                    temperature=provider.temperature,
                    max_tokens=provider.max_tokens,
                    top_p=provider.top_p,
                    proxy_url=provider.proxy_url,
                    proxy_enabled=provider.proxy_enabled,
                    is_enabled=provider.is_enabled,
                    custom_params=provider.custom_params,
                )

                if provider_manager.update_provider(provider_id, updated_config):
                    QMessageBox.information(
                        None,
                        "成功",
                        f"已更新提供商:\n"
                        f"名称: {updated_config.name}\n"
                        f"端点: {updated_config.api_endpoint or '(默认)'}\n"
                        f"模型: {updated_config.model}"
                    )
                    self._load_providers_in_page()
                else:
                    QMessageBox.warning(None, "失败", "更新提供商失败")

    def _on_quick_update_api_key(self):
        """快速更新 API Key"""
        current = self.provider_list_widget.currentItem()
        if not current:
            QMessageBox.warning(None, "提示", "请先选择要更新 API Key 的提供商")
            return

        api_key = self.api_key_input.text().strip()
        if not api_key:
            QMessageBox.warning(None, "提示", "请输入新的 API 密码")
            return

        text = current.text()
        try:
            provider_id = text.split("(")[1].split(")")[0]
        except IndexError:
            QMessageBox.warning(None, "错误", "无法解析提供商 ID")
            return

        providers = provider_manager.get_providers()
        provider = next((p for p in providers if p.id == provider_id), None)

        if provider:
            # 更新 API Key
            from src.services.provider_service import ProviderConfig
            updated_config = ProviderConfig(
                id=provider.id,
                name=provider.name,
                provider_type=provider.provider_type,
                api_key=api_key,
                api_endpoint=provider.api_endpoint,
                model=provider.model,
                temperature=provider.temperature,
                max_tokens=provider.max_tokens,
                top_p=provider.top_p,
                proxy_url=provider.proxy_url,
                proxy_enabled=provider.proxy_enabled,
                is_enabled=provider.is_enabled,
                custom_params=provider.custom_params,
            )

            if provider_manager.update_provider(provider_id, updated_config):
                QMessageBox.information(None, "成功", f"已更新 {provider.name} 的 API 密码")
                self.api_key_input.clear()
            else:
                QMessageBox.warning(None, "失败", "更新 API 密码失败")

    def _on_import_provider(self):
        """导入提供商（简化版本）"""
        from PySide6.QtWidgets import QInputDialog, QMessageBox

        # 显示预设选择对话框
        presets = [f"{p.name} ({p.id})" for p in PROVIDER_PRESETS]

        result = QInputDialog.getItem(
            None, "选择预设", "选择一个预设配置:", presets, 0, False
        )

        # result 是一个元组 (ok, selection)
        if result and len(result) == 2:
            ok, selection = result
            if ok and selection and isinstance(selection, str):
                # 解析预设 ID
                try:
                    preset_id = selection.split("(")[1].split(")")[0]
                except IndexError:
                    QMessageBox.warning(None, "错误", "无法解析预设 ID")
                    return

                # 获取 API Key
                api_key_result = QInputDialog.getText(
                    None, "输入 API Key", "请输入 API 密钥:", QLineEdit.Password
                )

                if api_key_result and len(api_key_result) == 2:
                    ok, api_key = api_key_result
                    if ok and api_key:
                        try:
                            config = provider_manager.import_from_preset(preset_id, api_key)
                            if config and provider_manager.add_provider(config):
                                QMessageBox.information(None, "成功", f"已添加提供商: {config.name}")
                            else:
                                QMessageBox.warning(None, "失败", "添加提供商失败")
                        except Exception as e:
                            QMessageBox.critical(None, "错误", f"导入失败: {e}")

    def _on_switch_provider(self):
        """切换提供商（简化版本）"""
        from PySide6.QtWidgets import QInputDialog, QMessageBox

        providers = provider_manager.get_providers()
        if not providers:
            QMessageBox.warning(None, "提示", "没有配置任何提供商")
            return

        provider_names = [f"{p.name} ({p.id})" for p in providers]

        result = QInputDialog.getItem(
            None, "切换提供商", "选择要切换到的提供商:", provider_names, 0, False
        )

        # result 是一个元组 (ok, selection)
        if result and len(result) == 2:
            ok, selection = result
            if ok and selection and isinstance(selection, str):
                try:
                    provider_id = selection.split("(")[1].split(")")[0]
                except IndexError:
                    QMessageBox.warning(None, "错误", "无法解析提供商 ID")
                    return

                try:
                    if provider_manager.switch_provider(provider_id):
                        QMessageBox.information(None, "成功", f"已切换到: {selection}")
                    else:
                        QMessageBox.warning(None, "失败", "切换失败")
                except Exception as e:
                    QMessageBox.critical(None, "错误", f"切换失败: {e}")

    def _on_commit_code(self):
        """提交代码功能 - 支持 Git 和 SVN"""
        try:
            # 检测 VCS 类型
            vcs_type = self._detect_vcs()

            if vcs_type is None:
                QMessageBox.warning(
                    None,
                    "不是版本控制仓库",
                    f"当前目录不是 Git 或 SVN 仓库:\n{self.current_work_dir}\n\n请先初始化版本控制仓库。"
                )
                return

            # 根据 VCS 类型获取文件状态
            if vcs_type == "git":
                modified_files, untracked_files = self._get_git_status()
                vcs_name = "Git"
            else:  # svn
                modified_files, untracked_files = self._get_svn_status()
                vcs_name = "SVN"

            if not modified_files and not untracked_files:
                QMessageBox.information(
                    None,
                    "没有更改",
                    "当前工作目录没有需要提交的更改。"
                )
                return

            # 创建提交对话框
            from PySide6.QtWidgets import QDialog, QVBoxLayout, QTextEdit, QCheckBox, QDialogButtonBox, QScrollArea, QWidget

            dialog = QDialog()
            dialog.setWindowTitle(f"提交代码 ({vcs_name})")
            dialog.setMinimumWidth(700)
            dialog.setMinimumHeight(500)
            dialog_layout = QVBoxLayout(dialog)

            # 显示 VCS 类型
            dialog_layout.addWidget(QLabel(f"版本控制系统: {vcs_name}"))

            # 已修改文件
            if modified_files:
                dialog_layout.addWidget(QLabel("已修改的文件:"))
                modified_text = QTextEdit()
                modified_text.setMaximumHeight(100)
                modified_text.setReadOnly(True)
                modified_text.setText('\n'.join(modified_files))
                dialog_layout.addWidget(modified_text)

            # 新增文件（带勾选）
            if untracked_files:
                dialog_layout.addWidget(QLabel("新增文件 (勾选要添加的文件):"))

                # 创建滚动区域
                scroll = QScrollArea()
                scroll.setWidgetResizable(True)
                scroll.setMaximumHeight(200)

                checkbox_container = QWidget()
                checkbox_layout = QVBoxLayout(checkbox_container)

                self.untracked_checkboxes = []

                for file_path in untracked_files:
                    checkbox = QCheckBox(file_path)
                    checkbox.setChecked(True)  # 默认勾选
                    checkbox_layout.addWidget(checkbox)
                    self.untracked_checkboxes.append(checkbox)

                checkbox_layout.addStretch()
                scroll.setWidget(checkbox_container)
                dialog_layout.addWidget(scroll)

            # 提交消息输入
            dialog_layout.addWidget(QLabel("提交消息:"))
            commit_msg_edit = QTextEdit()
            commit_msg_edit.setMaximumHeight(60)
            commit_msg_edit.setPlaceholderText("输入提交消息，描述本次更改...")
            dialog_layout.addWidget(commit_msg_edit)

            # 推送/更新选项
            push_label = "提交后推送到远程仓库 (Git)" if vcs_type == "git" else "提交前更新代码 (SVN)"
            push_checkbox = QCheckBox(push_label)
            dialog_layout.addWidget(push_checkbox)

            # 按钮
            buttons = QDialogButtonBox(
                QDialogButtonBox.Ok | QDialogButtonBox.Cancel
            )
            buttons.accepted.connect(dialog.accept)
            buttons.rejected.connect(dialog.reject)
            dialog_layout.addWidget(buttons)

            if dialog.exec() != QDialog.Accepted:
                return

            commit_msg = commit_msg_edit.text().strip()
            if not commit_msg:
                QMessageBox.warning(None, "提示", "请输入提交消息")
                return

            # 执行提交
            if vcs_type == "git":
                self._commit_git(modified_files, untracked_files, commit_msg, push_checkbox.isChecked())
            else:  # svn
                self._commit_svn(modified_files, untracked_files, commit_msg, push_checkbox.isChecked())

        except FileNotFoundError:
            QMessageBox.warning(
                None,
                "版本控制工具未安装",
                "未找到 Git 或 SVN 命令。\n请安装相应的版本控制工具后再使用此功能。"
            )
        except Exception as e:
            QMessageBox.critical(
                None,
                "操作失败",
                f"提交代码时发生错误:\n{str(e)}"
            )

    def _detect_vcs(self):
        """检测当前目录的版本控制系统类型"""
        # 检查 Git
        git_result = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            capture_output=True,
            text=True,
            cwd=str(self.current_work_dir)
        )
        if git_result.returncode == 0:
            return "git"

        # 检查 SVN
        svn_result = subprocess.run(
            ["svn", "info"],
            capture_output=True,
            text=True,
            cwd=str(self.current_work_dir)
        )
        if svn_result.returncode == 0:
            return "svn"

        return None

    def _get_git_status(self):
        """获取 Git 状态"""
        # 获取已修改文件
        status_result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            cwd=str(self.current_work_dir)
        )
        modified_files = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []

        # 获取未跟踪文件
        untracked_result = subprocess.run(
            ["git", "ls-files", "--others", "--exclude-standard"],
            capture_output=True,
            text=True,
            cwd=str(self.current_work_dir)
        )
        untracked_files = untracked_result.stdout.strip().split('\n') if untracked_result.stdout.strip() else []

        # 过滤掉空行
        modified_files = [f for f in modified_files if f]
        untracked_files = [f for f in untracked_files if f]

        return modified_files, untracked_files

    def _get_svn_status(self):
        """获取 SVN 状态"""
        status_result = subprocess.run(
            ["svn", "status"],
            capture_output=True,
            text=True,
            cwd=str(self.current_work_dir)
        )

        lines = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []
        modified_files = []
        untracked_files = []

        for line in lines:
            if not line:
                continue
            # SVN status 格式: "M       file.py" 或 "?       newfile.py"
            status = line[0] if line else ''
            file_path = line[8:] if len(line) > 8 else line  # 跳过状态字符和空格

            if status == 'M':  # 已修改
                modified_files.append(file_path)
            elif status == '?':  # 未跟踪
                untracked_files.append(file_path)
            elif status == 'A':  # 已添加（待提交）
                modified_files.append(f"{file_path} (已添加)")

        return modified_files, untracked_files

    def _commit_git(self, modified_files, untracked_files, commit_msg, push_after):
        """执行 Git 提交"""
        # 添加选中新增的文件
        selected_untracked = []
        if hasattr(self, 'untracked_checkboxes'):
            for checkbox in self.untracked_checkboxes:
                if checkbox.isChecked():
                    selected_untracked.append(checkbox.text())

        # 添加已修改的文件
        if modified_files:
            self.chat_area.append(f"\n[系统] 正在添加已修改的文件...")

        if selected_untracked:
            self.chat_area.append(f"[系统] 正在添加 {len(selected_untracked)} 个新增文件...")

        # 执行 git add
        all_files_to_add = modified_files + selected_untracked

        if all_files_to_add:
            # 逐个添加文件
            for file_path in all_files_to_add:
                # 提取文件名（去掉 Git 状态前缀）
                if ' ' in file_path:
                    file_path = file_path.split(' ', 1)[1]

                add_result = subprocess.run(
                    ["git", "add", file_path],
                    capture_output=True,
                    text=True,
                    cwd=str(self.current_work_dir)
                )

                if add_result.returncode != 0:
                    QMessageBox.critical(
                        None,
                        "添加文件失败",
                        f"无法添加文件 {file_path}:\n{add_result.stderr}"
                    )
                    return

        # 执行 git commit
        self.chat_area.append(f"[系统] 正在提交更改...")

        commit_result = subprocess.run(
            ["git", "commit", "-m", commit_msg],
            capture_output=True,
            text=True,
            cwd=str(self.current_work_dir)
        )

        if commit_result.returncode != 0:
            QMessageBox.critical(
                None,
                "提交失败",
                f"Git commit 失败:\n{commit_result.stderr}"
            )
            return

        self.chat_area.append(f"[系统] 提交成功！")
        self.chat_area.append(f"[系统] 提交消息: {commit_msg}")

        if len(selected_untracked) > 0:
            self.chat_area.append(f"[系统] 包含 {len(selected_untracked)} 个新增文件")

        # 检查是否需要推送
        if push_after:
            self.chat_area.append(f"[系统] 正在推送到远程仓库...")

            push_result = subprocess.run(
                ["git", "push"],
                capture_output=True,
                text=True,
                cwd=str(self.current_work_dir)
            )

            if push_result.returncode != 0:
                self.chat_area.append(f"[系统] 推送失败: {push_result.stderr}")
                QMessageBox.warning(
                    None,
                    "推送失败",
                    f"已提交到本地，但推送失败:\n{push_result.stderr}"
                )
            else:
                self.chat_area.append(f"[系统] 推送成功！")
                QMessageBox.information(
                    None,
                    "提交成功",
                    f"代码已提交并推送到远程仓库\n提交消息: {commit_msg}"
                )
        else:
            QMessageBox.information(
                None,
                "提交成功",
                f"代码已提交到本地仓库\n提交消息: {commit_msg}\n\n你可以稍后手动推送。"
            )

    def _commit_svn(self, modified_files, untracked_files, commit_msg, update_before):
        """执行 SVN 提交"""
        # 添加选中新增的文件
        selected_untracked = []
        if hasattr(self, 'untracked_checkboxes'):
            for checkbox in self.untracked_checkboxes:
                if checkbox.isChecked():
                    selected_untracked.append(checkbox.text())

        # 先更新（如果选择）
        if update_before:
            self.chat_area.append(f"\n[系统] 正在更新代码...")

            update_result = subprocess.run(
                ["svn", "update"],
                capture_output=True,
                text=True,
                cwd=str(self.current_work_dir)
            )

            if update_result.returncode != 0:
                self.chat_area.append(f"[系统] 更新失败: {update_result.stderr}")
                QMessageBox.warning(
                    None,
                    "更新失败",
                    f"更新失败，是否继续提交？\n{update_result.stderr}"
                )
            else:
                self.chat_area.append(f"[系统] 更新完成")

        # 添加新增的文件
        if selected_untracked:
            self.chat_area.append(f"[系统] 正在添加 {len(selected_untracked)} 个新增文件...")

            for file_path in selected_untracked:
                add_result = subprocess.run(
                    ["svn", "add", file_path],
                    capture_output=True,
                    text=True,
                    cwd=str(self.current_work_dir)
                )

                if add_result.returncode != 0:
                    QMessageBox.critical(
                        None,
                        "添加文件失败",
                        f"无法添加文件 {file_path}:\n{add_result.stderr}"
                    )
                    return

        # 执行 svn commit
        self.chat_area.append(f"[系统] 正在提交更改...")

        commit_result = subprocess.run(
            ["svn", "commit", "-m", commit_msg],
            capture_output=True,
            text=True,
            cwd=str(self.current_work_dir)
        )

        if commit_result.returncode != 0:
            QMessageBox.critical(
                None,
                "提交失败",
                f"SVN commit 失败:\n{commit_result.stderr}"
            )
            return

        self.chat_area.append(f"[系统] 提交成功！")
        self.chat_area.append(f"[系统] 提交消息: {commit_msg}")

        if len(selected_untracked) > 0:
            self.chat_area.append(f"[系统] 包含 {len(selected_untracked)} 个新增文件")

        QMessageBox.information(
            None,
            "提交成功",
            f"代码已提交到 SVN 仓库\n提交消息: {commit_msg}"
        )

    def create_settings_page(self):
        """创建设置页面"""
        page = QWidget()
        layout = QVBoxLayout(page)

        layout.addWidget(QLabel("应用设置"))

        # 配置项
        config_widget = QWidget()
        config_layout = QVBoxLayout(config_widget)

        # AI 配置
        config_layout.addWidget(QLabel("AI 配置"))
        try:
            cfg = config_service.get_config()
            config_layout.addWidget(QLabel(f"提供商: {cfg.ai.provider}"))
            config_layout.addWidget(QLabel(f"模型: {cfg.ai.model}"))
            config_layout.addWidget(QLabel(f"温度: {cfg.ai.temperature}"))
        except:
            config_layout.addWidget(QLabel("无法加载配置"))

        config_layout.addStretch()
        layout.addWidget(config_widget)
        layout.addStretch()

        self.pages["设置"] = page
        self.content_stack.addWidget(page)

    def show_page(self, row):
        """显示指定页面"""
        page_names = list(self.pages.keys())
        if 0 <= row < len(page_names):
            page_name = page_names[row]
            self.content_stack.setCurrentWidget(self.pages[page_name])

    def closeEvent(self, event):
        """窗口关闭事件"""
        # 等待所有活跃线程完成
        for thread in self._active_threads:
            if thread.isRunning():
                thread.quit()
                thread.wait(1000)  # 最多等待 1 秒
        event.accept()


# 创建并显示窗口
app = QApplication(sys.argv)
window = CodeTraceAIWindow()
window.show()

print("CodeTraceAI GUI 已启动！")

# 运行应用
sys.exit(app.exec())
