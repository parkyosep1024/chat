"""RP Viewer 진입점.  실행:  py main.py"""
from __future__ import annotations

import sys
from pathlib import Path

# 어디서 실행해도 패키지(config/parser/renderer/ui)를 찾을 수 있게
sys.path.insert(0, str(Path(__file__).resolve().parent))

from PySide6.QtWidgets import QApplication  # noqa: E402

from config.settings import Settings  # noqa: E402
from ui.main_window import MainWindow  # noqa: E402


def main() -> int:
    app = QApplication(sys.argv)
    app.setApplicationName("RP Viewer")
    settings = Settings.load()
    win = MainWindow(settings)
    win.show()
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
