#!/usr/bin/env python
"""
CodeTraceAI 快速测试脚本
运行所有测试并生成报告
"""
import sys
import subprocess
from pathlib import Path


def run_test(test_file, description):
    """运行单个测试文件"""
    print(f"\n{'='*70}")
    print(f"运行: {description}")
    print(f"文件: {test_file}")
    print(f"{'='*70}")

    result = subprocess.run(
        [sys.executable, str(test_file)],
        capture_output=False,
        text=True
    )

    success = result.returncode == 0
    status = "✅ 通过" if success else "❌ 失败"
    print(f"\n结果: {status}\n")

    return success


def main():
    """主函数"""
    print("\n" + "="*70)
    print("CodeTraceAI 测试套件")
    print("="*70)

    project_root = Path(__file__).parent
    tests = [
        # 核心测试
        (
            project_root / "tests" / "test_core.py",
            "核心功能测试"
        ),
        # 集成测试
        (
            project_root / "tests" / "test_integration.py",
            "完整集成测试"
        ),
        # 自动提交测试（可选，会实际提交代码）
        # (
        #     project_root / "test_auto_commit.py",
        #     "自动提交功能测试"
        # ),
    ]

    results = []
    for test_file, description in tests:
        if test_file.exists():
            success = run_test(test_file, description)
            results.append((description, success))
        else:
            print(f"\n⚠️  警告: 测试文件不存在 - {test_file}")

    # 打印总结
    print("\n" + "="*70)
    print("测试总结")
    print("="*70)

    passed = sum(1 for _, success in results if success)
    total = len(results)

    for description, success in results:
        status = "✅ 通过" if success else "❌ 失败"
        print(f"{status} - {description}")

    print(f"\n总计: {passed}/{total} 通过")

    if passed == total:
        print("\n🎉 所有测试通过！项目运行正常！")
        return 0
    else:
        print(f"\n⚠️  有 {total - passed} 个测试失败，请检查")
        return 1


if __name__ == "__main__":
    exit_code = main()
    input("\n按 Enter 键退出...")
    sys.exit(exit_code)
