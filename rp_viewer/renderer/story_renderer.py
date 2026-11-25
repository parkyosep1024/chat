"""파싱된 세그먼트 → QTextDocument용 HTML.

태그 종류별 처리는 TAG_HANDLERS에 등록한다. 등록되지 않은 태그는 원문 그대로 텍스트로 표시한다.
향후 BG / MUSIC / SFX 를 추가하려면 _render_xxx 메서드를 만들고 TAG_HANDLERS에 넣으면 된다.
"""
from __future__ import annotations

import html
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Dict, List, Tuple

from PySide6.QtCore import QSize, Qt, QUrl
from PySide6.QtGui import QImage, QImageReader

from config.settings import Settings
from parser.asset_parser import TagSegment, TextSegment, parse
from parser.path_resolver import resolve_asset
from renderer import markdown_lite

COLORS = {
    "bg": "#1e1f22",
    "text": "#d8d8d8",
    "heading": "#f0f0f0",
    "hr": "#4a4c52",
    "warn_bg": "#3a2a1c",
    "warn_border": "#a8742c",
    "warn_text": "#f0c27a",
    "muted": "#8a8d93",
}


@dataclass
class RenderResult:
    html: str
    images: List[Path] = field(default_factory=list)       # 링크 "asset:N" → images[N]
    resources: Dict[str, QImage] = field(default_factory=dict)  # 문서에 등록할 축소 이미지
    found: int = 0
    missing: int = 0


class StoryRenderer:
    def __init__(self) -> None:
        # 원본 이미지 캐시: path → (mtime, QImage). 같은 본문을 다시 렌더링할 때 디스크 재읽기 방지.
        self._cache: Dict[Path, Tuple[float, QImage]] = {}
        self.TAG_HANDLERS: Dict[str, Callable[[TagSegment, RenderResult, "_Ctx"], str]] = {
            "ASSET": self._render_asset,
            # "BG": self._render_bg,
            # "MUSIC": self._render_music,
        }

    # ------------------------------------------------------------------ public
    def render(self, text: str, settings: Settings, view_width: int, dpr: float = 1.0) -> RenderResult:
        ctx = _Ctx(settings, max(100, view_width), dpr)
        result = RenderResult(html="")
        parts: List[str] = []
        for seg in parse(text):
            if isinstance(seg, TextSegment):
                parts.append(markdown_lite.to_html(seg.text, settings.font_size))
            else:
                handler = self.TAG_HANDLERS.get(seg.kind)
                if handler is None:
                    # 미지원 태그: 원문 그대로 표시 (숨기지도, 해석하지도 않음)
                    parts.append(markdown_lite.to_html(seg.raw, settings.font_size))
                else:
                    parts.append(handler(seg, result, ctx))
        result.html = self._wrap(parts, settings)
        return result

    # ---------------------------------------------------------------- handlers
    def _render_asset(self, seg: TagSegment, result: RenderResult, ctx: "_Ctx") -> str:
        res = resolve_asset(ctx.settings.repo_root, seg.value)
        img = self._load(res.path) if res.path else None
        if img is None or img.isNull():
            result.missing += 1
            reason = res.error or "Cannot read image"
            return self._warning_box(reason, seg.value, ctx)

        result.found += 1
        idx = len(result.images)
        result.images.append(res.path)

        # 원본 비율 유지, 최대 너비 = 뷰 너비 × 비율, 작은 이미지는 확대하지 않음
        max_w = int(ctx.view_width * ctx.settings.image_max_width_ratio)
        w, h = img.width(), img.height()
        if w > max_w:
            h = max(1, round(h * max_w / w))
            w = max_w
        # 고DPI에서도 선명하도록 실제 픽셀 크기로 미리 부드럽게 축소
        px = QSize(max(1, round(w * ctx.dpr)), max(1, round(h * ctx.dpr)))
        scaled = img if px.width() >= img.width() else img.scaled(
            px, Qt.IgnoreAspectRatio, Qt.SmoothTransformation)
        # authority 없는 형식 사용 (rpimg://0/... 은 QUrl이 0.0.0.0 으로 바꿔버림)
        name = QUrl(f"rpimg:img{idx}_{w}x{h}").toString()
        result.resources[name] = scaled
        return (f'<p class="img" align="center"><a href="asset:{idx}">'
                f'<img src="{name}" width="{w}" height="{h}"></a></p>')

    # ----------------------------------------------------------------- helpers
    def _load(self, path: Path) -> QImage | None:
        try:
            mtime = path.stat().st_mtime
        except OSError:
            return None
        cached = self._cache.get(path)
        if cached and cached[0] == mtime:
            return cached[1]
        reader = QImageReader(str(path))
        reader.setAutoTransform(True)
        img = reader.read()  # GIF는 첫 프레임 (원본 보기 팝업에서는 애니메이션 재생)
        if img.isNull():
            return None
        self._cache[path] = (mtime, img)
        return img

    @staticmethod
    def _warning_box(reason: str, value: str, ctx: "_Ctx") -> str:
        c = COLORS
        small = max(11, ctx.settings.font_size - 3)
        return (
            f'<table class="warn" align="center" cellpadding="10" cellspacing="0" '
            f'style="background-color:{c["warn_bg"]}; border:1px solid {c["warn_border"]};">'
            f'<tr><td style="color:{c["warn_text"]}; font-size:{small}px;">'
            f'⚠ {html.escape(reason)}:<br>'
            f'<span style="font-family:Consolas, monospace;">{html.escape(value) or "(empty)"}</span>'
            f'</td></tr></table>'
        )

    @staticmethod
    def _wrap(parts: List[str], s: Settings) -> str:
        c = COLORS
        fam = html.escape(s.font_family, quote=True)
        para_gap = round(s.font_size * 0.9)
        css = f"""
            body {{ color:{c['text']}; font-family:'{fam}'; font-size:{s.font_size}px; }}
            p.para {{ margin-top:0px; margin-bottom:{para_gap}px; line-height:165%; }}
            p.heading {{ color:{c['heading']}; margin-top:{para_gap}px; margin-bottom:{para_gap}px; }}
            p.img {{ margin-top:{para_gap}px; margin-bottom:{para_gap * 2}px; }}
            table.warn {{ margin-top:{para_gap}px; margin-bottom:{para_gap * 2}px; }}
            hr {{ color:{c['hr']}; }}
            a {{ text-decoration:none; }}
        """
        return f"<html><head><style>{css}</style></head><body>{''.join(parts)}</body></html>"


@dataclass
class _Ctx:
    settings: Settings
    view_width: int
    dpr: float
