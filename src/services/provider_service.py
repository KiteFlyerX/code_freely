"""
Provider 管理系统
参考 cc-switch 设计，统一管理 AI 提供商配置
"""
from dataclasses import dataclass, field
from typing import Optional, Dict, List, Any
from enum import Enum
from datetime import datetime
from pathlib import Path
import json
import hashlib

from ..database.manager import get_db_session
from ..models.database import SystemConfig


class ProviderType(Enum):
    """提供商类型"""
    CLAUDE = "claude"
    OPENAI = "openai"
    DEEPSEEK = "deepseek"
    CUSTOM = "custom"


@dataclass
class ProviderConfig:
    """AI 提供商配置"""
    id: str = ""
    name: str = ""
    provider_type: ProviderType = ProviderType.CUSTOM

    # API 配置
    api_key: str = ""
    api_endpoint: str = ""
    model: str = ""

    # 参数
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: float = 1.0

    # 代理配置
    proxy_url: str = ""
    proxy_enabled: bool = False

    # 状态
    is_active: bool = False
    is_enabled: bool = True

    # 元数据
    created_at: datetime = None
    updated_at: datetime = None

    # 自定义参数（扩展字段）
    custom_params: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.updated_at is None:
            self.updated_at = datetime.now()

    def to_dict(self) -> Dict[str, Any]:
        """转换为字典"""
        return {
            "id": self.id,
            "name": self.name,
            "provider_type": self.provider_type.value,
            "api_key": self.api_key,
            "api_endpoint": self.api_endpoint,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "top_p": self.top_p,
            "proxy_url": self.proxy_url,
            "proxy_enabled": self.proxy_enabled,
            "is_active": self.is_active,
            "is_enabled": self.is_enabled,
            "custom_params": self.custom_params,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ProviderConfig":
        """从字典创建"""
        return cls(
            id=data.get("id", ""),
            name=data.get("name", ""),
            provider_type=ProviderType(data.get("provider_type", "custom")),
            api_key=data.get("api_key", ""),
            api_endpoint=data.get("api_endpoint", ""),
            model=data.get("model", ""),
            temperature=data.get("temperature", 0.7),
            max_tokens=data.get("max_tokens", 4096),
            top_p=data.get("top_p", 1.0),
            proxy_url=data.get("proxy_url", ""),
            proxy_enabled=data.get("proxy_enabled", False),
            is_active=data.get("is_active", False),
            is_enabled=data.get("is_enabled", True),
            custom_params=data.get("custom_params", {}),
            created_at=datetime.fromisoformat(data["created_at"]) if data.get("created_at") else None,
            updated_at=datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else None,
        )


@dataclass
class ProviderPreset:
    """提供商预设配置"""
    id: str
    name: str
    description: str
    category: str
    config: ProviderConfig


# 预设配置
PROVIDER_PRESETS: List[ProviderPreset] = [
    # Claude 预设
    ProviderPreset(
        id="claude-official",
        name="Claude 官方",
        description="Anthropic 官方 API",
        category="claude",
        config=ProviderConfig(
            id="claude-official",
            name="Claude 官方",
            provider_type=ProviderType.CLAUDE,
            api_endpoint="https://api.anthropic.com",
            model="claude-sonnet-4-6",
        )
    ),
    ProviderPreset(
        id="claude-aws-bedrock",
        name="AWS Bedrock",
        description="AWS Bedrock Claude",
        category="claude",
        config=ProviderConfig(
            id="claude-aws-bedrock",
            name="Claude (AWS Bedrock)",
            provider_type=ProviderType.CLAUDE,
            api_endpoint="https://bedrock-runtime.us-east-1.amazonaws.com",
            model="anthropic.claude-3-sonnet-20240229-v1:0",
        )
    ),

    # OpenAI 预设
    ProviderPreset(
        id="openai-official",
        name="OpenAI 官方",
        description="OpenAI 官方 API",
        category="openai",
        config=ProviderConfig(
            id="openai-official",
            name="OpenAI 官方",
            provider_type=ProviderType.OPENAI,
            api_endpoint="https://api.openai.com/v1",
            model="gpt-4o",
        )
    ),
    ProviderPreset(
        id="openai-azure",
        name="Azure OpenAI",
        description="Azure OpenAI 服务",
        category="openai",
        config=ProviderConfig(
            id="openai-azure",
            name="OpenAI (Azure)",
            provider_type=ProviderType.OPENAI,
            api_endpoint="https://{your-resource}.openai.azure.com",
            model="gpt-4o",
        )
    ),

    # DeepSeek 预设
    ProviderPreset(
        id="deepseek-official",
        name="DeepSeek 官方",
        description="DeepSeek 官方 API",
        category="deepseek",
        config=ProviderConfig(
            id="deepseek-official",
            name="DeepSeek 官方",
            provider_type=ProviderType.DEEPSEEK,
            api_endpoint="https://api.deepseek.com",
            model="deepseek-chat",
        )
    ),

    # 第三方中转服务预设
    ProviderPreset(
        id="packycode",
        name="PackyCode",
        description="PackyCode 中转服务",
        category="relay",
        config=ProviderConfig(
            id="packycode",
            name="PackyCode",
            provider_type=ProviderType.CLAUDE,
            api_endpoint="https://api2.packycode.com/v1",
            model="claude-sonnet-4-6",
        )
    ),
]


class ProviderManager:
    """
    Provider 管理器
    参考 cc-switch 设计，统一管理 AI 提供商配置
    """

    def __init__(self):
        self._db_manager = None  # Lazy initialization

    def _get_session(self):
        """获取数据库会话"""
        return get_db_session()

    def get_providers(self) -> List[ProviderConfig]:
        """获取所有提供商配置（带重试机制）"""
        import time
        max_retries = 3
        retry_delay = 0.1

        for attempt in range(max_retries):
            session = self._get_session()
            try:
                configs = session.query(SystemConfig).filter(
                    SystemConfig.key.like("provider_%")
                ).all()

                providers = []
                for cfg in configs:
                    try:
                        provider_data = json.loads(cfg.value)
                        providers.append(ProviderConfig.from_dict(provider_data))
                    except (json.JSONDecodeError, ValueError):
                        continue

                return providers
            except Exception as e:
                error_str = str(e).lower()
                if ("database is locked" in error_str or "locked" in error_str) and attempt < max_retries - 1:
                    time.sleep(retry_delay)
                    continue
                raise
            finally:
                session.close()

    def get_active_provider(self) -> Optional[ProviderConfig]:
        """获取当前活动的提供商"""
        session = self._get_session()
        try:
            active_cfg = session.query(SystemConfig).filter(
                SystemConfig.key == "active_provider_id"
            ).first()

            active_id = active_cfg.value if active_cfg else None

            if active_id:
                # 直接查询提供商配置，避免嵌套调用 get_providers
                provider_cfg = session.query(SystemConfig).filter(
                    SystemConfig.key == f"provider_{active_id}"
                ).first()

                if provider_cfg:
                    try:
                        return ProviderConfig.from_dict(json.loads(provider_cfg.value))
                    except (json.JSONDecodeError, ValueError):
                        pass

            # 返回默认提供商
            return self.get_default_provider()
        finally:
            session.close()

    def get_default_provider(self) -> Optional[ProviderConfig]:
        """获取默认提供商"""
        session = self._get_session()
        try:
            default_cfg = session.query(SystemConfig).filter(
                SystemConfig.key == "default_provider_id"
            ).first()

            default_id = default_cfg.value if default_cfg else None

            if default_id:
                # 直接查询提供商配置
                provider_cfg = session.query(SystemConfig).filter(
                    SystemConfig.key == f"provider_{default_id}"
                ).first()

                if provider_cfg:
                    try:
                        provider = ProviderConfig.from_dict(json.loads(provider_cfg.value))
                        if provider.is_enabled:
                            return provider
                    except (json.JSONDecodeError, ValueError):
                        pass

            # 返回第一个启用的提供商（直接查询）
            configs = session.query(SystemConfig).filter(
                SystemConfig.key.like("provider_%")
            ).all()

            for cfg in configs:
                try:
                    provider = ProviderConfig.from_dict(json.loads(cfg.value))
                    if provider.is_enabled:
                        return provider
                except (json.JSONDecodeError, ValueError):
                    continue

            return None
        finally:
            session.close()

    def _set_config(self, key: str, value: str):
        """设置配置项（带重试机制）"""
        import time
        max_retries = 5
        retry_delay = 0.2  # 200ms

        for attempt in range(max_retries):
            session = self._get_session()
            try:
                config = session.query(SystemConfig).filter(
                    SystemConfig.key == key
                ).first()

                if config:
                    config.value = value
                else:
                    config = SystemConfig(key=key, value=value)
                    session.add(config)

                session.commit()
                return
            except Exception as e:
                session.rollback()
                error_str = str(e).lower()
                if ("database is locked" in error_str or "locked" in error_str) and attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # 指数退避
                    continue
                raise
            finally:
                session.close()

    def _get_config(self, key: str) -> Optional[str]:
        """获取配置项"""
        session = self._get_session()
        try:
            config = session.query(SystemConfig).filter(
                SystemConfig.key == key
            ).first()
            return config.value if config else None
        finally:
            session.close()

    def _delete_config(self, key: str):
        """删除配置项（带重试机制）"""
        import time
        max_retries = 5
        retry_delay = 0.2

        for attempt in range(max_retries):
            session = self._get_session()
            try:
                config = session.query(SystemConfig).filter(
                    SystemConfig.key == key
                ).first()
                if config:
                    session.delete(config)
                    session.commit()
                return
            except Exception as e:
                session.rollback()
                error_str = str(e).lower()
                if ("database is locked" in error_str or "locked" in error_str) and attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))
                    continue
                raise
            finally:
                session.close()

    def add_provider(self, config: ProviderConfig) -> bool:
        """添加提供商配置"""
        import time
        max_retries = 5
        retry_delay = 0.2  # 200ms

        for attempt in range(max_retries):
            try:
                # 保存到数据库
                config_data = json.dumps(config.to_dict())

                # 检查是否已存在
                session = self._get_session()
                try:
                    existing = session.query(SystemConfig).filter(
                        SystemConfig.key == f"provider_{config.id}"
                    ).first()

                    if existing:
                        existing.value = config_data
                    else:
                        new_config = SystemConfig(
                            key=f"provider_{config.id}",
                            value=config_data,
                            description=f"AI Provider: {config.name}"
                        )
                        session.add(new_config)

                    session.commit()
                finally:
                    session.close()

                # 如果这是第一个提供商，设为默认
                if self.get_providers_count() == 1:
                    self._set_config("default_provider_id", config.id)

                return True
            except Exception as e:
                error_str = str(e).lower()
                if ("database is locked" in error_str or "locked" in error_str) and attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # 指数退避
                    continue
                print(f"添加提供商失败: {e}")
                return False

    def switch_provider(self, provider_id: str) -> bool:
        """切换到指定提供商"""
        try:
            self._set_config("active_provider_id", provider_id)
            return True
        except Exception as e:
            print(f"切换提供商失败: {e}")
            return False

    def delete_provider(self, provider_id: str) -> bool:
        """删除提供商配置"""
        try:
            # 不能删除当前活动的提供商
            active = self.get_active_provider()
            if active and active.id == provider_id:
                return False

            # 删除配置
            self._delete_config(f"provider_{provider_id}")

            # 如果删除的是默认提供商，更新默认设置
            default_id = self._get_config("default_provider_id")
            if default_id == provider_id:
                providers = self.get_providers()
                if providers:
                    self._set_config("default_provider_id", providers[0].id)

            return True
        except Exception as e:
            print(f"删除提供商失败: {e}")
            return False

    def update_provider(self, provider_id: str, config: ProviderConfig) -> bool:
        """更新提供商配置（带重试机制）"""
        import time
        max_retries = 5
        retry_delay = 0.2  # 200ms

        for attempt in range(max_retries):
            try:
                config_data = json.dumps(config.to_dict())
                session = self._get_session()
                try:
                    existing = session.query(SystemConfig).filter(
                        SystemConfig.key == f"provider_{provider_id}"
                    ).first()

                    if existing:
                        existing.value = config_data
                        session.commit()
                        return True
                    return False
                except Exception as e:
                    session.rollback()
                    raise
                finally:
                    session.close()
            except Exception as e:
                error_str = str(e).lower()
                if ("database is locked" in error_str or "locked" in error_str) and attempt < max_retries - 1:
                    time.sleep(retry_delay * (attempt + 1))  # 指数退避
                    continue
                print(f"更新提供商失败: {e}")
                return False

    def get_providers_count(self) -> int:
        """获取提供商数量"""
        return len(self.get_providers())

    def import_from_preset(self, preset_id: str, api_key: str) -> Optional[ProviderConfig]:
        """从预设导入提供商"""
        for preset in PROVIDER_PRESETS:
            if preset.id == preset_id:
                config = preset.config
                config.api_key = api_key
                return config
        return None

    def export_providers(self) -> str:
        """导出所有提供商配置为 JSON"""
        providers = self.get_providers()
        return json.dumps([p.to_dict() for p in providers], indent=2, ensure_ascii=False)

    def import_providers(self, json_data: str) -> int:
        """从 JSON 导入提供商配置"""
        try:
            data = json.loads(json_data)
            imported = 0

            for provider_data in data:
                config = ProviderConfig.from_dict(provider_data)
                if self.add_provider(config):
                    imported += 1

            return imported
        except Exception as e:
            print(f"导入提供商失败: {e}")
            return 0

    def import_from_ccswitch(self) -> int:
        """
        从 cc-switch 导入提供商配置

        Returns:
            int: 导入的提供商数量
        """
        import sqlite3
        from pathlib import Path
        import os

        # 查找 cc-switch 数据库
        possible_paths = [
            Path.home() / ".cc-switch" / "cc-switch.db",
            Path(os.environ.get("APPDATA", "")) / "cc-switch" / "cc-switch.db",
            Path(os.environ.get("LOCALAPPDATA", "")) / "cc-switch" / "cc-switch.db",
        ]

        db_path = None
        for path in possible_paths:
            if path.exists():
                db_path = path
                break

        if not db_path:
            raise FileNotFoundError("未找到 cc-switch 配置文件")

        imported_count = 0

        try:
            # 连接数据库
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()

            # 查询所有提供商
            cursor.execute("""
                SELECT id, app_type, name, settings_config, website_url, category
                FROM providers
            """)

            rows = cursor.fetchall()

            for row in rows:
                try:
                    # 解析 settings_config JSON
                    settings = json.loads(row["settings_config"])
                    env = settings.get("env", {})

                    # 提取 API 密钥
                    api_key = env.get("ANTHROPIC_AUTH_TOKEN") or env.get("OPENAI_API_KEY") or env.get("DEEPSEEK_API_KEY", "")

                    # 提取基础 URL
                    base_url = env.get("ANTHROPIC_BASE_URL", "")

                    # 提取模型
                    model = env.get("ANTHROPIC_MODEL") or env.get("OPENAI_MODEL") or env.get("DEEPSEEK_MODEL", "")

                    # 确定提供商类型
                    provider_type = ProviderType.CUSTOM
                    if row["app_type"] == "claude":
                        provider_type = ProviderType.CLAUDE
                    elif row["app_type"] == "openai":
                        provider_type = ProviderType.OPENAI
                    elif row["app_type"] == "deepseek":
                        provider_type = ProviderType.DEEPSEEK

                    # 使用 cc-switch 的 ID（添加前缀避免冲突）
                    provider_id = f"ccswitch_{row['id']}"

                    # 创建配置
                    config = ProviderConfig(
                        id=provider_id,
                        name=row["name"],
                        provider_type=provider_type,
                        api_key=api_key,
                        api_endpoint=base_url,
                        model=model,
                    )

                    # 添加到数据库
                    if self.add_provider(config):
                        imported_count += 1
                        print(f"已导入提供商: {row['name']}")

                except (json.JSONDecodeError, KeyError) as e:
                    print(f"跳过提供商 {row.get('name', 'unknown')}: {e}")
                    continue

            conn.close()
            return imported_count

        except Exception as e:
            raise RuntimeError(f"从 cc-switch 导入失败: {e}")


# 全局 Provider 管理器实例
provider_manager = ProviderManager()
