"""
CodeTraceAI 打包脚本
使用 PyInstaller 将应用打包为绿色免安装的 exe
"""
import os
import sys
import subprocess
from pathlib import Path

# 项目根目录
ROOT_DIR = Path(__file__).parent
DIST_DIR = ROOT_DIR / "dist"
BUILD_DIR = ROOT_DIR / "build"

# PyInstaller 配置
PYINSTALLER_SPEC = """
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['start_simple_gui.py'],
    pathex=[],
    binaries=[],
    datas=[
        ('src', 'src'),
    ],
    hiddenimports=[
        'PySide6.QtCore',
        'PySide6.QtGui',
        'PySide6.QtWidgets',
        'qfluentwidgets',
        'sqlalchemy',
        'sqlalchemy.dialects',
        'sqlalchemy.dialects.sqlite',
        'sqlalchemy.orm',
        'anthropic',
        'openai',
        'gitpython',
        'aiohttp',
        'markdown',
        'src.ai',
        'src.ai.base',
        'src.ai.claude',
        'src.ai.openai_impl',
        'src.ai.deepseek_impl',
        'src.tools',
        'src.tools.base',
        'src.tools.default_tools',
        'src.services',
        'src.services.config_service',
        'src.services.conversation_service',
        'src.services.provider_service',
        'src.services.bug_service',
        'src.services.review_service',
        'src.services.knowledge_service',
        'src.services.ai_client_factory',
        'src.database',
        'src.database.manager',
        'src.database.repositories',
        'src.models',
        'src.models.database',
        'src.vcs',
        'src.vcs.base',
        'src.vcs.git_impl',
        'src.gui',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=['Tkinter', 'matplotlib', 'pandas', 'numpy', 'scipy'],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='CodeTraceAI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,  # 窗口模式，不显示控制台
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
"""


def create_build_script():
    """创建 PyInstaller 打包脚本"""
    spec_file = ROOT_DIR / "codetraceai.spec"

    print(f"创建 PyInstaller spec 文件: {spec_file}")
    spec_file.write_text(PYINSTALLER_SPEC)

    return spec_file


def install_pyinstaller():
    """安装 PyInstaller"""
    print("安装 PyInstaller...")
    subprocess.run(
        [sys.executable, "-m", "pip", "install", "pyinstaller>=5.0.0"],
        check=True,
        cwd=ROOT_DIR
    )


def build_exe():
    """执行打包"""
    spec_file = create_build_script()

    print("\n开始打包...")
    print("=" * 60)

    # 清理旧的构建文件
    if BUILD_DIR.exists():
        import shutil
        shutil.rmtree(BUILD_DIR)
        print("已清理旧的 build 目录")

    if DIST_DIR.exists():
        import shutil
        shutil.rmtree(DIST_DIR)
        print("已清理旧的 dist 目录")

    # 执行 PyInstaller
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--clean",
        "--noconfirm",
        str(spec_file),
    ]

    print(f"执行命令: {' '.join(cmd)}")
    result = subprocess.run(cmd, cwd=ROOT_DIR)

    if result.returncode != 0:
        print("\n" + "=" * 60)
        print("❌ 打包失败！")
        return False

    print("\n" + "=" * 60)
    print("✅ 打包成功！")

    # 检查输出
    exe_path = DIST_DIR / "CodeTraceAI.exe"
    if exe_path.exists():
        size_mb = exe_path.stat().st_size / (1024 * 1024)
        print(f"\n📦 生成的 exe 文件: {exe_path}")
        print(f"   文件大小: {size_mb:.2f} MB")

        # 创建绿色版目录结构
        portable_dir = DIST_DIR / "CodeTraceAI_Portable"
        create_portable_package(portable_dir, exe_path)
    else:
        print(f"⚠️ 警告: 未找到预期的 exe 文件")
        return False

    return True


def create_portable_package(portable_dir: Path, exe_path: Path):
    """创建绿色免安装版本"""
    import shutil

    print(f"\n创建绿色版目录: {portable_dir}")

    if portable_dir.exists():
        shutil.rmtree(portable_dir)

    portable_dir.mkdir(parents=True, exist_ok=True)

    # 复制 exe
    shutil.copy2(exe_path, portable_dir / "CodeTraceAI.exe")

    # 创建必要目录
    (portable_dir / "data").mkdir(exist_ok=True)
    (portable_dir / "logs").mkdir(exist_ok=True)

    # 创建启动脚本
    start_bat = portable_dir / "启动.bat"
    start_bat.write_text("""@echo off
chcp 65001 >nul
echo CodeTraceAI - AI 编程辅助工具
echo.
start "" "CodeTraceAI.exe"
""")

    # 创建说明文件
    readme = portable_dir / "使用说明.txt"
    readme.write_text("""CodeTraceAI - AI 编程辅助工具
=====================

绿色免安装版本，无需安装直接运行。

使用方法:
1. 双击 "CodeTraceAI.exe" 或 "启动.bat" 启动程序
2. 首次运行会自动创建数据库文件
3. 在设置中配置 AI 提供商和 API 密钥

目录说明:
- CodeTraceAI.exe  主程序
- data/            数据目录（自动创建）
- logs/            日志目录（自动创建）
- 使用说明.txt     本文件

注意事项:
- 请确保已安装 Git（如果需要版本控制功能）
- 需要配置有效的 AI API 密钥才能使用

版本: 0.1.0
更新日期: 2024
""")

    # 创建版本信息
    version_file = portable_dir / "version.txt"
    version_file.write_text("0.1.0\n")

    print(f"✅ 绿色版创建完成: {portable_dir}")
    print(f"   - CodeTraceAI.exe")
    print(f"   - 启动.bat")
    print(f"   - 使用说明.txt")


def main():
    """主函数"""
    print("=" * 60)
    print("CodeTraceAI 打包工具")
    print("=" * 60)

    try:
        # 安装 PyInstaller
        install_pyinstaller()

        # 执行打包
        success = build_exe()

        if success:
            print("\n" + "=" * 60)
            print("🎉 打包完成！")
            print("=" * 60)
            print(f"\n输出目录: {DIST_DIR}")
            print(f"绿色版: {DIST_DIR / 'CodeTraceAI_Portable'}")

    except subprocess.CalledProcessError as e:
        print(f"\n❌ 错误: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 未预期的错误: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
