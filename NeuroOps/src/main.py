import sys
import os

# Ensure src and project root are in pythonpath
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(current_dir)
sys.path.append(project_root)
sys.path.append(current_dir)

from ui.main_window import MainWindow
from PyQt6.QtWidgets import QApplication

# Assuming init_db() is defined elsewhere or needs to be added.
# For this change, we'll just add a placeholder if it's not provided.
def init_db():
    print("Initializing database...")
    # Placeholder for actual database initialization logic

def exception_hook(exctype, value, traceback):
    print("Unhandled exception:", file=sys.stderr)
    sys.__excepthook__(exctype, value, traceback)

def main():
    app = QApplication(sys.argv)
    
    # Load Theme
    theme_path = os.path.join(os.path.dirname(__file__), 'ui/styles/global.qss')
    if os.path.exists(theme_path):
        with open(theme_path, 'r') as f:
            app.setStyleSheet(f.read())
    else:
        print(f"Warning: Stylesheet not found at {theme_path}")
            
    window = MainWindow()
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    sys.excepthook = exception_hook
    
    # Init DB
    init_db()
    
    main()
