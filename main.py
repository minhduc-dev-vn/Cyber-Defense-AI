"""
main.py — Entry point của Cyber Defense AI.

Chạy: python main.py
"""
import sys
from pathlib import Path

# Thêm thư mục gốc project vào sys.path để import hoạt động đúng
ROOT = Path(__file__).parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from ui.app import App


def main() -> None:
    """Khởi động ứng dụng Cyber Defense AI."""
    app = App()
    app.run()


if __name__ == "__main__":
    main()
