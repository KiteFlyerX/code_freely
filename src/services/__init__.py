"""
服务层模块
提供业务逻辑服务
"""
from .config_service import (
    AIConfig,
    AppConfig,
    ConfigService,
    config_service,
)
from .conversation_service import (
    ConversationService,
    conversation_service,
)
from .bug_service import (
    BugCreateInfo,
    BugUpdateInfo,
    BugDetail,
    BugService,
    bug_service,
)
from .review_service import (
    ReviewComment,
    ReviewCreateInfo,
    ReviewSubmitInfo,
    ReviewDetail,
    ReviewSummary,
    CodeReviewService,
    review_service,
)
from .knowledge_service import (
    KnowledgeCreateInfo,
    KnowledgeEntryDetail,
    KnowledgeStats,
    KnowledgeService,
    knowledge_service,
)
from .provider_service import (
    ProviderType,
    ProviderConfig,
    ProviderPreset,
    ProviderManager,
    provider_manager,
    PROVIDER_PRESETS,
)
from .ai_client_factory import (
    AIClientFactory,
    ai_client_factory,
    get_ai_client,
    create_ai_client,
)

# 从 models 导入枚举类型
from ..models import BugStatus, ReviewStatus

__all__ = [
    "AIConfig",
    "AppConfig",
    "ConfigService",
    "config_service",
    "ConversationService",
    "conversation_service",
    "BugCreateInfo",
    "BugUpdateInfo",
    "BugDetail",
    "BugService",
    "bug_service",
    "ReviewComment",
    "ReviewCreateInfo",
    "ReviewSubmitInfo",
    "ReviewDetail",
    "ReviewSummary",
    "CodeReviewService",
    "review_service",
    "KnowledgeCreateInfo",
    "KnowledgeEntryDetail",
    "KnowledgeStats",
    "KnowledgeService",
    "knowledge_service",
    "ProviderType",
    "ProviderConfig",
    "ProviderPreset",
    "ProviderManager",
    "provider_manager",
    "PROVIDER_PRESETS",
    "AIClientFactory",
    "ai_client_factory",
    "get_ai_client",
    "create_ai_client",
    "BugStatus",
    "ReviewStatus",
]
