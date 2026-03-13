"""
OpenAI AI 实现
使用 OpenAI API 调用 GPT 模型
"""
import asyncio
from typing import AsyncIterator, List, Optional, Dict, Any
from openai import AsyncOpenAI
import httpx

from .base import BaseAI, Message, MessageRole, AIResponse, AIRequestConfig


class OpenAI(BaseAI):
    """
    OpenAI AI 实现
    支持 GPT-4, GPT-3.5 等模型
    """

    # 支持的模型列表
    SUPPORTED_MODELS = {
        "gpt-4o": "gpt-4o",
        "gpt-4o-mini": "gpt-4o-mini",
        "gpt-4-turbo": "gpt-4-turbo",
        "gpt-4": "gpt-4",
        "gpt-3.5-turbo": "gpt-3.5-turbo",
    }

    def __init__(self, api_key: str, model: str = "gpt-4o", base_url: str = None, **kwargs):
        super().__init__(api_key, model, **kwargs)

        # 设置超时时间（默认 5 分钟）
        timeout = kwargs.get("timeout", 300)

        # 初始化异步客户端
        if base_url:
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=httpx.Timeout(timeout=timeout, connect=60)
            )
        else:
            self.client = AsyncOpenAI(
                api_key=api_key,
                timeout=httpx.Timeout(timeout=timeout, connect=60)
            )

        # 设置默认参数
        self.default_max_tokens = kwargs.get("max_tokens", 4096)

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, str]]:
        """
        转换消息格式为 OpenAI API 格式

        Args:
            messages: 内部消息格式

        Returns:
            List[Dict[str, str]]: OpenAI API 消息格式
        """
        result = []
        system_message = None

        for msg in messages:
            role_mapping = {
                MessageRole.SYSTEM: "system",
                MessageRole.USER: "user",
                MessageRole.ASSISTANT: "assistant",
            }

            # OpenAI 要求 system 消息在最前面
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
            raise RuntimeError(f"OpenAI API 错误: {e}") from e

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
            raise RuntimeError(f"OpenAI 流式请求错误: {e}") from e

    def validate_api_key(self) -> bool:
        """
        验证 API 密钥是否有效

        Returns:
            bool: 密钥是否有效
        """
        try:
            # 使用同步客户端验证
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
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
            "api_base": "https://api.openai.com/v1",
        })
        return info


class OpenAIFactory:
    """OpenAI AI 工厂类"""

    @staticmethod
    def create(api_key: str, model: str = "gpt-4o", **kwargs) -> OpenAI:
        """
        创建 OpenAI AI 实例

        Args:
            api_key: API 密钥
            model: 模型名称
            **kwargs: 其他配置

        Returns:
            OpenAI: OpenAI AI 实例
        """
        if model not in OpenAI.SUPPORTED_MODELS:
            raise ValueError(f"不支持的模型: {model}。支持的模型: {list(OpenAI.SUPPORTED_MODELS.keys())}")

        return OpenAI(api_key=api_key, model=model, **kwargs)
