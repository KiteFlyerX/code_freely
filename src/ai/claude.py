"""
Claude AI 实现
使用 Anthropic API 调用 Claude 模型，支持工具调用
"""
import asyncio
import json
import uuid
from typing import AsyncIterator, List, Optional, Dict, Any
import anthropic
from anthropic import Anthropic, AsyncAnthropic

from .base import BaseAI, Message, MessageRole, AIResponse, AIRequestConfig, ToolCall


class ClaudeAI(BaseAI):
    """
    Claude AI 实现
    支持 Claude 3 Opus, Sonnet, Haiku 等模型和工具调用
    """

    # 支持的模型列表
    SUPPORTED_MODELS = {
        "claude-opus-4-6": "claude-opus-4-6",
        "claude-sonnet-4-6": "claude-sonnet-4-6",
        "claude-haiku-4-5-20251001": "claude-haiku-4-5-20251001",
        "claude-3-5-sonnet-20241022": "claude-3-5-sonnet-20241022",
        "claude-3-5-haiku-20241022": "claude-3-5-haiku-20241022",
    }

    def __init__(self, api_key: str, model: str = "claude-sonnet-4-6", base_url: str = None, **kwargs):
        super().__init__(api_key, model, **kwargs)

        # 保存 base_url
        self.base_url = base_url

        # 设置超时时间（默认 5 分钟）
        timeout = kwargs.get("timeout", 300)

        # 初始化同步和异步客户端
        if base_url:
            # 使用自定义端点（中转服务）
            import httpx
            timeout_client = httpx.Timeout(timeout=timeout, connect=60)
            self.client = Anthropic(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout_client
            )
            self.async_client = AsyncAnthropic(
                api_key=api_key,
                base_url=base_url,
                timeout=timeout_client
            )
        else:
            # 使用官方端点
            import httpx
            timeout_client = httpx.Timeout(timeout=timeout, connect=60)
            self.client = Anthropic(
                api_key=api_key,
                timeout=timeout_client
            )
            self.async_client = AsyncAnthropic(
                api_key=api_key,
                timeout=timeout_client
            )

        # 设置默认参数
        self.default_max_tokens = kwargs.get("max_tokens", 4096)

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        转换消息格式为 Claude API 格式

        Args:
            messages: 内部消息格式

        Returns:
            List[Dict[str, Any]]: Claude API 消息格式
        """
        result = []
        for msg in messages:
            if msg.role == MessageRole.TOOL:
                # 工具返回消息
                result.append({
                    "role": "user",
                    "content": [
                        {
                            "type": "tool_result",
                            "tool_use_id": msg.tool_call_id,
                            "content": msg.content
                        }
                    ]
                })
            elif msg.role == MessageRole.ASSISTANT and msg.tool_calls:
                # 带工具调用的助手消息
                content = []
                for tool_call in msg.tool_calls:
                    content.append({
                        "type": "tool_use",
                        "id": tool_call.id,
                        "name": tool_call.name,
                        "input": tool_call.arguments
                    })

                # 如果还有文本内容，添加到 content
                if msg.content:
                    content.append({
                        "type": "text",
                        "text": msg.content
                    })

                result.append({
                    "role": "assistant",
                    "content": content
                })
            else:
                # 普通消息
                role_mapping = {
                    MessageRole.SYSTEM: "user",  # Claude 用 user 消息包含系统指令
                    MessageRole.USER: "user",
                    MessageRole.ASSISTANT: "assistant",
                }
                result.append({
                    "role": role_mapping[msg.role],
                    "content": msg.content
                })
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

        # 构建请求参数
        request_params = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": config.max_tokens or self.default_max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "stream": False,
        }

        # 添加工具配置
        if config.tools:
            request_params["tools"] = config.tools

        if config.extra_params:
            request_params.update(config.extra_params)

        try:
            response = await self.async_client.messages.create(**request_params)

            # 解析响应
            content = ""
            tool_calls = []

            for block in response.content:
                if block.type == "text":
                    content += block.text
                elif block.type == "tool_use":
                    tool_calls.append(ToolCall(
                        id=block.id,
                        name=block.name,
                        arguments=block.input,
                    ))

            return AIResponse(
                content=content,
                model=response.model,
                finish_reason=response.stop_reason,
                usage={
                    "input_tokens": response.usage.input_tokens,
                    "output_tokens": response.usage.output_tokens,
                },
                raw_response=response,
                tool_calls=tool_calls if tool_calls else None,
            )

        except anthropic.APIError as e:
            raise RuntimeError(f"Claude API 错误: {e}") from e
        except Exception as e:
            raise RuntimeError(f"请求失败: {e}") from e

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

        # 构建请求参数
        request_params = {
            "model": self.model,
            "messages": api_messages,
            "max_tokens": config.max_tokens or self.default_max_tokens,
            "temperature": config.temperature,
            "top_p": config.top_p,
            "stream": True,
        }

        if config.tools:
            request_params["tools"] = config.tools

        if config.extra_params:
            request_params.update(config.extra_params)

        try:
            stream = await self.async_client.messages.create(**request_params)

            async for event in stream:
                if event.type == "content_block_delta":
                    if hasattr(event.delta, 'text'):
                        yield event.delta.text

        except anthropic.APIError as e:
            raise RuntimeError(f"Claude API 错误: {e}") from e
        except Exception as e:
            raise RuntimeError(f"流式请求失败: {e}") from e

    def validate_api_key(self) -> bool:
        """
        验证 API 密钥是否有效

        Returns:
            bool: 密钥是否有效
        """
        try:
            # 发送一个简单的请求来验证密钥
            response = self.client.messages.create(
                model=self.model,
                messages=[{"role": "user", "content": "Hi"}],
                max_tokens=10
            )
            return True
        except anthropic.AuthenticationError:
            return False
        except Exception:
            return False

    def get_model_info(self) -> Dict[str, Any]:
        """获取模型信息"""
        info = super().get_model_info()
        info.update({
            "supported_models": list(self.SUPPORTED_MODELS.keys()),
            "api_base": "https://api.anthropic.com",
        })
        return info


class ClaudeAIFactory:
    """Claude AI 工厂类"""

    @staticmethod
    def create(api_key: str, model: str = "claude-sonnet-4-6", **kwargs) -> ClaudeAI:
        """
        创建 Claude AI 实例

        Args:
            api_key: API 密钥
            model: 模型名称
            **kwargs: 其他配置

        Returns:
            ClaudeAI: Claude AI 实例
        """
        if model not in ClaudeAI.SUPPORTED_MODELS:
            raise ValueError(f"不支持的模型: {model}。支持的模型: {list(ClaudeAI.SUPPORTED_MODELS.keys())}")

        return ClaudeAI(api_key=api_key, model=model, **kwargs)
