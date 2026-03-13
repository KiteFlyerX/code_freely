"""
测试模块 - 验证核心功能
"""
import sys
from pathlib import Path

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def test_config_service():
    """测试配置服务"""
    from src.services.config_service import config_service

    config = config_service.get_config()
    print(f"AI Provider: {config.ai.provider}")
    print(f"AI Model: {config.ai.model}")
    print("Config service: OK")


def test_database():
    """测试数据库"""
    from src.database import init_database, db_manager
    from src.models import SystemConfig

    init_database()
    print("Database initialized")

    with db_manager.get_session() as session:
        configs = session.query(SystemConfig).all()
        print(f"Found {len(configs)} config entries")
    print("Database: OK")


def test_vcs():
    """测试版本控制"""
    from src.vcs import GitVCSFactory

    # 检测当前目录
    vcs = GitVCSFactory.create(str(Path.cwd()))
    if vcs:
        branch = vcs.get_current_branch()
        print(f"Git repository detected, current branch: {branch}")
        print("VCS: OK")
    else:
        print("Not a Git repository")


def test_ai_interface():
    """测试 AI 接口"""
    from src.ai import ClaudeAI

    # 只验证类结构，不实际调用 API
    print(f"ClaudeAI supported models: {list(ClaudeAI.SUPPORTED_MODELS.keys())}")
    print("AI interface: OK")


if __name__ == "__main__":
    print("Running CodeTraceAI tests...\n")

    tests = [
        ("Config Service", test_config_service),
        ("Database", test_database),
        ("VCS", test_vcs),
        ("AI Interface", test_ai_interface),
    ]

    for name, test_func in tests:
        print(f"\n--- {name} ---")
        try:
            test_func()
        except Exception as e:
            import traceback
            print(f"FAILED: {e}")
            traceback.print_exc()

    print("\n--- All tests completed ---")
