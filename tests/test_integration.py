"""
CodeTraceAI 集成测试套件
测试所有核心功能和服务
"""
import sys
import asyncio
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.database import init_database, db_manager
from src.services import (
    config_service,
    conversation_service,
    bug_service,
    review_service,
    knowledge_service,
)
from src.services.config_service import AIConfig
from src.ai import ClaudeAI, OpenAI, DeepSeekAI
from src.vcs import GitVCSFactory


class TestResults:
    """测试结果收集"""

    def __init__(self):
        self.passed = []
        self.failed = []

    def add_pass(self, test_name: str):
        self.passed.append(test_name)
        print(f"  [PASS] {test_name}")

    def add_fail(self, test_name: str, error: str):
        self.failed.append((test_name, error))
        print(f"  [FAIL] {test_name}: {error}")

    def summary(self):
        total = len(self.passed) + len(self.failed)
        print(f"\n{'='*50}")
        print(f"测试结果: {len(self.passed)}/{total} 通过")
        if self.failed:
            print(f"\n失败的测试:")
            for name, error in self.failed:
                print(f"  - {name}: {error}")
        print(f"{'='*50}")
        return len(self.failed) == 0


def test_database(results: TestResults):
    """测试数据库"""
    print("\n[Database] 测试数据库模块...")

    try:
        # 初始化数据库
        init_database()
        results.add_pass("数据库初始化")

        # 测试会话
        with db_manager.get_session() as session:
            from src.models import SystemConfig
            # 查询测试
            configs = session.query(SystemConfig).limit(1).all()
        results.add_pass("数据库会话")

    except Exception as e:
        results.add_fail("数据库模块", str(e))


def test_ai_interfaces(results: TestResults):
    """测试 AI 接口"""
    print("\n[AI] 测试 AI 接口模块...")

    # Claude
    try:
        models = list(ClaudeAI.SUPPORTED_MODELS.keys())
        assert len(models) > 0
        results.add_pass(f"Claude AI 模型列表 ({len(models)} 个)")
    except Exception as e:
        results.add_fail("Claude AI", str(e))

    # OpenAI
    try:
        models = list(OpenAI.SUPPORTED_MODELS.keys())
        assert len(models) > 0
        results.add_pass(f"OpenAI 模型列表 ({len(models)} 个)")
    except Exception as e:
        results.add_fail("OpenAI", str(e))

    # DeepSeek
    try:
        models = list(DeepSeekAI.SUPPORTED_MODELS.keys())
        assert len(models) > 0
        results.add_pass(f"DeepSeek 模型列表 ({len(models)} 个)")
    except Exception as e:
        results.add_fail("DeepSeek", str(e))


def test_vcs(results: TestResults):
    """测试版本控制"""
    print("\n[VCS] 测试版本控制模块...")

    try:
        # 检测当前目录
        vcs = GitVCSFactory.create(str(Path.cwd()))
        if vcs:
            branch = vcs.get_current_branch()
            results.add_pass(f"Git 检测成功 (分支: {branch})")

            # 测试其他功能
            has_changes = vcs.has_uncommitted_changes()
            results.add_pass("Git 状态检查")

            modified = vcs.get_modified_files()
            results.add_pass(f"Git 文件变更检查 ({len(modified)} 个文件)")
        else:
            results.add_pass("Git 检测 (当前不是 Git 仓库)")
    except Exception as e:
        results.add_fail("版本控制", str(e))


def test_config_service(results: TestResults):
    """测试配置服务"""
    print("\n[Config] 测试配置服务...")

    try:
        config = config_service.get_config()
        results.add_pass("配置加载")

        # 测试 AI 配置
        assert config.ai is not None
        results.add_pass("AI 配置结构")

        # 测试配置更新
        config_service.update_ai_config(temperature=0.5)
        results.add_pass("配置更新")

    except Exception as e:
        results.add_fail("配置服务", str(e))


def test_conversation_service(results: TestResults):
    """测试对话服务"""
    print("\n[Chat] 测试对话服务...")

    try:
        # 创建对话
        conv_id = conversation_service.create_conversation(
            title="测试对话",
            project_path=str(Path.cwd())
        )
        results.add_pass(f"创建对话 (ID: {conv_id})")

        # 获取对话列表
        conversations = conversation_service.list_conversations(limit=10)
        results.add_pass(f"对话列表 ({len(conversations)} 个)")

        # 获取消息
        messages = conversation_service.get_messages(conv_id)
        results.add_pass("获取消息")

    except Exception as e:
        results.add_fail("对话服务", str(e))


def test_bug_service(results: TestResults):
    """测试 Bug 追踪服务"""
    print("\n[Bug] 测试 Bug 追踪服务...")

    try:
        from src.services import BugCreateInfo

        # 创建 Bug
        bug_id = bug_service.create_bug(BugCreateInfo(
            title="测试 Bug",
            description="这是一个测试 Bug",
            error_type="TestError"
        ))
        results.add_pass(f"创建 Bug (ID: {bug_id})")

        # 获取 Bug 详情
        bug = bug_service.get_bug(bug_id)
        assert bug is not None
        results.add_pass("获取 Bug 详情")

        # 获取 Bug 列表
        bugs = bug_service.list_bugs(limit=10)
        results.add_pass(f"Bug 列表 ({len(bugs)} 个)")

        # 状态更新
        bug_service.mark_in_progress(bug_id)
        results.add_pass("Bug 状态更新")

        # 搜索
        search_results = bug_service.search_bugs("测试")
        results.add_pass("Bug 搜索")

    except Exception as e:
        results.add_fail("Bug 追踪服务", str(e))


def test_review_service(results: TestResults):
    """测试代码审查服务"""
    print("\n[Review] 测试代码审查服务...")

    try:
        from src.services import ReviewCreateInfo, ReviewSubmitInfo, ReviewStatus

        # 先创建一个代码修改记录
        from src.database.repositories import CodeChangeRepository, MessageRepository
        from src.database import get_db_session

        msg_repo = MessageRepository(get_db_session())
        code_repo = CodeChangeRepository(get_db_session())

        # 创建测试消息
        msg = msg_repo.create(
            conversation_id=1,
            role="assistant",
            content="测试内容"
        )

        # 创建测试代码修改
        change = code_repo.create(
            message_id=msg.id,
            file_path="test.py",
            project_path=str(Path.cwd()),
            original_code="old code",
            modified_code="new code"
        )

        # 创建审查
        review_id = review_service.create_review(ReviewCreateInfo(
            code_change_id=change.id,
            reviewer="测试者"
        ))
        results.add_pass(f"创建审查 (ID: {review_id})")

        # 提交审查
        review_service.submit_review(review_id, ReviewSubmitInfo(
            status=ReviewStatus.APPROVED,
            comment="测试通过",
            rating=5
        ))
        results.add_pass("提交审查")

        # 获取审查摘要
        summary = review_service.get_review_summary(change.id)
        results.add_pass("审查摘要")

        # 合并检查
        can_merge, _ = review_service.can_merge(change.id)
        results.add_pass("合并检查")

    except Exception as e:
        results.add_fail("代码审查服务", str(e))


def test_knowledge_service(results: TestResults):
    """测试知识库服务"""
    print("\n[Knowledge] 测试知识库服务...")

    try:
        from src.services import KnowledgeCreateInfo

        # 创建知识条目
        entry_id = knowledge_service.create_entry(KnowledgeCreateInfo(
            title="测试知识",
            content="这是测试内容",
            category="常见问题",
            tags=["test", "python"]
        ))
        results.add_pass(f"创建知识条目 (ID: {entry_id})")

        # 获取条目
        entry = knowledge_service.get_entry(entry_id)
        assert entry is not None
        results.add_pass("获取知识条目")

        # 搜索
        search_results = knowledge_service.search("测试")
        results.add_pass("知识搜索")

        # 获取统计
        stats = knowledge_service.get_statistics()
        results.add_pass(f"知识统计 (总数: {stats.total_entries})")

        # 按分类获取
        entries = knowledge_service.get_by_category("常见问题")
        results.add_pass("分类获取")

        # 查找相似条目
        similar = knowledge_service.find_similar(entry_id)
        results.add_pass("相似条目查找")

    except Exception as e:
        results.add_fail("知识库服务", str(e))


def test_integration(results: TestResults):
    """集成测试 - 测试服务间协作"""
    print("\n[Integration] 测试服务集成...")

    try:
        # 测试从 Bug 提取知识
        from src.services import BugCreateInfo

        bug_id = bug_service.create_bug(BugCreateInfo(
            title="集成测试 Bug",
            description="用于测试知识提取",
            error_type="IntegrationError"
        ))

        knowledge_id = knowledge_service.extract_from_bug(bug_id)
        assert knowledge_id is not None
        results.add_pass("Bug 到知识提取")

        # 测试知识条目访问计数
        knowledge_service.mark_helpful(knowledge_id)
        results.add_pass("知识访问计数")

    except Exception as e:
        results.add_fail("服务集成", str(e))


def run_all_tests():
    """运行所有测试"""
    print("="*50)
    print("CodeTraceAI 集成测试")
    print("="*50)

    results = TestResults()

    # 核心模块测试
    test_database(results)
    test_ai_interfaces(results)
    test_vcs(results)
    test_config_service(results)

    # 服务层测试
    test_conversation_service(results)
    test_bug_service(results)
    test_review_service(results)
    test_knowledge_service(results)

    # 集成测试
    test_integration(results)

    # 输出结果
    success = results.summary()

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = run_all_tests()
    sys.exit(exit_code)
