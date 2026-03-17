"""
AI 客户端工厂
根据 Provider 配置创建对应的 AI 客户端
"""
from typing import Optional
from .provider_service import ProviderManager, ProviderConfig, ProviderType, provider_manager
from ..ai.claude import ClaudeAI
from ..ai.openai_impl import OpenAI
from ..ai.deepseek_impl import DeepSeekAI
from ..ai.base import BaseAI


class AIClientFactory:
    """
    AI 客户端工厂
    根据提供商配置创建相应的 AI 客户端实例
    """

    def __init__(self, provider_manager: Optional[ProviderManager] = None):
        self._provider_manager = provider_manager  # Can be None, will use global when needed

    def _get_provider_manager(self) -> ProviderManager:
        """获取 provider manager，如果未设置则使用全局实例"""
        if self._provider_manager is None:
            return provider_manager
        return self._provider_manager

    def create_client(self, config: ProviderConfig) -> BaseAI:
        """
        根据提供商配置创建 AI 客户端

        Args:
            config: 提供商配置

        Returns:
            BaseAI 实例

        Raises:
            ValueError: 不支持的提供商类型
        """
        provider_type = config.provider_type

        if provider_type == ProviderType.CLAUDE:
            return self._create_claude_client(config)
        elif provider_type == ProviderType.OPENAI:
            return self._create_openai_client(config)
        elif provider_type == ProviderType.DEEPSEEK:
            return self._create_deepseek_client(config)
        elif provider_type == ProviderType.CUSTOM:
            # 根据自定义端点自动判断类型
            return self._create_custom_client(config)
        else:
            raise ValueError(f"不支持的提供商类型: {provider_type}")

    def _create_claude_client(self, config: ProviderConfig) -> ClaudeAI:
        """创建 Claude 客户端"""
        return ClaudeAI(
            api_key=config.api_key,
            model=config.model,
            base_url=config.api_endpoint if config.api_endpoint else None,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            # 添加重试配置
            max_retries=3,  # 最多重试 3 次
            retry_delay=1.0,  # 初始重试延迟 1 秒
            timeout=300,  # 超时时间 5 分钟
        )

    def _create_openai_client(self, config: ProviderConfig) -> OpenAI:
        """创建 OpenAI 客户端"""
        return OpenAI(
            api_key=config.api_key,
            model=config.model,
            base_url=config.api_endpoint if config.api_endpoint else None,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            # 添加重试配置
            max_retries=3,  # 最多重试 3 次
            retry_delay=1.0,  # 初始重试延迟 1 秒
            timeout=300,  # 超时时间 5 分钟
        )

    def _create_deepseek_client(self, config: ProviderConfig) -> DeepSeekAI:
        """创建 DeepSeek 客户端"""
        return DeepSeekAI(
            api_key=config.api_key,
            model=config.model,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            top_p=config.top_p,
            # 添加重试配置
            max_retries=3,  # 最多重试 3 次
            retry_delay=1.0,  # 初始重试延迟 1 秒
            timeout=300,  # 超时时间 5 分钟
        )

    def _create_custom_client(self, config: ProviderConfig) -> BaseAI:
        """
        创建自定义客户端

        根据端点和模型名称自动判断使用哪个实现
        """
        endpoint = config.api_endpoint.lower()
        model = config.model.lower()

        # 判断是否为 Anthropic/Claude 兼容接口
        # 包括官方 API 和常见的中转服务
        claude_keywords = [
            "anthropic", "claude", "bedrock",
            "silkrelay", "relay", "api2p",  # 常见中转服务
            "packy", "siliconflow", "aigocode"
        ]
        if any(keyword in endpoint for keyword in claude_keywords) or "claude" in model or "glm" in model:
            return self._create_claude_client(config)

        # 判断是否为 OpenAI 兼容接口
        openai_keywords = ["openai", "azure", "v1/chat/completions"]
        if any(keyword in endpoint for keyword in openai_keywords):
            return self._create_openai_client(config)

        # 判断是否为 DeepSeek
        deepseek_keywords = ["deepseek", "deepseek.com"]
        if any(keyword in endpoint for keyword in deepseek_keywords) or "deepseek" in model:
            return self._create_deepseek_client(config)

        # 默认使用 Claude 实现（大多数第三方中转服务都是 Anthropic 兼容）
        return self._create_claude_client(config)

    def get_active_client(self) -> Optional[BaseAI]:
        """
        获取当前活动的 AI 客户端
        从本地数据库读取

        Returns:
            BaseAI 实例，如果没有活动提供商则返回 None
        """
        config = self._get_provider_manager().get_active_provider()

        if not config or not config.api_key:
            return None

        return self.create_client(config)

    def get_client_by_id(self, provider_id: str) -> Optional[BaseAI]:
        """
        根据提供商 ID 获取 AI 客户端

        Args:
            provider_id: 提供商 ID

        Returns:
            BaseAI 实例，如果提供商不存在或未配置 API key 则返回 None
        """
        providers = self._get_provider_manager().get_providers()
        for provider in providers:
            if provider.id == provider_id:
                if not provider.api_key:
                    return None
                return self.create_client(provider)
        return None


# 全局 AI 客户端工厂实例
ai_client_factory = AIClientFactory()


def get_ai_client() -> Optional[BaseAI]:
    """
    获取当前活动的 AI 客户端的便捷函数

    Returns:
        BaseAI 实例，如果没有活动提供商则返回 None
    """
    return ai_client_factory.get_active_client()


def create_ai_client(config: ProviderConfig) -> BaseAI:
    """
    根据配置创建 AI 客户端的便捷函数

    Args:
        config: 提供商配置

    Returns:
        BaseAI 实例
    """
    return ai_client_factory.create_client(config)
