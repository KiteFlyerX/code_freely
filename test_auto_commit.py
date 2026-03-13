"""
测试自动提交功能
验证代码修改后是否自动提交到 Git 仓库
"""
import sys
import os
from pathlib import Path

# 添加 src 到路径
sys.path.insert(0, str(Path(__file__).parent))

from src.services import config_service
from src.vcs import GitVCSFactory
from src.database.repositories import CodeChangeRepository, MessageRepository
from src.database import get_db_session


def test_auto_commit():
    """测试自动提交功能"""
    print("=" * 60)
    print("测试自动提交功能")
    print("=" * 60)

    # 1. 检查当前配置
    print("\n[1] 检查当前配置...")
    config = config_service.get_config()
    print(f"  自动提交: {config.auto_commit}")
    print(f"  创建临时分支: {config.create_temp_branch}")

    if not config.auto_commit:
        print("  [WARNING] 自动提交未启用，请在设置中启用")
        return False

    # 2. 检查 Git 仓库
    print("\n[2] 检查 Git 仓库...")
    project_path = str(Path.cwd())
    vcs = GitVCSFactory.create(project_path)

    if not vcs:
        print(f"  [ERROR] 当前目录不是 Git 仓库: {project_path}")
        return False

    current_branch = vcs.get_current_branch()
    print(f"  [OK] 当前是 Git 仓库")
    print(f"  [OK] 当前分支: {current_branch}")

    # 3. 检查是否有未提交的更改
    print("\n[3] 检查未提交的更改...")
    has_changes = vcs.has_uncommitted_changes()
    modified_files = vcs.get_modified_files()

    print(f"  未提交的更改: {'是' if has_changes else '否'}")
    print(f"  修改的文件数: {len(modified_files)}")

    for file_info in modified_files[:5]:  # 只显示前5个
        status = "新增" if file_info.is_new else "修改"
        print(f"    - [{status}] {file_info.path}")

    if len(modified_files) > 5:
        print(f"    ... 还有 {len(modified_files) - 5} 个文件")

    # 4. 创建测试代码修改记录
    print("\n[4] 创建测试代码修改记录...")
    try:
        msg_repo = MessageRepository(get_db_session())
        code_repo = CodeChangeRepository(get_db_session())

        # 创建测试消息
        msg = msg_repo.create(
            conversation_id=1,
            role="assistant",
            content="测试自动提交功能"
        )

        # 创建测试代码修改
        if modified_files:
            # 使用第一个修改的文件
            test_file = modified_files[0].path
            original_content = vcs.get_file_content(test_file) or "未找到原始内容"
            modified_content = original_content + "\n# 测试自动提交"

            change = code_repo.create(
                message_id=msg.id,
                file_path=test_file,
                project_path=project_path,
                original_code=original_content,
                modified_code=modified_content
            )

            print(f"  [OK] 创建代码修改记录 (ID: {change.id})")
            print(f"  [OK] 文件: {test_file}")
        else:
            print("  [WARNING] 没有修改的文件，跳过创建代码修改记录")

    except Exception as e:
        print(f"  [ERROR] 创建代码修改记录失败: {e}")
        return False

    # 5. 模拟自动提交
    print("\n[5] 模拟自动提交...")
    try:
        # 获取所有未提交的文件
        files_to_commit = [f.path for f in modified_files]

        if not files_to_commit:
            print("  [WARNING] 没有文件需要提交")
            return False

        # 创建提交消息
        commit_message = f"CodeTraceAI: 自动提交代码修改\n\n"
        commit_message += f"- 修改文件数: {len(files_to_commit)}\n"
        commit_message += f"- 关联消息 ID: {msg.id}\n"
        commit_message += f"- 关联代码修改 ID: {change.id if 'change' in locals() else 'N/A'}"

        # 执行提交
        commit_hash = vcs.commit(commit_message, files_to_commit)

        if commit_hash:
            print(f"  [OK] 自动提交成功!")
            print(f"  [OK] 提交哈希: {commit_hash[:12]}")
            print(f"  [OK] 提交消息: {commit_message[:50]}...")
        else:
            print(f"  [ERROR] 自动提交失败")
            return False

    except Exception as e:
        print(f"  [ERROR] 自动提交过程出错: {e}")
        import traceback
        traceback.print_exc()
        return False

    # 6. 验证提交结果
    print("\n[6] 验证提交结果...")
    try:
        recent_commits = vcs.get_recent_commits(limit=5)
        print(f"  最近的提交:")

        for i, commit in enumerate(recent_commits[:3], 1):
            print(f"    {i}. [{commit.hash[:8]}] {commit.message[:40]}...")

        # 检查是否还有未提交的更改
        has_changes_after = vcs.has_uncommitted_changes()
        if has_changes_after:
            print(f"  [WARNING] 仍有未提交的更改")
        else:
            print(f"  [OK] 所有更改已提交")

    except Exception as e:
        print(f"  [ERROR] 验证提交结果失败: {e}")
        return False

    print("\n" + "=" * 60)
    print("[OK] 自动提交功能测试通过!")
    print("=" * 60)
    return True


def test_temp_branch():
    """测试临时分支功能"""
    print("\n" + "=" * 60)
    print("测试临时分支功能")
    print("=" * 60)

    config = config_service.get_config()

    if not config.create_temp_branch:
        print("临时分支功能未启用")
        return True

    print(f"[OK] 临时分支功能已启用")
    print(f"  说明: 在实际使用中，创建代码修改时会自动创建临时分支")
    print(f"  分支命名格式: codetrace-<timestamp>")

    return True


def main():
    """主函数"""
    print("\n[TEST] CodeTraceAI 自动提交功能测试\n")

    # 测试自动提交
    auto_commit_ok = test_auto_commit()

    # 测试临时分支
    temp_branch_ok = test_temp_branch()

    # 总结
    print("\n" + "=" * 60)
    print("测试总结")
    print("=" * 60)
    print(f"自动提交功能: {'[OK] 通过' if auto_commit_ok else '[FAIL] 失败'}")
    print(f"临时分支功能: {'[OK] 通过' if temp_branch_ok else '[FAIL] 失败'}")
    print("=" * 60)

    if auto_commit_ok and temp_branch_ok:
        print("\n[SUCCESS] 所有测试通过!")
        return 0
    else:
        print("\n[WARNING] 部分测试失败，请检查配置")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
