"""
Provider Management System 测试脚本
"""
import sys
import os
import asyncio

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

from src.database import init_database
from src.services import (
    provider_manager,
    PROVIDER_PRESETS,
    ProviderConfig,
    ProviderType,
    get_ai_client,
    ai_client_factory,
)

# 初始化数据库
print("=" * 60)
print("初始化数据库...")
init_database()
print("数据库初始化完成\n")

# 测试 1: 列出所有预设
print("=" * 60)
print("测试 1: 列出所有预设配置")
print("=" * 60)
print(f"共有 {len(PROVIDER_PRESETS)} 个预设配置:\n")

# 按类别分组
categories = {}
for preset in PROVIDER_PRESETS:
    if preset.category not in categories:
        categories[preset.category] = []
    categories[preset.category].append(preset)

for category, presets in categories.items():
    print(f"\n[{category.upper()}]")
    for preset in presets:
        print(f"  - {preset.id}: {preset.name}")
        print(f"    {preset.description}")

# 测试 2: 从预设导入提供商
print("\n" + "=" * 60)
print("测试 2: 从预设导入提供商")
print("=" * 60)

# 使用你的真实 API Key
API_KEY = input("\n请输入 API Key (或直接回车跳过): ").strip()

if API_KEY:
    # 导入 Claude 官方预设
    config = provider_manager.import_from_preset("claude-official", API_KEY)
    if config:
        config.id = "my-claude"
        config.name = "我的 Claude"
        if provider_manager.add_provider(config):
            print(f"[成功] 已导入: {config.name}")
        else:
            print("[失败] 导入失败")

    # 导入 OpenAI 官方预设
    config = provider_manager.import_from_preset("openai-official", API_KEY)
    if config:
        config.id = "my-openai"
        config.name = "我的 OpenAI"
        if provider_manager.add_provider(config):
            print(f"[成功] 已导入: {config.name}")

# 测试 3: 列出已配置的提供商
print("\n" + "=" * 60)
print("测试 3: 列出已配置的提供商")
print("=" * 60)

providers = provider_manager.get_providers()
if not providers:
    print("没有配置任何提供商")
else:
    print(f"共有 {len(providers)} 个提供商:\n")
    for p in providers:
        active = provider_manager.get_active_provider()
        is_active = " [活动中]" if active and p.id == active.id else ""
        print(f"  - {p.name} ({p.id}){is_active}")
        print(f"    类型: {p.provider_type.value}")
        print(f"    模型: {p.model}")
        print(f"    端点: {p.api_endpoint}")
        masked_key = p.api_key[:8] + "..." if len(p.api_key) > 8 else "(未设置)"
        print(f"    API 密钥: {masked_key}")
        print()

# 测试 4: 切换提供商
if len(providers) > 0:
    print("=" * 60)
    print("测试 4: 切换活动提供商")
    print("=" * 60)

    target_provider = providers[0]
    if provider_manager.switch_provider(target_provider.id):
        print(f"[成功] 已切换到: {target_provider.name}")

        # 验证
        active = provider_manager.get_active_provider()
        if active and active.id == target_provider.id:
            print(f"[成功] 验证通过: 当前活动提供商是 {active.name}")
        else:
            print("[失败] 切换验证失败")

# 测试 5: AI 客户端工厂
print("\n" + "=" * 60)
print("测试 5: AI 客户端工厂")
print("=" * 60)

try:
    # 获取活动客户端
    active_client = get_ai_client()
    if active_client:
        print(f"[成功] 获取活动客户端: {type(active_client).__name__}")
        print(f"  模型: {active_client.model}")
    else:
        print("[信息] 没有活动的 AI 客户端（需要先配置有效的提供商）")

    # 测试创建特定类型的客户端
    print("\n测试创建不同类型的客户端:")

    # Claude 客户端
    test_config = ProviderConfig(
        id="test-claude-client",
        name="测试 Claude",
        provider_type=ProviderType.CLAUDE,
        api_key="test-key",
        model="claude-sonnet-4-6",
    )
    client = ai_client_factory.create_client(test_config)
    print(f"  Claude 客户端: {type(client).__name__}")

    # OpenAI 客户端
    test_config = ProviderConfig(
        id="test-openai-client",
        name="测试 OpenAI",
        provider_type=ProviderType.OPENAI,
        api_key="test-key",
        model="gpt-4o",
    )
    client = ai_client_factory.create_client(test_config)
    print(f"  OpenAI 客户端: {type(client).__name__}")

    # DeepSeek 客户端
    test_config = ProviderConfig(
        id="test-deepseek-client",
        name="测试 DeepSeek",
        provider_type=ProviderType.DEEPSEEK,
        api_key="test-key",
        model="deepseek-chat",
    )
    client = ai_client_factory.create_client(test_config)
    print(f"  DeepSeek 客户端: {type(client).__name__}")

    print("\n[成功] 所有客户端类型创建成功")

except Exception as e:
    print(f"[失败] AI 客户端工厂测试失败: {e}")

# 测试 6: 实际 API 调用（如果有有效的 API Key）
print("\n" + "=" * 60)
print("测试 6: 实际 API 调用测试")
print("=" * 60)

active = provider_manager.get_active_provider()
if active and active.api_key and active.api_key != "test-key":
    try:
        async def test_api_call():
            from src.ai import Message, MessageRole, AIRequestConfig

            client = get_ai_client()
            if not client:
                print("[跳过] 没有有效的 AI 客户端")
                return

            messages = [
                Message(role=MessageRole.USER, content="你好，请用一句话介绍你自己。")
            ]
            config = AIRequestConfig(
                temperature=0.7,
                max_tokens=100,
            )

            print(f"正在测试 {type(client).__name__}...")
            print("发送消息: '你好，请用一句话介绍你自己。'")

            response = await client.chat(messages, config)

            print(f"\n[成功] API 调用成功！")
            print(f"模型: {response.model}")
            print(f"回复: {response.content}")

            if response.usage:
                print(f"Token 使用: {response.usage}")

        asyncio.run(test_api_call())

    except Exception as e:
        print(f"[失败] API 调用失败: {e}")
        import traceback
        traceback.print_exc()
else:
    print("[跳过] 没有配置有效的 API 密钥，跳过实际 API 调用测试")

# 测试 7: 导出/导入
print("\n" + "=" * 60)
print("测试 7: 导出/导入配置")
print("=" * 60)

try:
    # 导出
    json_data = provider_manager.export_providers()
    print(f"[成功] 导出配置: {len(json_data)} 字符")

    # 保存到文件
    export_file = "test_providers_export.json"
    with open(export_file, "w", encoding="utf-8") as f:
        f.write(json_data)
    print(f"[成功] 已保存到: {export_file}")

    # 导入
    import_count = provider_manager.import_providers(json_data)
    print(f"[信息] 导入测试: {import_count} 个提供商（可能是重复的）")

    # 清理测试文件
    os.remove(export_file)
    print(f"[成功] 已清理测试文件")

except Exception as e:
    print(f"[失败] 导出/导入测试失败: {e}")

# 总结
print("\n" + "=" * 60)
print("测试完成")
print("=" * 60)

print("\n提示:")
print("  - 使用 'python -m codetrace.cli provider --help' 查看所有命令")
print("  - 使用 'python -m codetrace.cli provider presets' 查看可用预设")
print("  - 使用 'python -m codetrace.cli provider import' 导入提供商配置")
