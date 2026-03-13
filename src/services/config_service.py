"""
配置服务
管理 API 密钥、模型参数等配置
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any
from dataclasses import dataclass, asdict

from ..database import get_db_session
from ..database.repositories import ConfigRepository


@dataclass
class AIConfig:
    """AI 配置"""
    provider: str = "claude"  # claude, openai, deepseek
    model: str = "claude-sonnet-4-6"
    api_key: str = ""
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return asdict(self)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AIConfig":
        """从字典创建"""
        return cls(**data)


@dataclass
class AppConfig:
    """应用配置"""
    # AI 配置
    ai: AIConfig = None

    # 其他配置
    default_project_path: str = ""
    auto_commit: bool = True
    create_temp_branch: bool = True
    theme: str = "auto"  # light, dark, auto

    def __post_init__(self):
        if self.ai is None:
            self.ai = AIConfig()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "ai": self.ai.to_dict() if self.ai else {},
            "default_project_path": self.default_project_path,
            "auto_commit": self.auto_commit,
            "create_temp_branch": self.create_temp_branch,
            "theme": self.theme,
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "AppConfig":
        """从字典创建"""
        ai_data = data.get("ai", {})
        return cls(
            ai=AIConfig.from_dict(ai_data) if ai_data else AIConfig(),
            default_project_path=data.get("default_project_path", ""),
            auto_commit=data.get("auto_commit", True),
            create_temp_branch=data.get("create_temp_branch", True),
            theme=data.get("theme", "auto"),
        )


class ConfigService:
    """
    配置服务
    管理应用配置的加载和保存
    """

    def __init__(self):
        self._config: Optional[AppConfig] = None
        self._config_dir = Path.home() / ".codetrace"
        self._config_file = self._config_dir / "config.json"

    def _ensure_config_dir(self):
        """确保配置目录存在"""
        self._config_dir.mkdir(parents=True, exist_ok=True)

    def load_config(self) -> AppConfig:
        """加载配置"""
        if self._config is not None:
            return self._config

        self._ensure_config_dir()

        if self._config_file.exists():
            try:
                with open(self._config_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                self._config = AppConfig.from_dict(data)
            except Exception:
                self._config = AppConfig()
        else:
            self._config = AppConfig()
            self.save_config()

        return self._config

    def save_config(self) -> None:
        """保存配置"""
        if self._config is None:
            return

        self._ensure_config_dir()

        with open(self._config_file, "w", encoding="utf-8") as f:
            json.dump(self._config.to_dict(), f, indent=2, ensure_ascii=False)

    def get_config(self) -> AppConfig:
        """获取配置"""
        if self._config is None:
            return self.load_config()
        return self._config

    def update_ai_config(self, **kwargs) -> None:
        """更新 AI 配置"""
        config = self.get_config()
        for key, value in kwargs.items():
            if hasattr(config.ai, key):
                setattr(config.ai, key, value)
        self.save_config()

    def update_app_config(self, **kwargs) -> None:
        """更新应用配置"""
        config = self.get_config()
        for key, value in kwargs.items():
            if hasattr(config, key):
                setattr(config, key, value)
        self.save_config()

    def get_ai_api_key(self, provider: str) -> str:
        """
        获取 AI API 密钥
        优先从配置文件读取，如果为空则从环境变量读取
        """
        import os

        config = self.get_config()

        # 如果配置的 provider 匹配，返回配置的密钥
        if config.ai.provider == provider and config.ai.api_key:
            return config.ai.api_key

        # 从环境变量读取
        env_keys = {
            "claude": "ANTHROPIC_API_KEY",
            "openai": "OPENAI_API_KEY",
            "deepseek": "DEEPSEEK_API_KEY",
        }

        env_key = env_keys.get(provider.lower())
        if env_key:
            return os.environ.get(env_key, "")

        return ""

    def save_api_key(self, provider: str, api_key: str) -> None:
        """保存 API 密钥"""
        config = self.get_config()
        if config.ai.provider == provider:
            config.ai.api_key = api_key
            self.save_config()


# 全局配置服务实例
config_service = ConfigService()
