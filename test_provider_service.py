"""
测试 Provider Service
验证提供商管理功能
"""
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

from src.database import init_database
from src.services import provider_manager, PROVIDER_PRESETS, ProviderConfig, ProviderType

# 初始化数据库
print("初始化数据库...")
init_database()
print("数据库初始化完成\n")

# 测试 1: 列出预设
print("=" * 50)
print("测试 1: 列出所有预设")
print("=" * 50)
for preset in PROVIDER_PRESETS:
    print(f"- {preset.id}: {preset.name} ({preset.category})")
    print(f"  {preset.description}")
print()

# 测试 2: 添加测试提供商
print("=" * 50)
print("测试 2: 添加测试提供商")
print("=" * 50)

test_provider = ProviderConfig(
    id="test-claude",
    name="测试 Claude",
    provider_type=ProviderType.CLAUDE,
    api_key="test-key-12345",
    api_endpoint="https://api.anthropic.com",
    model="claude-sonnet-4-6",
    temperature=0.7,
    max_tokens=4096,
)

if provider_manager.add_provider(test_provider):
    print("[PASS] 添加提供商成功")
else:
    print("[FAIL] 添加提供商失败")
print()

# 测试 3: 列出所有提供商
print("=" * 50)
print("测试 3: 列出所有提供商")
print("=" * 50)
providers = provider_manager.get_providers()
print(f"找到 {len(providers)} 个提供商:")
for p in providers:
    print(f"- {p.name} ({p.id})")
    print(f"  类型: {p.provider_type.value}")
    print(f"  模型: {p.model}")
    masked_key = p.api_key[:8] + "..." if len(p.api_key) > 8 else "***"
    print(f"  API 密钥: {masked_key}")
print()

# 测试 4: 获取活动提供商
print("=" * 50)
print("测试 4: 获取活动提供商")
print("=" * 50)
active = provider_manager.get_active_provider()
if active:
    print(f"[PASS] 活动提供商: {active.name} ({active.id})")
else:
    print("[INFO] 没有活动提供商")
print()

# 测试 5: 切换提供商
print("=" * 50)
print("测试 5: 切换提供商")
print("=" * 50)
if provider_manager.switch_provider("test-claude"):
    print("[PASS] 切换提供商成功")
    active = provider_manager.get_active_provider()
    if active and active.id == "test-claude":
        print(f"[PASS] 验证成功: 当前活动提供商是 {active.name}")
    else:
        print("[FAIL] 切换验证失败")
else:
    print("[FAIL] 切换提供商失败")
print()

# 测试 6: 导出/导入提供商
print("=" * 50)
print("测试 6: 导出/导入提供商")
print("=" * 50)
try:
    json_data = provider_manager.export_providers()
    print(f"[PASS] 导出成功: {len(json_data)} 字符")

    # 测试导入
    import_count = provider_manager.import_providers(json_data)
    print(f"[INFO] 导入测试: {import_count} 个提供商（可能是重复的）")
except Exception as e:
    print(f"[FAIL] 导出/导入失败: {e}")
print()

# 测试 7: 从预设导入
print("=" * 50)
print("测试 7: 从预设导入")
print("=" * 50)
preset_config = provider_manager.import_from_preset("claude-official", "sk-ant-test-key")
if preset_config:
    print(f"[PASS] 从预设导入成功: {preset_config.name}")
    print(f"  类型: {preset_config.provider_type.value}")
    print(f"  端点: {preset_config.api_endpoint}")
    print(f"  模型: {preset_config.model}")
else:
    print("[FAIL] 从预设导入失败")
print()

# 测试 8: AI 客户端工厂
print("=" * 50)
print("测试 8: AI 客户端工厂")
print("=" * 50)
try:
    from src.services import ai_client_factory

    # 使用测试配置创建客户端
    test_config = ProviderConfig(
        id="test-openai",
        name="测试 OpenAI",
        provider_type=ProviderType.OPENAI,
        api_key="test-key",
        model="gpt-4o",
    )

    client = ai_client_factory.create_client(test_config)
    print(f"[PASS] 创建客户端成功: {type(client).__name__}")

    # 测试获取活动客户端（可能返回 None，因为没有有效的 API key）
    active_client = ai_client_factory.get_active_client()
    if active_client:
        print(f"[PASS] 获取活动客户端成功: {type(active_client).__name__}")
    else:
        print("[INFO] 没有活动的 AI 客户端（预期行为）")
except Exception as e:
    print(f"[FAIL] AI 客户端工厂测试失败: {e}")
    import traceback
    traceback.print_exc()
print()

print("=" * 50)
print("所有测试完成")
print("=" * 50)
