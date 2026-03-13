"""
DeepSeek AI 实现
使用 OpenAI 兼容的 API 调用 DeepSeek 模型
"""
import asyncio
from typing import AsyncIterator, List, Optional, Dict, Any
from openai import AsyncOpenAI
import httpx

from .base import BaseAI, Message, MessageRole, AIResponse, AIRequestConfig


class DeepSeekAI(BaseAI):
    """
    DeepSeek AI 实现
    支持 DeepSeek-V3, DeepSeek-Coder 等模型
    """

    # 支持的模型列表
    SUPPORTED_MODELS = {
        "deepseek-chat": "deepseek-chat",
        "deepseek-coder": "deepseek-coder",
        "deepseek-reasoner": "deepseek-reasoner",
    }

    # DeepSeek API 基础 URL
    API_BASE = "https://api.deepseek.com"

    def __init__(self, api_key: str, model: str = "deepseek-chat", **kwargs):
        super().__init__(api_key, model, **kwargs)

        # 设置超时时间（默认 5 分钟）
        timeout = kwargs.get("timeout", 300)

        # 初始化异步客户端（使用 DeepSeek 的 API 端点）
        self.client = AsyncOpenAI(
            api_key=api_key,
            base_url=self.API_BASE,
            timeout=httpx.Timeout(timeout=timeout, connect=60)
        )

        # 设置默认参数
        self.default_max_tokens = kwargs.get("max_tokens", 4096)

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """
        转换消息格式为 DeepSeek API 格式

        Args:
            messages: 内部消息格式

        Returns:
            List[Dict[str, str]]: DeepSeek API 消息格式
        """
        result = []
        system_message = None

        for msg in messages:
            role_mapping = {
                MessageRole.SYSTEM: "system",
                MessageRole.USER: "user",
                MessageRole.ASSISTANT: "assistant",
            }

            # DeepSeek 要求 system 消息在最前面
            if msg.role == MessageRole.SYSTEM:
                system_message = {
                    "role": role_mapping[msg.role],
                    "content": msg.content
                }
            else:
                result.append({
                    "role": role_mapping[msg.role],
                    "content": msg.content
                })

        # 如果有 system 消息，放在最前面
        if system_message:
            result.insert(0, system_message)

        return result

    async def chat(
        self,
        messages: List[Message],
        config: Optional[AIRequestConfig] = None
    ) -> AIResponse:
        """
        发送聊天请求

        Args:
            messages: 消息列表
            config: 请求配置

        Returns:
            AIResponse: AI 响应结果
        """
        if config is None:
            config = AIRequestConfig()

        api_messages = self._convert_messages(messages)

        try:
            response = await self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                max_tokens=config.max_tokens or self.default_max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                stream=False,
                **config.extra_params
            )

            choice = response.choices[0]

            return AIResponse(
                content=choice.message.content or "",
                model=response.model,
                finish_reason=choice.finish_reason,
                usage={
                    "prompt_tokens": response.usage.prompt_tokens,
                    "completion_tokens": response.usage.completion_tokens,
                    "total_tokens": response.usage.total_tokens,
                },
                raw_response=response,
            )

        except Exception as e:
            raise RuntimeError(f"DeepSeek API 错误: {e}") from e

    async def chat_stream(
        self,
        messages: List[Message],
        config: Optional[AIRequestConfig] = None
    ) -> AsyncIterator[str]:
        """
        流式聊天请求

        Args:
            messages: 消息列表
            config: 请求配置

        Yields:
            str: 流式响应片段
        """
        if config is None:
            config = AIRequestConfig()
            config.stream = True

        api_messages = self._convert_messages(messages)

        try:
            stream = await self.client.chat.completions.create(
                model=self.model,
                messages=api_messages,
                max_tokens=config.max_tokens or self.default_max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                stream=True,
                **config.extra_params
            )

            async for chunk in stream:
                if chunk.choices and chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise RuntimeError(f"DeepSeek 流式请求错误: {e}") from e

    def validate_api_key(self) -> bool:
        """
        验证 API 密钥是否有效

        Returns:
            bool: 密钥是否有效
        """
        try:
            # 使用同步客户端验证
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key, base_url=self.API_BASE)
            response = client.chat.completions.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            return True
        except Exception:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        info = super().get_model_info()
        info.update({
            "supported_models": list(self.SUPPORTED_MODELS.keys()),
            "api_base": self.API_BASE,
        })
        return info


class DeepSeekAIFactory:
    """DeepSeek AI 工厂类"""

    @staticmethod
    def create(api_key: str, model: str = "deepseek-chat", **kwargs) -> DeepSeekAI:
        """
        创建 DeepSeek AI 实例

        Args:
            api_key: API 密钥
            model: 模型名称
            **kwargs: 其他配置

        Returns:
            DeepSeekAI: DeepSeek AI 实例
        """
        if model not in DeepSeekAI.SUPPORTED_MODELS:
            raise ValueError(f"不支持的模型: {model}。支持的模型: {list(DeepSeekAI.SUPPORTED_MODELS.keys())}")

        return DeepSeekAI(api_key=api_key, model=model, **kwargs)
