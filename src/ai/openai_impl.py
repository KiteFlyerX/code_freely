"""
OpenAI AI 实现
使用 OpenAI API 调用 GPT 模型
"""
import asyncio
import json
from typing import AsyncIterator, List, Optional, Dict, Any
from openai import AsyncOpenAI
import httpx

from .base import BaseAI, Message, MessageRole, AIResponse, AIRequestConfig, ToolCall


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
        
        # 获取重试配置
        self.max_retries = kwargs.get("max_retries", 3)
        self.retry_delay = kwargs.get("retry_delay", 1.0)

        # 初始化异步客户端
        if base_url:
            self.client = AsyncOpenAI(
                api_key=api_key,
                base_url=base_url,
                timeout=httpx.Timeout(timeout=timeout, connect=60),
                max_retries=0  # 禁用内置重试，我们自己实现
            )
        else:
            self.client = AsyncOpenAI(
                api_key=api_key,
                timeout=httpx.Timeout(timeout=timeout, connect=60),
                max_retries=0
            )

        # 设置默认参数
        self.default_max_tokens = kwargs.get("max_tokens", 4096)

    def _convert_messages(self, messages: List[Message]) -> List[Dict[str, Any]]:
        """
        转换消息格式为 OpenAI API 格式

        Args:
            messages: 内部消息格式

        Returns:
            List[Dict[str, Any]]: OpenAI API 消息格式
        """
        result = []
        system_message = None

        for msg in messages:
            if msg.role == MessageRole.TOOL:
                # 工具返回消息
                result.append({
                    "role": "tool",
                    "tool_call_id": msg.tool_call_id,
                    "content": msg.content
                })
            elif msg.role == MessageRole.ASSISTANT and msg.tool_calls:
                # 带工具调用的助手消息
                tool_calls = []
                for tool_call in msg.tool_calls:
                    tool_calls.append({
                        "id": tool_call.id,
                        "type": "function",
                        "function": {
                            "name": tool_call.name,
                            "arguments": json.dumps(tool_call.arguments)
                        }
                    })

                result.append({
                    "role": "assistant",
                    "content": msg.content or "",
                    "tool_calls": tool_calls
                })
            else:
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

    async def _retry_stream_request(self, request_func, *args, **kwargs):
        """
        带重试的流式请求
        
        Args:
            request_func: 请求函数
            *args: 位置参数
            **kwargs: 关键字参数
            
        Yields:
            流式响应块
        """
        last_error = None
        
        for attempt in range(self.max_retries):
            try:
                stream = await request_func(*args, **kwargs)
                async for chunk in stream:
                    yield chunk
                return  # 成功完成，退出重试
            except (ConnectionError, OSError, TimeoutError) as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # 指数退避
                    delay = self.retry_delay * (2 ** attempt)
                    print(f"[OPENAI API] 连接中断，{delay}秒后重试 (尝试 {attempt + 1}/{self.max_retries}): {e}")
                    await asyncio.sleep(delay)
                else:
                    print(f"[OPENAI API] 重试失败，已达最大重试次数: {e}")
            except Exception as e:
                # 其他异常不重试
                raise RuntimeError(f"OpenAI API 错误: {e}") from e
        
        # 所有重试都失败
        raise RuntimeError(f"流式请求失败（已重试 {self.max_retries} 次）: {last_error}") from last_error

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
            response = await self.client.chat.completions.create(**request_params)

            choice = response.choices[0]

            # 解析工具调用
            tool_calls = []
            if choice.message.tool_calls:
                for tc in choice.message.tool_calls:
                    tool_calls.append(ToolCall(
                        id=tc.id,
                        name=tc.function.name,
                        arguments=json.loads(tc.function.arguments),
                    ))

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
                tool_calls=tool_calls if tool_calls else None,
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
            async for chunk in self._retry_stream_request(
                self.client.chat.completions.create,
                model=self.model,
                messages=api_messages,
                max_tokens=config.max_tokens or self.default_max_tokens,
                temperature=config.temperature,
                top_p=config.top_p,
                stream=True,
                **config.extra_params
            ):
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
