"""
调试 GUI 导入问题
"""
import sys
import os

script_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, script_dir)

print("Step 1: Creating QApplication...")
from PySide6.QtWidgets import QApplication
app = QApplication([])
print("  OK")

print("\nStep 2: Importing src.gui...")
try:
    import src.gui
    print("  OK")
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nStep 3: Importing MainWindow...")
try:
    from src.gui import MainWindow
    print("  OK")
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nStep 4: Creating MainWindow...")
try:
    window = MainWindow()
    print("  OK")
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nStep 5: Showing window...")
try:
    window.show()
    print("  OK")
except Exception as e:
    print(f"  FAILED: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("\nAll steps passed! Starting app...")
sys.exit(app.exec())
