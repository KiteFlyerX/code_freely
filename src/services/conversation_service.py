"""
对话服务
处理与 AI 的对话交互
"""
import asyncio
from typing import List, Optional, AsyncIterator
from datetime import datetime

from ..ai import BaseAI, Message, MessageRole, AIResponse, AIRequestConfig
from ..database import get_db_session
from ..database.repositories import ConversationRepository, MessageRepository
from ..models import Conversation as ConversationModel, ConversationMessage as MessageModel
from .config_service import config_service
from ..vcs import get_vcs


class ConversationService:
    """
    对话服务
    管理 AI 对话、消息存储和代码修改记录
    """

    def __init__(self):
        self._ai_client: Optional[BaseAI] = None
        self._conversation_repo = ConversationRepository(get_db_session())
        self._message_repo = MessageRepository(get_db_session())

    def _get_ai_client(self) -> BaseAI:
        """获取 AI 客户端"""
        if self._ai_client is None:
            from .ai_client_factory import get_ai_client

            self._ai_client = get_ai_client()

            if not self._ai_client:
                raise ValueError("未配置有效的 AI 提供商，请先配置提供商和 API 密钥")

        return self._ai_client

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
        self._message_repo.create(
            conversation_id=conversation_id,
            role=MessageRole.USER.value,
            content=content,
        )

        # 获取对话历史
        history = self._message_repo.get_by_conversation(conversation_id)

        # 转换为 AI 消息格式
        messages = [
            Message(
                role=MessageRole(msg.role),
                content=msg.content,
                timestamp=msg.timestamp,
            )
            for msg in history
        ]

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

    async def send_message_stream(
        self,
        conversation_id: int,
        content: str,
    ) -> AsyncIterator[str]:
        """
        发送消息并流式获取 AI 响应

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

        # 获取对话历史（不包括刚刚保存的用户消息，因为需要 AI 格式）
        history = self._message_repo.get_by_conversation(conversation_id)

        # 转换为 AI 消息格式
        messages = [
            Message(
                role=MessageRole(msg.role),
                content=msg.content,
                timestamp=msg.timestamp,
            )
            for msg in history
        ]

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
