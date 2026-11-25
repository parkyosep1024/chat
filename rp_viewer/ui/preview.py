"""RP Preview 영역 (QTextBrowser 기반)."""
from __future__ import annotations

from pathlib import Path
from typing import List

from PySide6.QtCore import QTimer, QUrl, Signal
from PySide6.QtWidgets import QTextBrowser

from config.settings import Settings
from renderer.story_renderer import COLORS, RenderResult, StoryRenderer


class PreviewView(QTextBrowser):
    imageClicked = Signal(Path)
    rendered = Signal(object)  # RenderResult

    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self.settings = settings
        self.renderer = StoryRenderer()
        self._text = ""
        self._images: List[Path] = []
        self._resources: dict = {}
        self._last_width = -1

        self.setOpenLinks(False)
        self.setOpenExternalLinks(False)
        self.anchorClicked.connect(self._on_anchor)
        self.setStyleSheet(
            f"QTextBrowser{{background:{COLORS['bg']}; color:{COLORS['text']}; border:none;}}")
        self.document().setDocumentMargin(28)

        # 창 크기 변경 시 이미지 크기 재계산 (debounce)
        self._resize_timer = QTimer(self, singleShot=True, interval=150)
        self._resize_timer.timeout.connect(self._rerender_keep_scroll)

    def render_text(self, text: str) -> RenderResult:
        self._text = text
        return self._rerender_keep_scroll()

    def _content_width(self) -> int:
        return self.viewport().width() - int(self.document().documentMargin() * 2)

    def _rerender_keep_scroll(self) -> RenderResult:
        bar = self.verticalScrollBar()
        old_val, old_max = bar.value(), bar.maximum()
        at_bottom = old_max > 0 and old_val >= old_max - 4

        self._last_width = self.viewport().width()
        result = self.renderer.render(self._text, self.settings, self._content_width(),
                                      self.devicePixelRatioF())
        self._resources = result.resources
        self._images = result.images
        self.setHtml(result.html)

        # 스크롤 위치 유지 (맨 아래였다면 맨 아래 유지)
        new_max = bar.maximum()
        if at_bottom:
            bar.setValue(new_max)
        elif old_max > 0:
            bar.setValue(round(old_val * new_max / old_max) if new_max != old_max else old_val)
        self.rendered.emit(result)
        return result

    def loadResource(self, rtype: int, url: QUrl):
        # 렌더러가 미리 축소해 둔 이미지만 제공. 그 외 외부 리소스는 로드하지 않음.
        img = self._resources.get(url.toString())
        return img if img is not None else None

    def resizeEvent(self, e) -> None:
        super().resizeEvent(e)
        if self._text and self.viewport().width() != self._last_width:
            self._resize_timer.start()

    def _on_anchor(self, url: QUrl) -> None:
        s = url.toString()
        if s.startswith("asset:"):
            try:
                self.imageClicked.emit(self._images[int(s[6:])])
            except (ValueError, IndexError):
                pass
