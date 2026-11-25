"""이미지 클릭 시 원본 크기로 보여주는 팝업."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import Qt
from PySide6.QtGui import QGuiApplication, QImageReader, QMovie, QPixmap
from PySide6.QtWidgets import QDialog, QLabel, QScrollArea, QVBoxLayout


class ImageViewerDialog(QDialog):
    def __init__(self, path: Path, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle(f"{path.name}")
        self.setAttribute(Qt.WA_DeleteOnClose)

        label = QLabel(alignment=Qt.AlignCenter)
        label.setStyleSheet("background:#111;")
        self._movie = None
        if path.suffix.lower() == ".gif":
            self._movie = QMovie(str(path))
            label.setMovie(self._movie)
            self._movie.start()
            size = self._movie.currentPixmap().size()
        else:
            reader = QImageReader(str(path))
            reader.setAutoTransform(True)
            pix = QPixmap.fromImage(reader.read())
            label.setPixmap(pix)
            size = pix.size()

        scroll = QScrollArea()
        scroll.setWidget(label)
        scroll.setWidgetResizable(True)
        scroll.setAlignment(Qt.AlignCenter)
        scroll.setStyleSheet("QScrollArea{background:#111; border:none;}")

        lay = QVBoxLayout(self)
        lay.setContentsMargins(0, 0, 0, 0)
        lay.addWidget(scroll)

        screen = QGuiApplication.primaryScreen().availableGeometry()
        w = min(size.width() + 24, int(screen.width() * 0.9))
        h = min(size.height() + 24, int(screen.height() * 0.9))
        self.resize(max(w, 200), max(h, 150))
        self.setToolTip(f"{path}\n{size.width()} × {size.height()}")

    def keyPressEvent(self, e) -> None:
        if e.key() in (Qt.Key_Escape, Qt.Key_Space, Qt.Key_Return):
            self.close()
        else:
            super().keyPressEvent(e)
