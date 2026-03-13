"""
测试 GUI 模块导入
"""
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
os.chdir(script_dir)
sys.path.insert(0, script_dir)

from PySide6.QtWidgets import QApplication, QMainWindow, QLabel, QVBoxLayout, QWidget
app = QApplication([])

print("Testing module imports...")

try:
    import src.ai
    print("OK: src.ai")
except Exception as e:
    print(f"FAIL: src.ai - {e}")

try:
    import src.database
    print("OK: src.database")
except Exception as e:
    print(f"FAIL: src.database - {e}")

try:
    import src.models
    print("OK: src.models")
except Exception as e:
    print(f"FAIL: src.models - {e}")

try:
    import src.services
    print("OK: src.services")
except Exception as e:
    print(f"FAIL: src.services - {e}")

try:
    import src.vcs
    print("OK: src.vcs")
except Exception as e:
    print(f"FAIL: src.vcs - {e}")

try:
    import src.gui
    print("OK: src.gui")
except Exception as e:
    print(f"FAIL: src.gui - {e}")
    import traceback
    traceback.print_exc()

try:
    from src.gui.main_window import MainWindow
    print("OK: MainWindow")
except Exception as e:
    print(f"FAIL: MainWindow - {e}")
    import traceback
    traceback.print_exc()

print("\nAttempting to create window...")
try:
    window = MainWindow()
    window.show()
    print("Window created and shown!")
    print("GUI running... (window should be visible)")
    app.exec()
except Exception as e:
    print(f"Failed: {e}")
    import traceback
    traceback.print_exc()
