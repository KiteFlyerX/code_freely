"""
对话服务
处理与 AI 的对话交互，支持工具调用
"""
import asyncio
from typing import List, Optional, AsyncIterator, Callable
from datetime import datetime
from pathlib import Path

from ..ai import BaseAI, Message, MessageRole, AIResponse, AIRequestConfig
from ..database import get_db_session
from ..database.repositories import ConversationRepository, MessageRepository
from ..models import Conversation as ConversationModel, ConversationMessage as MessageModel
from .config_service import config_service
from ..vcs import get_vcs
from ..tools import tool_registry


class ConversationService:
    """
    对话服务
    管理 AI 对话、消息存储和代码修改记录
    """

    def __init__(self):
        self._ai_client: Optional[BaseAI] = None
        self._conversation_repo = ConversationRepository(get_db_session())
        self._message_repo = MessageRepository(get_db_session())
        self._current_work_dir: Optional[Path] = None

    def set_work_dir(self, work_dir: Path):
        """设置当前工作目录"""
        self._current_work_dir = work_dir

    async def _generate_commit_message(self, user_question: str, ai_response: str) -> str:
        """
        使用 AI 分析代码变更并生成专业的提交消息

        Args:
            user_question: 用户的问题
            ai_response: AI 的响应

        Returns:
            str: AI 生成的提交消息
        """
        import subprocess

        target_dir = str(self._current_work_dir) if self._current_work_dir else str(Path.cwd())

        try:
            # 先添加所有更改到暂存区
            subprocess.run(
                ['git', 'add', '-A'],
                capture_output=True,
                cwd=target_dir
            )

            # 获取 git diff (暂存区的变更)
            diff_result = subprocess.run(
                ['git', 'diff', '--cached', '--unified=1'],
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                text=True,
                cwd=target_dir
            )

            diff_content = diff_result.stdout.strip()

            if not diff_content:
                # 没有变更
                return None

            # 限制 diff 大小，避免 token 过多
            if len(diff_content) > 15000:
                # 保留头部和尾部
                half = 7000
                diff_content = diff_content[:half] + "\n... (中间部分省略) ...\n" + diff_content[-half:]

            # 获取变更的文件列表
            status_result = subprocess.run(
                ['git', 'status', '--short'],
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                text=True,
                cwd=target_dir
            )

            status_lines = status_result.stdout.strip().split('\n') if status_result.stdout.strip() else []
            changed_files = []
            for line in status_lines:
                parts = line.split()
                if len(parts) >= 2:
                    changed_files.append(parts[1])

            # 使用 AI 生成提交消息
            ai_client = self._get_ai_client()

            file_info = f"\n变更的文件: {', '.join(changed_files[:10])}"
            if len(changed_files) > 10:
                file_info += f" 等 {len(changed_files)} 个文件"

            prompt = f"""分析以下代码变更，生成一个简洁的 Git 提交消息。

用户需求: {user_question[:200]}
{file_info}

代码变更 (git diff --cached):
```
{diff_content}
```

请生成一个专业的 Git 提交消息，遵循以下规范：
1. 使用 conventional commits 格式: <type>: <description>
2. type 可以是: feat(新功能), fix(修复), refactor(重构), perf(性能优化), style(代码格式), docs(文档), test(测试), chore(构建/工具)
3. description 应该简洁明了，说明改动的目的和内容
4. 只返回一条提交消息，格式如: "fix: 修复用户登录时的验证错误"
5. 不要加引号，不要有其他内容

提交消息:"""

            # 调用 AI 生成提交消息
            from ..ai.base import Message, MessageRole, AIRequestConfig

            messages = [
                Message(role=MessageRole.SYSTEM, content="你是一个专业的 Git 提交消息生成助手。请分析代码变更并生成符合规范的提交消息。"),
                Message(role=MessageRole.USER, content=prompt)
            ]

            config = AIRequestConfig(
                temperature=0.2,  # 降低温度以获得更稳定的结果
                max_tokens=100,   # 限制生成长度
            )

            response = await ai_client.chat(messages, config)

            if response.content:
                # 清理 AI 返回的内容
                commit_msg = response.content.strip()
                # 移除可能的引号
                commit_msg = commit_msg.strip('"\'').strip()
                # 移除可能的 "提交消息:" 前缀
                if commit_msg.startswith("提交消息:"):
                    commit_msg = commit_msg[5:].strip()
                if commit_msg.startswith("message:"):
                    commit_msg = commit_msg[8:].strip()
                # 取第一行
                commit_msg = commit_msg.split('\n')[0].strip()
                return commit_msg

            return "chore: 更新代码"

        except Exception as e:
            print(f"AI 生成提交消息失败: {e}")
            import traceback
            traceback.print_exc()
            # 回退到简单生成方式
            return f"chore: {user_question[:50]}"

    def _get_ai_client(self) -> BaseAI:
        """获取 AI 客户端"""
        if self._ai_client is None:
            from .ai_client_factory import get_ai_client

            self._ai_client = get_ai_client()

            if not self._ai_client:
                raise ValueError("未配置有效的 AI 提供商，请先配置提供商和 API 密钥")

        return self._ai_client

    def _execute_tool(self, tool_name: str, arguments: dict) -> dict:
        """
        执行工具

        Args:
            tool_name: 工具名称
            arguments: 工具参数

        Returns:
            dict: 工具执行结果
        """
        # 切换到工作目录执行工具
        import os
        old_cwd = os.getcwd()
        target_dir = str(self._current_work_dir) if self._current_work_dir else old_cwd

        try:
            os.chdir(target_dir)

            # 确保参数不为 None
            if arguments is None:
                arguments = {}

            # 添加日志用于调试
            print(f"[DEBUG] 执行工具: {tool_name}, 参数: {arguments}")

            result = tool_registry.execute(tool_name, **arguments)
            result_dict = result.to_dict()

            # 不再每次 Write 都自动提交，改为批量提交
            # 移除了原有的自动提交逻辑

            return result_dict
        finally:
            # 恢复原工作目录
            os.chdir(old_cwd)

    def commit_changes(self, commit_message: Optional[str] = None, force: bool = False) -> Optional[dict]:
        """
        提交当前工作目录的所有更改

        Args:
            commit_message: 自定义提交消息，如果为 None 则自动生成
            force: 是否强制提交（忽略 auto_commit 配置）

        Returns:
            dict: 提交结果，包含 success, commit_id, commit_msg 等信息
        """
        import subprocess
        from .config_service import config_service

        target_dir = str(self._current_work_dir) if self._current_work_dir else str(Path.cwd())

        try:
            # 检查是否启用自动提交（除非强制提交）
            if not force:
                config = config_service.get_config()
                if not config.auto_commit:
                    return {"success": False, "error": "自动提交未启用"}

            # 检查是否有 VCS
            vcs = get_vcs(target_dir)
            if not vcs:
                return {"success": False, "error": "不是版本控制仓库"}

            # 获取文件状态
            status_result = subprocess.run(
                ['git', 'status', '--short'],
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                text=True,
                cwd=target_dir
            )

            if status_result.returncode != 0:
                return {"success": False, "error": "获取文件状态失败"}

            # 检查是否有更改
            if not status_result.stdout.strip():
                return {"success": False, "error": "没有需要提交的更改"}

            # 分析变更类型
            added_files = []
            modified_files = []
            deleted_files = []

            for line in status_result.stdout.strip().split('\n'):
                if line:
                    parts = line.strip().split()
                    if len(parts) >= 2:
                        status = parts[0]
                        path = parts[1]
                        if status.startswith('A'):
                            added_files.append(path)
                        elif status.startswith('M'):
                            modified_files.append(path)
                        elif status.startswith('D'):
                            deleted_files.append(path)

            # 生成提交消息
            if commit_message is None:
                # 自动生成提交消息
                if added_files and not modified_files and not deleted_files:
                    commit_message = f"Add {', '.join(added_files[:3])}"
                    if len(added_files) > 3:
                        commit_message += f" and {len(added_files) - 3} more files"
                elif modified_files and not added_files and not deleted_files:
                    commit_message = f"Update {', '.join(modified_files[:3])}"
                    if len(modified_files) > 3:
                        commit_message += f" and {len(modified_files) - 3} more files"
                else:
                    # 混合变更
                    parts = []
                    if added_files:
                        parts.append(f"add {len(added_files)} file(s)")
                    if modified_files:
                        parts.append(f"update {len(modified_files)} file(s)")
                    if deleted_files:
                        parts.append(f"delete {len(deleted_files)} file(s)")
                    commit_message = f"{', '.join(parts)}"

                commit_message = f"✨ {commit_message}"

            # 执行 git add
            add_result = subprocess.run(
                ['git', 'add', '-A'],
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                cwd=target_dir
            )

            if add_result.returncode != 0:
                return {"success": False, "error": "添加文件到暂存区失败"}

            # 执行 git commit
            commit_result = subprocess.run(
                ['git', 'commit', '-m', commit_message],
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                cwd=target_dir
            )

            if commit_result.returncode != 0:
                return {"success": False, "error": f"提交失败: {commit_result.stderr}"}

            # 获取 commit hash
            hash_result = subprocess.run(
                ['git', 'rev-parse', 'HEAD'],
                capture_output=True,
                encoding='utf-8',
                errors='replace',
                text=True,
                cwd=target_dir
            )
            commit_id = hash_result.stdout.strip() if hash_result.returncode == 0 else None

            # 推送到远程仓库
            push_success = True
            push_error = None
            try:
                # 检查是否有远程仓库
                remote_result = subprocess.run(
                    ['git', 'remote'],
                    capture_output=True,
                    encoding='utf-8',
                    errors='replace',
                    text=True,
                    cwd=target_dir
                )

                if remote_result.returncode == 0 and remote_result.stdout.strip():
                    # 有远程仓库，执行推送
                    push_result = subprocess.run(
                        ['git', 'push'],
                        capture_output=True,
                        encoding='utf-8',
                        errors='replace',
                        text=True,
                        cwd=target_dir,
                        timeout=60
                    )

                    if push_result.returncode != 0:
                        push_success = False
                        push_error = push_result.stderr or "推送失败"
            except subprocess.TimeoutExpired:
                push_success = False
                push_error = "推送超时"
            except Exception as e:
                push_success = False
                push_error = str(e)

            return {
                "success": True,
                "commit_id": commit_id,
                "commit_msg": commit_message,
                "pushed": push_success,
                "push_error": push_error,
                "files": {
                    "added": added_files,
                    "modified": modified_files,
                    "deleted": deleted_files,
                }
            }

        except Exception as e:
            return {"success": False, "error": str(e)}

    def create_conversation(
        self, title: str, project_path: Optional[str] = None
    ) -> int:
        """
        创建新对话

        Args:
            title: 对话标题
            project_path: 项目路径（可选）

        Returns:
            int: 对话 ID
        """
        conv = self._conversation_repo.create(title=title, project_path=project_path)
        return conv.id

    def get_conversation(self, conversation_id: int) -> Optional[ConversationModel]:
        """获取对话"""
        return self._conversation_repo.get_by_id(conversation_id)

    def list_conversations(
        self, project_path: Optional[str] = None, limit: int = 50
    ) -> List[ConversationModel]:
        """获取对话列表"""
        return self._conversation_repo.list_all(limit=limit, project_path=project_path)

    def get_messages(self, conversation_id: int) -> List[MessageModel]:
        """获取对话的消息"""
        return self._message_repo.get_by_conversation(conversation_id)

    async def send_message(
        self,
        conversation_id: int,
        content: str,
        stream: bool = False,
    ) -> MessageModel:
        """
        发送消息并获取 AI 响应

        Args:
            conversation_id: 对话 ID
            content: 用户消息内容
            stream: 是否使用流式响应

        Returns:
            MessageModel: AI 响应消息
        """
        # 保存用户消息
        user_message = self._message_repo.create(
            conversation_id=conversation_id,
            role=MessageRole.USER.value,
            content=content,
        )

        # 获取对话历史（不包括刚刚保存的用户消息，手动添加）
        history = self._message_repo.get_by_conversation(conversation_id)
        # 移除最后一个（刚保存的用户消息），因为我们会手动添加
        history = history[:-1]

        # 构建消息列表
        messages = []
        # 添加历史消息
        for msg in history:
            messages.append(Message(
                role=MessageRole(msg.role),
                content=msg.content,
                timestamp=msg.timestamp,
            ))
        # 添加当前用户消息
        messages.append(Message(
            role=MessageRole.USER,
            content=content,
        ))

        # 获取活动提供商的配置
        from .provider_service import provider_manager

        provider_config = provider_manager.get_active_provider()

        if provider_config:
            ai_config = AIRequestConfig(
                temperature=provider_config.temperature,
                max_tokens=provider_config.max_tokens,
                top_p=provider_config.top_p,
                stream=stream,
            )
        else:
            # 默认配置
            ai_config = AIRequestConfig(
                temperature=0.7,
                max_tokens=4096,
                top_p=1.0,
                stream=stream,
            )

        # 调用 AI
        ai_client = self._get_ai_client()

        if stream:
            # 流式响应
            full_response = ""
            async for chunk in ai_client.chat_stream(messages, ai_config):
                full_response += chunk

            response = AIResponse(
                content=full_response,
                model=ai_client.model,
            )
        else:
            # 普通响应
            response = await ai_client.chat(messages, ai_config)

        # 保存 AI 响应
        ai_message = self._message_repo.create(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT.value,
            content=response.content,
            model=response.model,
            tokens_used=response.usage.get("output_tokens") if response.usage else None,
        )

        return ai_message

    async def send_message_with_tools_stream(
        self,
        conversation_id: int,
        content: str,
        work_dir: Optional[Path] = None,
    ) -> AsyncIterator[str]:
        """
        发送消息并流式获取 AI 响应（支持工具调用）

        Args:
            conversation_id: 对话 ID
            content: 用户消息内容
            work_dir: 工作目录（用于文件操作）

        Yields:
            str: AI 响应片段
        """
        # 设置工作目录
        if work_dir:
            self.set_work_dir(work_dir)
        elif not self._current_work_dir:
            # 如果没有设置工作目录，使用当前目录
            self.set_work_dir(Path.cwd())

        # 保存用户消息
        self._message_repo.create(
            conversation_id=conversation_id,
            role=MessageRole.USER.value,
            content=content,
        )

        # 获取对话历史（不包括刚刚保存的用户消息）
        history = self._message_repo.get_by_conversation(conversation_id)
        # 移除最后一个（刚保存的用户消息）
        history = history[:-1]

        # 构建消息列表
        messages = []
        # 添加历史消息
        for msg in history:
            messages.append(Message(
                role=MessageRole(msg.role),
                content=msg.content,
                timestamp=msg.timestamp,
            ))
        # 添加当前用户消息
        messages.append(Message(
            role=MessageRole.USER,
            content=content,
        ))

        # 获取工具配置
        tools = tool_registry.get_schemas()

        # 获取活动提供商的配置
        from .provider_service import provider_manager

        provider_config = provider_manager.get_active_provider()

        if provider_config:
            ai_config = AIRequestConfig(
                temperature=provider_config.temperature,
                max_tokens=provider_config.max_tokens,
                top_p=provider_config.top_p,
                stream=False,  # 注意：这里会使用内部流式
                tools=tools,
            )
        else:
            # 默认配置
            ai_config = AIRequestConfig(
                temperature=0.7,
                max_tokens=4096,
                top_p=1.0,
                stream=False,
                tools=tools,
            )

        # 添加系统消息，告诉 AI 它可以使用的工具
        system_message = Message(
            role=MessageRole.SYSTEM,
            content="""你是一个 AI 编程助手（类似 Claude Code），可以帮助用户编写、查看和修改代码。

**重要：你的行为模式**
1. 用户直接告诉你"默认使用深色模式"等需求时，这通常是要修改代码实现功能
2. 不要反复询问用户意图，直接使用工具探索和修改代码
3. 先用 Read 工具查看相关文件，然后提出修改方案，最后用 Write 工具修改

**可用工具：**
- Read: 读取文件内容（先读后写！）
- Write: 写入文件内容（会覆盖整个文件）
- Bash: 执行系统命令（git、测试等）
- Glob: 搜索文件（用模式如 **/*.py）

**工作流程：**
用户: "默认使用深色模式"
→ 你: "我来帮你修改代码，让程序默认使用深色模式"
→ 用 Glob 搜索相关文件（如 **/*gui*.py）
→ 用 Read 查看文件内容
→ 解释修改方案
→ 用 Write 写入修改后的代码

工作目录: {work_dir}

**注意事项：**
- 使用 Read 前先用 Glob 找到文件
- Write 会覆盖整个文件，修改前务必先用 Read 读取
- 代码修改后告知用户具体改动""".format(
                work_dir=str(work_dir) if work_dir else "当前目录"
            ),
        )
        messages.insert(0, system_message)

        # 调用 AI（带工具调用的流式响应）
        ai_client = self._get_ai_client()
        full_response = ""

        async for chunk in ai_client.chat_with_tools_stream(
            messages=messages,
            tools=tools,
            tool_executor=self._execute_tool,
            config=ai_config,
            max_iterations=10,
        ):
            full_response += chunk
            yield chunk

        # 保存 AI 响应
        self._message_repo.create(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT.value,
            content=full_response,
            model=ai_client.model,
        )

        # 自动提交：AI 完成响应后，检查是否有更改需要提交
        try:
            from .config_service import config_service
            config = config_service.get_config()

            if config.auto_commit:
                # 使用 AI 生成提交消息
                commit_msg = await self._generate_commit_message(content, full_response)

                if commit_msg is None:
                    # 没有变更需要提交
                    return

                # 执行提交
                commit_result = self.commit_changes(commit_message=commit_msg, force=True)

                if commit_result.get("success"):
                    # 提交成功，输出提示信息
                    yield f"\n\n✅ 已自动提交: {commit_msg}"
                    if commit_result.get("commit_id"):
                        yield f" ({commit_result['commit_id'][:8]})"
                    if commit_result.get("pushed"):
                        yield f" 并已推送到远程仓库"
                elif "没有需要提交的更改" not in commit_result.get("error", ""):
                    # 如果不是因为没更改而失败，显示错误
                    yield f"\n\n⚠️ 自动提交失败: {commit_result.get('error', '')}"
        except Exception as e:
            # 自动提交失败不影响对话
            print(f"自动提交失败: {e}")
            import traceback
            traceback.print_exc()

    async def send_message_with_tools(
        self,
        conversation_id: int,
        content: str,
        work_dir: Optional[Path] = None,
        stream: bool = False,
    ) -> AsyncIterator[str]:
        """
        发送消息并获取 AI 响应（支持工具调用）

        Args:
            conversation_id: 对话 ID
            content: 用户消息内容
            work_dir: 工作目录（用于文件操作）
            stream: 是否使用流式响应

        Yields:
            str: AI 响应片段
        """
        # 设置工作目录
        if work_dir:
            self.set_work_dir(work_dir)
        elif not self._current_work_dir:
            # 如果没有设置工作目录，使用当前目录
            self.set_work_dir(Path.cwd())

        # 保存用户消息
        self._message_repo.create(
            conversation_id=conversation_id,
            role=MessageRole.USER.value,
            content=content,
        )

        # 获取对话历史（不包括刚刚保存的用户消息）
        history = self._message_repo.get_by_conversation(conversation_id)
        # 移除最后一个（刚保存的用户消息）
        history = history[:-1]

        # 构建消息列表
        messages = []
        # 添加历史消息
        for msg in history:
            messages.append(Message(
                role=MessageRole(msg.role),
                content=msg.content,
                timestamp=msg.timestamp,
            ))
        # 添加当前用户消息
        messages.append(Message(
            role=MessageRole.USER,
            content=content,
        ))

        # 获取工具配置
        tools = tool_registry.get_schemas()

        # 获取活动提供商的配置
        from .provider_service import provider_manager

        provider_config = provider_manager.get_active_provider()

        if provider_config:
            ai_config = AIRequestConfig(
                temperature=provider_config.temperature,
                max_tokens=provider_config.max_tokens,
                top_p=provider_config.top_p,
                stream=False,  # 工具调用模式不支持流式
                tools=tools,
            )
        else:
            # 默认配置
            ai_config = AIRequestConfig(
                temperature=0.7,
                max_tokens=4096,
                top_p=1.0,
                stream=False,
                tools=tools,
            )

        # 添加系统消息，告诉 AI 它可以使用的工具
        system_message = Message(
            role=MessageRole.SYSTEM,
            content="""你是一个 AI 编程助手（类似 Claude Code），可以帮助用户编写、查看和修改代码。

**重要：你的行为模式**
1. 用户直接告诉你"默认使用深色模式"等需求时，这通常是要修改代码实现功能
2. 不要反复询问用户意图，直接使用工具探索和修改代码
3. 先用 Read 工具查看相关文件，然后提出修改方案，最后用 Write 工具修改

**可用工具：**
- Read: 读取文件内容（先读后写！）
- Write: 写入文件内容（会覆盖整个文件）
- Bash: 执行系统命令（git、测试等）
- Glob: 搜索文件（用模式如 **/*.py）

**工作流程：**
用户: "默认使用深色模式"
→ 你: "我来帮你修改代码，让程序默认使用深色模式"
→ 用 Glob 搜索相关文件（如 **/*gui*.py）
→ 用 Read 查看文件内容
→ 解释修改方案
→ 用 Write 写入修改后的代码

工作目录: {work_dir}

**注意事项：**
- 使用 Read 前先用 Glob 找到文件
- Write 会覆盖整个文件，修改前务必先用 Read 读取
- 代码修改后告知用户具体改动""".format(
                work_dir=str(work_dir) if work_dir else "当前目录"
            ),
        )
        messages.insert(0, system_message)

        # 调用 AI（带工具调用）
        ai_client = self._get_ai_client()
        response = await ai_client.chat_with_tools(
            messages=messages,
            tools=tools,
            tool_executor=self._execute_tool,
            config=ai_config,
            max_iterations=10,
        )

        # 保存 AI 响应
        self._message_repo.create(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT.value,
            content=response.content,
            model=response.model,
        )

        yield response.content

    async def send_message_stream(
        self,
        conversation_id: int,
        content: str,
    ) -> AsyncIterator[str]:
        """
        发送消息并流式获取 AI 响应（不含工具调用）

        Args:
            conversation_id: 对话 ID
            content: 用户消息内容

        Yields:
            str: AI 响应片段
        """
        # 保存用户消息
        self._message_repo.create(
            conversation_id=conversation_id,
            role=MessageRole.USER.value,
            content=content,
        )

        # 获取对话历史（不包括刚刚保存的用户消息）
        history = self._message_repo.get_by_conversation(conversation_id)
        # 移除最后一个（刚保存的用户消息）
        history = history[:-1]

        # 构建消息列表
        messages = []
        # 添加历史消息
        for msg in history:
            messages.append(Message(
                role=MessageRole(msg.role),
                content=msg.content,
                timestamp=msg.timestamp,
            ))
        # 添加当前用户消息
        messages.append(Message(
            role=MessageRole.USER,
            content=content,
        ))

        # 获取活动提供商的配置
        from .provider_service import provider_manager

        provider_config = provider_manager.get_active_provider()

        if provider_config:
            ai_config = AIRequestConfig(
                temperature=provider_config.temperature,
                max_tokens=provider_config.max_tokens,
                top_p=provider_config.top_p,
                stream=True,
            )
        else:
            # 默认配置
            ai_config = AIRequestConfig(
                temperature=0.7,
                max_tokens=4096,
                top_p=1.0,
                stream=True,
            )

        # 调用 AI
        ai_client = self._get_ai_client()
        full_response = ""

        async for chunk in ai_client.chat_stream(messages, ai_config):
            full_response += chunk
            yield chunk

        # 保存 AI 响应
        self._message_repo.create(
            conversation_id=conversation_id,
            role=MessageRole.ASSISTANT.value,
            content=full_response,
            model=ai_client.model,
        )

    def apply_code_change(
        self,
        message_id: int,
        file_path: str,
        project_path: str,
        original_code: str,
        modified_code: str,
    ) -> int:
        """
        应用代码修改

        Args:
            message_id: 关联的消息 ID
            file_path: 文件路径
            project_path: 项目路径
            original_code: 原始代码
            modified_code: 修改后的代码

        Returns:
            int: 代码修改记录 ID
        """
        from ..database.repositories import CodeChangeRepository
        import difflib

        # 生成 diff
        diff = "".join(
            difflib.unified_diff(
                original_code.splitlines(keepends=True),
                modified_code.splitlines(keepends=True),
                fromfile=f"a{file_path}",
                tofile=f"b{file_path}",
            )
        )

        # 创建代码修改记录
        code_change_repo = CodeChangeRepository(get_db_session())

        config = config_service.get_config()
        branch_name = None

        # 如果配置了自动创建临时分支
        if config.create_temp_branch:
            vcs = get_vcs(project_path)
            if vcs:
                branch_name = vcs.create_temp_branch()

        change = code_change_repo.create(
            message_id=message_id,
            file_path=file_path,
            project_path=project_path,
            original_code=original_code,
            modified_code=modified_code,
            diff=diff,
            branch_name=branch_name,
        )

        return change.id

    def validate_api_key(self) -> bool:
        """验证当前 API 密钥是否有效"""
        try:
            ai_client = self._get_ai_client()
            return ai_client.validate_api_key()
        except Exception:
            return False


# 全局对话服务实例
conversation_service = ConversationService()
