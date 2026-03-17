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

            usage_info = {
                "input_tokens": response.usage.input_tokens,
                "output_tokens": response.usage.output_tokens,
                "total_tokens": response.usage.input_tokens + response.usage.output_tokens,
            }
            self._set_last_usage(usage_info)

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

        # 用于收集 usage 信息
        usage_info = {"input_tokens": 0, "output_tokens": 0}

        try:
            stream = await self.async_client.messages.create(**request_params)

            async for event in stream:
                if event.type == "message_start":
                    if hasattr(event, 'usage') and event.usage:
                        usage_info["input_tokens"] = event.usage.input_tokens

                elif event.type == "content_block_delta":
                    if hasattr(event.delta, 'text'):
                        yield event.delta.text

                elif event.type == "message_delta":
                    if hasattr(event, 'usage') and event.usage:
                        usage_info["output_tokens"] = event.usage.output_tokens

        except anthropic.APIError as e:
            raise RuntimeError(f"Claude API 错误: {e}") from e
        except Exception as e:
            raise RuntimeError(f"流式请求失败: {e}") from e
        finally:
            # 保存 usage 信息
            usage_info["total_tokens"] = usage_info.get("input_tokens", 0) + usage_info.get("output_tokens", 0)
            self._set_last_usage(usage_info)

    async def chat_stream_with_tools(
        self,
        messages: List[Message],
        config: Optional[AIRequestConfig] = None
    ) -> tuple[AsyncIterator[str], List[ToolCall]]:
        """
        流式聊天请求，同时收集工具调用

        Args:
            messages: 消息列表
            config: 请求配置

        Returns:
            tuple: (流式文本迭代器, 工具调用列表)
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
            "stream": True,
        }

        if config.tools:
            request_params["tools"] = config.tools

        if config.extra_params:
            request_params.update(config.extra_params)

        tool_calls = []
        current_tool = None

        # 用于收集 usage 信息
        usage_info = {"input_tokens": 0, "output_tokens": 0}

        async def text_generator():
            nonlocal current_tool
            try:
                stream = await self.async_client.messages.create(**request_params)

                async for event in stream:
                    if event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            # 开始新的工具调用
                            current_tool = ToolCall(
                                id=event.content_block.id,
                                name=event.content_block.name,
                                arguments={}
                            )
                            tool_calls.append(current_tool)

                    elif event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            # 文本内容
                            yield event.delta.text
                        elif event.delta.type == "input_json_delta":
                            # 工具参数增量
                            if current_tool:
                                import json
                                partial = event.delta.partial_json
                                try:
                                    # 尝试解析累积的参数
                                    if not hasattr(current_tool, '_partial_args'):
                                        current_tool._partial_args = ""
                                    current_tool._partial_args += partial
                                    # 尝试解析为完整的 JSON
                                    current_tool.arguments = json.loads(current_tool._partial_args)
                                except json.JSONDecodeError:
                                    # 还不完整，继续累积
                                    pass

                    elif event.type == "content_block_stop":
                        # 内容块结束
                        current_tool = None

                    elif event.type == "message_delta":
                        # 消息结束，可能包含 usage 信息
                        if hasattr(event, 'usage') and event.usage:
                            if hasattr(event.usage, 'output_tokens'):
                                usage_info["output_tokens"] = event.usage.output_tokens

                    elif event.type == "message_stop":
                        # 整个消息流结束，获取最终的 usage
                        # 注意：Anthropic 的流式响应中，input_tokens 在开始时已知
                        # output_tokens 在 message_delta 中累计
                        # 我们需要从响应中获取完整信息
                        pass

            except anthropic.APIError as e:
                raise RuntimeError(f"Claude API 错误: {e}") from e
            except Exception as e:
                raise RuntimeError(f"流式请求失败: {e}") from e

        # 保存 usage 信息以便外部访问
        # 注意：由于流式响应的特性，input_tokens 需要从 API 响应的开头获取
        # 这里我们创建一个包装器来捕获完整的 usage
        async def wrapper():
            # 首先发起请求以获取 input_tokens（在流开始前）
            nonlocal usage_info
            try:
                # 创建一个非流式请求来获取 input_tokens
                # 由于流式响应的 input_tokens 在响应头中，我们需要特殊处理
                # 临时方案：使用流式响应，但捕获所有事件
                stream = await self.async_client.messages.create(**request_params)

                input_tokens = None
                async for event in stream:
                    if event.type == "message_start":
                        if hasattr(event, 'usage') and event.usage:
                            usage_info["input_tokens"] = event.usage.input_tokens

                    # 同时处理文本生成
                    if event.type == "content_block_delta":
                        if event.delta.type == "text_delta":
                            yield event.delta.text
                        elif event.delta.type == "input_json_delta":
                            # 工具调用处理
                            pass

                    elif event.type == "content_block_start":
                        if event.content_block.type == "tool_use":
                            current_tool = ToolCall(
                                id=event.content_block.id,
                                name=event.content_block.name,
                                arguments={}
                            )
                            tool_calls.append(current_tool)

                    elif event.type == "content_block_stop":
                        current_tool = None

                    elif event.type == "message_delta":
                        if hasattr(event, 'usage') and event.usage:
                            usage_info["output_tokens"] = event.usage.output_tokens

            except anthropic.APIError as e:
                raise RuntimeError(f"Claude API 错误: {e}") from e
            except Exception as e:
                raise RuntimeError(f"流式请求失败: {e}") from e
            finally:
                # 保存最终的 usage 信息
                usage_info["total_tokens"] = usage_info.get("input_tokens", 0) + usage_info.get("output_tokens", 0)
                self._set_last_usage(usage_info)

        return wrapper(), tool_calls

    async def chat_stream_collect_tools(
        self,
        messages: List[Message],
        config: Optional[AIRequestConfig] = None
    ) -> tuple[AsyncIterator[str], List[ToolCall]]:
        """
        流式聊天请求，同时收集工具调用（base.py 调用的方法）

        Args:
            messages: 消息列表
            config: 请求配置

        Returns:
            tuple: (流式文本迭代器, 工具调用列表)
        """
        return await self.chat_stream_with_tools(messages, config)

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
