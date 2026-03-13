#!/usr/bin/env python
"""
CodeTraceAI 仓库管理脚本
方便查看修改、同步代码、管理分支
"""
import subprocess
import sys
from pathlib import Path


def run_command(cmd: list, description: str):
    """运行命令并显示结果"""
    print(f"\n{'='*50}")
    print(f"{description}")
    print(f"{'='*50}")
    print(f"$ {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd, capture_output=True, text=True)

    if result.stdout:
        print(result.stdout)
    if result.stderr:
        print(result.stderr)

    return result.returncode == 0


def show_status():
    """显示仓库状态"""
    run_command(
        ["git", "status", "-sb"],
        "仓库状态"
    )


def show_log():
    """显示最近提交"""
    run_command(
        ["git", "log", "--oneline", "--graph", "-10"],
        "最近提交记录"
    )


def show_diff():
    """显示未提交的修改"""
    run_command(
        ["git", "diff", "--stat"],
        "修改统计"
    )

    print("\n是否查看详细差异? (y/n): ", end="")
    if input().lower() == 'y':
        run_command(["git", "diff"], "详细差异")


def show_remote():
    """显示远程仓库信息"""
    run_command(
        ["git", "remote", "-v"],
        "远程仓库"
    )

    run_command(
        ["git", "branch", "-vv"],
        "分支追踪"
    )


def sync_repo():
    """同步仓库"""
    print("\n获取远程更新...")
    if run_command(["git", "fetch", "origin"], "获取远程更新"):
        print("\n推送本地更改...")
        run_command(["git", "push", "origin", "master"], "推送到远程")


def show_untracked():
    """显示未跟踪的文件"""
    result = subprocess.run(
        ["git", "ls-files", "--others", "--exclude-standard"],
        capture_output=True,
        text=True
    )

    print(f"\n{'='*50}")
    print("未跟踪的文件")
    print(f"{'='*50}")

    if result.stdout.strip():
        print(result.stdout)
    else:
        print("(无未跟踪文件)")


def create_branch(branch_name: str):
    """创建新分支"""
    run_command(
        ["git", "checkout", "-b", branch_name],
        f"创建并切换到分支: {branch_name}"
    )


def show_branches():
    """显示所有分支"""
    run_command(
        ["git", "branch", "-a"],
        "所有分支"
    )


def menu():
    """主菜单"""
    while True:
        print("\n" + "="*50)
        print("CodeTraceAI 仓库管理")
        print("="*50)
        print("1. 查看仓库状态")
        print("2. 查看最近提交")
        print("3. 查看修改内容")
        print("4. 查看远程仓库")
        print("5. 同步代码 (fetch + push)")
        print("6. 查看所有分支")
        print("7. 创建新分支")
        print("8. 查看未跟踪文件")
        print("0. 退出")
        print("="*50)

        choice = input("\n请选择 (0-8): ").strip()

        if choice == "1":
            show_status()
        elif choice == "2":
            show_log()
        elif choice == "3":
            show_diff()
        elif choice == "4":
            show_remote()
        elif choice == "5":
            sync_repo()
        elif choice == "6":
            show_branches()
        elif choice == "7":
            name = input("输入新分支名称: ").strip()
            if name:
                create_branch(name)
        elif choice == "8":
            show_untracked()
        elif choice == "0":
            print("退出")
            break
        else:
            print("无效选择")


if __name__ == "__main__":
    import os
    os.chdir(Path(__file__).parent.parent)
    menu()
