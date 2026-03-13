"""
逐步测试 GUI 导入
找出导致问题的具体模块
"""
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

print("Step 1: Creating QApplication...")
from PySide6.QtWidgets import QApplication
app = QApplication([])
print("  OK\n")

print("Step 2: Testing imports one by one...")

# 测试数据库
try:
    from src.database import init_database
    init_database()
    print("  [OK] src.database")
except Exception as e:
    print(f"  [FAIL] src.database: {e}")
    sys.exit(1)

# 测试服务
try:
    from src.services import config_service
    print("  [OK] src.services")
except Exception as e:
    print(f"  [FAIL] src.services: {e}")
    sys.exit(1)

# 测试 AI 模块
try:
    from src.ai import get_ai_provider
    print("  [OK] src.ai")
except Exception as e:
    print(f"  [FAIL] src.ai: {e}")
    sys.exit(1)

# 测试 VCS 模块
try:
    from src.vcs import get_vcs
    print("  [OK] src.vcs")
except Exception as e:
    print(f"  [FAIL] src.vcs: {e}")
    sys.exit(1)

# 测试单个视图导入
print("\nStep 3: Testing view imports...")

try:
    from src.gui.views.chat_view import ChatView
    print("  [OK] chat_view")
except Exception as e:
    print(f"  [FAIL] chat_view: {e}")
    sys.exit(1)

try:
    from src.gui.views.history_view import HistoryView
    print("  [OK] history_view")
except Exception as e:
    print(f"  [FAIL] history_view: {e}")
    sys.exit(1)

try:
    from src.gui.views.bug_view import BugView
    print("  [OK] bug_view")
except Exception as e:
    print(f"  [FAIL] bug_view: {e}")
    sys.exit(1)

try:
    from src.gui.views.review_view import ReviewView
    print("  [OK] review_view")
except Exception as e:
    print(f"  [FAIL] review_view: {e}")
    sys.exit(1)

try:
    from src.gui.views.knowledge_view import KnowledgeView
    print("  [OK] knowledge_view")
except Exception as e:
    print(f"  [FAIL] knowledge_view: {e}")
    sys.exit(1)

try:
    from src.gui.views.settings_view import SettingsView
    print("  [OK] settings_view")
except Exception as e:
    print(f"  [FAIL] settings_view: {e}")
    sys.exit(1)

print("\nStep 4: Importing MainWindow...")
try:
    from src.gui.main_window import MainWindow
    print("  [OK] MainWindow")
except Exception as e:
    print(f"  [FAIL] MainWindow: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nStep 5: Creating MainWindow instance...")
try:
    window = MainWindow()
    print("  [OK] MainWindow created")
except Exception as e:
    print(f"  [FAIL] MainWindow creation: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nAll tests passed! GUI should work now.")
print("\nPress Ctrl+C to exit if window doesn't appear...")

# 显示窗口
window.show()

# 运行应用
sys.exit(app.exec())
