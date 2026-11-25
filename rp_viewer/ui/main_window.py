"""메인 창: 왼쪽 입력창 / 오른쪽 Preview."""
from __future__ import annotations

from pathlib import Path

from PySide6.QtCore import QRect, Qt, QTimer
from PySide6.QtGui import QFont, QGuiApplication
from PySide6.QtWidgets import (QCheckBox, QFileDialog, QHBoxLayout, QLabel, QMainWindow,
                               QPlainTextEdit, QPushButton, QSplitter, QVBoxLayout, QWidget)

from config.settings import Settings
from ui.image_viewer import ImageViewerDialog
from ui.preview import PreviewView
from ui.settings_dialog import SettingsDialog

STYLE = """
QMainWindow, QWidget { background:#2b2d31; color:#dcdcdc; }
QPlainTextEdit { background:#1e1f22; color:#d0d0d0; border:1px solid #3a3c42;
                 selection-background-color:#3d5a80; }
QPushButton { background:#3a3c42; border:1px solid #4a4c52; padding:5px 12px; border-radius:4px; }
QPushButton:hover { background:#45474e; }
QPushButton:pressed { background:#2f3136; }
QLabel#sectionTitle { font-weight:bold; color:#bfc3c9; padding:4px 2px; }
QLabel#repoLabel { color:#9aa0a6; }
QLabel#status { color:#9aa0a6; padding:2px 4px; }
QSplitter::handle { background:#3a3c42; }
QCheckBox::indicator { width:14px; height:14px; }
"""


class MainWindow(QMainWindow):
    def __init__(self, settings: Settings) -> None:
        super().__init__()
        self.settings = settings
        self.setWindowTitle("RP Viewer")
        self.setStyleSheet(STYLE)

        # ---- 상단 도구 모음
        btn_repo = QPushButton("저장소 폴더 선택")
        btn_render = QPushButton("렌더링")
        btn_clear = QPushButton("입력 지우기")
        btn_clip = QPushButton("클립보드에서 붙여넣기")
        self.chk_auto = QCheckBox("자동 렌더링")
        self.chk_auto.setChecked(settings.auto_render)
        btn_settings = QPushButton("설정")
        self.repo_label = QLabel(objectName="repoLabel")
        self._update_repo_label()

        btn_repo.clicked.connect(self.choose_repo)
        btn_render.clicked.connect(self.render_now)
        btn_clear.clicked.connect(self.clear_input)
        btn_clip.clicked.connect(self.paste_from_clipboard)
        self.chk_auto.toggled.connect(self._on_auto_toggled)
        btn_settings.clicked.connect(self.open_settings)

        top = QHBoxLayout()
        for w in (btn_repo, btn_render, btn_clear, btn_clip, self.chk_auto, btn_settings):
            top.addWidget(w)
        top.addSpacing(12)
        top.addWidget(self.repo_label, 1)

        # ---- 왼쪽: 입력
        self.input = QPlainTextEdit()
        self.input.setPlaceholderText("ChatGPT 답변을 여기에 붙여넣으세요.\n\n예) [[ASSET:assets/other/image/Haeyeon.png]]")
        self.input.setFont(QFont(settings.font_family, 11))
        self.input.textChanged.connect(self._on_text_changed)
        left = QWidget()
        ll = QVBoxLayout(left)
        ll.setContentsMargins(0, 0, 0, 0)
        ll.addWidget(QLabel("ChatGPT 출력 붙여넣기", objectName="sectionTitle"))
        ll.addWidget(self.input)

        # ---- 오른쪽: Preview
        self.preview = PreviewView(settings)
        self.preview.imageClicked.connect(self.show_image)
        self.preview.rendered.connect(self._on_rendered)
        right = QWidget()
        rl = QVBoxLayout(right)
        rl.setContentsMargins(0, 0, 0, 0)
        rl.addWidget(QLabel("RP Preview", objectName="sectionTitle"))
        rl.addWidget(self.preview)

        self.splitter = QSplitter(Qt.Horizontal)
        self.splitter.addWidget(left)
        self.splitter.addWidget(right)
        self.splitter.setStretchFactor(0, 2)
        self.splitter.setStretchFactor(1, 3)

        self.status = QLabel(objectName="status")

        central = QWidget()
        cl = QVBoxLayout(central)
        cl.setContentsMargins(8, 8, 8, 4)
        cl.addLayout(top)
        cl.addWidget(self.splitter, 1)
        cl.addWidget(self.status)
        self.setCentralWidget(central)

        # 자동 렌더링 debounce
        self._debounce = QTimer(self, singleShot=True)
        self._debounce.timeout.connect(self.render_now)

        self._restore_geometry()

    # ----------------------------------------------------------------- actions
    def choose_repo(self) -> None:
        start = self.settings.repo_root or str(Path.home())
        folder = QFileDialog.getExistingDirectory(self, "저장소 루트 폴더 선택", start)
        if folder:
            self.set_repo(folder)

    def set_repo(self, folder: str) -> None:
        self.settings.repo_root = str(Path(folder).resolve())  # 항상 절대경로로 저장
        self.settings.save()
        self._update_repo_label()
        self.render_now()

    def render_now(self) -> None:
        self._debounce.stop()
        self.preview.render_text(self.input.toPlainText())

    def clear_input(self) -> None:
        self.input.clear()
        self.render_now()

    def paste_from_clipboard(self) -> None:
        # 향후 자동 감지: QGuiApplication.clipboard().dataChanged 에 연결해 이 메서드를 호출하면 됨
        text = QGuiApplication.clipboard().text()
        if not text:
            self.status.setText("클립보드에 텍스트가 없습니다.")
            return
        self.input.blockSignals(True)
        self.input.setPlainText(text)
        self.input.blockSignals(False)
        self.render_now()

    def open_settings(self) -> None:
        dlg = SettingsDialog(self.settings, self)
        if dlg.exec():
            dlg.apply()
            self.settings.save()
            self.input.setFont(QFont(self.settings.font_family, 11))
            self.render_now()

    def show_image(self, path: Path) -> None:
        ImageViewerDialog(path, self).show()

    # ------------------------------------------------------------------ events
    def _on_text_changed(self) -> None:
        if self.settings.auto_render:
            self._debounce.start(self.settings.render_debounce_ms)

    def _on_auto_toggled(self, on: bool) -> None:
        self.settings.auto_render = on
        self.settings.save()
        if on:
            self.render_now()

    def _on_rendered(self, result) -> None:
        if not self.settings.repo_root:
            self.status.setText("저장소 폴더가 설정되지 않았습니다. [저장소 폴더 선택]을 눌러 주세요.")
            return
        total = result.found + result.missing
        msg = f"에셋 {total}개 · 표시 {result.found} · 누락/차단 {result.missing}"
        self.status.setText(msg if total else "에셋 태그 없음")

    def _update_repo_label(self) -> None:
        root = self.settings.repo_root
        if not root:
            self.repo_label.setText("저장소: (미설정)")
        elif not Path(root).is_dir():
            self.repo_label.setText(f"저장소: {root}  ⚠ 폴더 없음")
        else:
            self.repo_label.setText(f"저장소: {root}")
        self.repo_label.setToolTip(root)

    def _restore_geometry(self) -> None:
        g = self.settings.window_geometry
        rect = QRect(*g) if isinstance(g, list) and len(g) == 4 else None
        screens = QGuiApplication.screens()
        if rect and any(s.availableGeometry().intersects(rect) for s in screens):
            self.setGeometry(rect)
        else:
            self.resize(1400, 900)
        if self.settings.splitter_sizes:
            self.splitter.setSizes(self.settings.splitter_sizes)
        else:
            self.splitter.setSizes([560, 840])
        if self.settings.window_maximized:
            self.setWindowState(Qt.WindowMaximized)

    def closeEvent(self, e) -> None:
        self.settings.window_maximized = self.isMaximized()
        g = self.normalGeometry() if self.isMaximized() else self.geometry()
        self.settings.window_geometry = [g.x(), g.y(), g.width(), g.height()]
        self.settings.splitter_sizes = self.splitter.sizes()
        self.settings.auto_render = self.chk_auto.isChecked()
        self.settings.save()
        super().closeEvent(e)
