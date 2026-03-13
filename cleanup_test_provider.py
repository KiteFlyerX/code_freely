"""
清理测试数据
删除测试提供商
"""
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

from src.database import init_database
from src.services import provider_manager

# 初始化数据库
init_database()

# 先切换到默认提供商（如果测试提供商是活动的）
active = provider_manager.get_active_provider()
if active and active.id == "test-claude":
    # 尝试导入一个预设提供商作为替代
    preset_config = provider_manager.import_from_preset("claude-official", "sk-ant-test-key")
    if preset_config:
        preset_config.id = "claude-cleanup-temp"
        if provider_manager.add_provider(preset_config):
            provider_manager.switch_provider("claude-cleanup-temp")
            print("已临时切换到 claude-official")

# 删除测试提供商
if provider_manager.delete_provider("test-claude"):
    print("已删除测试提供商: test-claude")
else:
    print("删除失败或提供商不存在")

# 验证
providers = provider_manager.get_providers()
print(f"\n剩余提供商数量: {len(providers)}")
