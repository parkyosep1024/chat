"""JSON 설정 파일 로드/저장.

설정 파일 위치: %APPDATA%\\RPViewer\\settings.json (직접 편집 가능)
소스 실행/EXE 실행 모두 같은 파일을 사용하며, 실행 위치나 작업 디렉터리에 의존하지 않는다.
"""
from __future__ import annotations

import json
import os
import sys
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import List, Optional


def _settings_dir() -> Path:
    appdata = os.environ.get("APPDATA")
    base = Path(appdata) if appdata else Path.home() / "AppData" / "Roaming"
    return base / "RPViewer"


SETTINGS_PATH = _settings_dir() / "settings.json"
# 이전 버전(소스 폴더에 저장)의 설정. 새 위치에 파일이 없을 때 한 번만 읽어서 옮긴다.
LEGACY_SETTINGS_PATH = Path(__file__).resolve().parent.parent / "settings.json"


@dataclass
class Settings:
    repo_root: str = ""
    auto_render: bool = True
    font_size: int = 17                 # 본문 글꼴 크기(px)
    font_family: str = "Malgun Gothic"  # 본문 글꼴
    image_max_width_ratio: float = 0.85  # Preview 너비 대비 이미지 최대 너비
    render_debounce_ms: int = 400
    window_geometry: Optional[List[int]] = None  # [x, y, w, h]
    window_maximized: bool = False
    splitter_sizes: Optional[List[int]] = field(default=None)

    @classmethod
    def load(cls) -> "Settings":
        s = cls()
        src = SETTINGS_PATH
        if (not src.exists() and not getattr(sys, "frozen", False)
                and LEGACY_SETTINGS_PATH.exists()):
            src = LEGACY_SETTINGS_PATH
        try:
            data = json.loads(src.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return s
        if not isinstance(data, dict):
            return s
        known = {f.name for f in fields(cls)}
        for key, value in data.items():
            if key in known:
                setattr(s, key, value)
        s._sanitize()
        return s

    def _sanitize(self) -> None:
        try:
            self.font_size = max(9, min(40, int(self.font_size)))
        except (TypeError, ValueError):
            self.font_size = 17
        try:
            self.image_max_width_ratio = max(0.2, min(1.0, float(self.image_max_width_ratio)))
        except (TypeError, ValueError):
            self.image_max_width_ratio = 0.85
        try:
            self.render_debounce_ms = max(100, min(3000, int(self.render_debounce_ms)))
        except (TypeError, ValueError):
            self.render_debounce_ms = 400
        self.auto_render = bool(self.auto_render)
        if not isinstance(self.repo_root, str):
            self.repo_root = ""
        elif self.repo_root:
            self.repo_root = str(Path(self.repo_root).expanduser().absolute())

    def save(self) -> None:
        try:
            SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
            SETTINGS_PATH.write_text(json.dumps(asdict(self), ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass
