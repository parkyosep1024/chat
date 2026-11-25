"""설정 대화상자."""
from __future__ import annotations

from PySide6.QtGui import QFont
from PySide6.QtWidgets import (QDialog, QDialogButtonBox, QFontComboBox, QFormLayout,
                               QLabel, QSpinBox)

from config.settings import SETTINGS_PATH, Settings


class SettingsDialog(QDialog):
    def __init__(self, settings: Settings, parent=None) -> None:
        super().__init__(parent)
        self.setWindowTitle("설정")
        self.settings = settings

        self.font_family = QFontComboBox()
        self.font_family.setCurrentFont(QFont(settings.font_family))
        self.font_size = QSpinBox(minimum=9, maximum=40, suffix=" px")
        self.font_size.setValue(settings.font_size)
        self.img_ratio = QSpinBox(minimum=20, maximum=100, suffix=" %")
        self.img_ratio.setValue(round(settings.image_max_width_ratio * 100))
        self.debounce = QSpinBox(minimum=100, maximum=3000, singleStep=50, suffix=" ms")
        self.debounce.setValue(settings.render_debounce_ms)

        form = QFormLayout(self)
        form.addRow("본문 글꼴", self.font_family)
        form.addRow("글꼴 크기", self.font_size)
        form.addRow("이미지 최대 너비", self.img_ratio)
        form.addRow("자동 렌더링 지연", self.debounce)
        path_label = QLabel(f"설정 파일: {SETTINGS_PATH}")
        path_label.setStyleSheet("color:#888;")
        path_label.setWordWrap(True)
        form.addRow(path_label)
        buttons = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        form.addRow(buttons)

    def apply(self) -> None:
        s = self.settings
        s.font_family = self.font_family.currentFont().family()
        s.font_size = self.font_size.value()
        s.image_max_width_ratio = self.img_ratio.value() / 100
        s.render_debounce_ms = self.debounce.value()
