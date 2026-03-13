"""
AI 模块
提供统一的 AI 接口抽象和多种 AI 提供商实现
"""
from .base import (
    BaseAI,
    Message,
    MessageRole,
    AIResponse,
    AIRequestConfig,
)
from .claude import ClaudeAI, ClaudeAIFactory
from .openai_impl import OpenAI, OpenAIFactory
from .deepseek_impl import DeepSeekAI, DeepSeekAIFactory

__all__ = [
    # 基础类
    "BaseAI",
    "Message",
    "MessageRole",
    "AIResponse",
    "AIRequestConfig",
    # Claude 实现
    "ClaudeAI",
    "ClaudeAIFactory",
    # OpenAI 实现
    "OpenAI",
    "OpenAIFactory",
    # DeepSeek 实现
    "DeepSeekAI",
    "DeepSeekAIFactory",
]

# AI 提供商注册表
AI_PROVIDERS = {
    "claude": ClaudeAIFactory,
    "openai": OpenAIFactory,
    "deepseek": DeepSeekAIFactory,
}


def get_ai_provider(provider_name: str):
    """
    获取 AI 提供商工厂

    Args:
        provider_name: 提供商名称 (claude, openai, deepseek)

    Returns:
        AI 提供商工厂类
    """
    provider = AI_PROVIDERS.get(provider_name.lower())
    if provider is None:
        available = ", ".join(AI_PROVIDERS.keys())
        raise ValueError(f"不支持的 AI 提供商: {provider_name}。可用: {available}")
    return provider
