"""최소 Markdown → HTML 변환 (태그가 제거된 일반 텍스트 조각에만 적용).

지원: **굵게**, *기울임*, # 제목(1~6), --- 구분선, 줄바꿈/문단.
"""
from __future__ import annotations

import html
import re
from typing import List

_HEADING = re.compile(r"^(#{1,6})\s+(.*?)\s*#*\s*$")
_HR = re.compile(r"^\s*([-*_])(\s*\1){2,}\s*$")
_BOLD = re.compile(r"\*\*(?=\S)(.+?)(?<=\S)\*\*")
_ITALIC = re.compile(r"(?<![*\w])\*(?=\S)([^*]+?)(?<=\S)\*(?![*\w])")
# ChatGPT 복사 시 남는 Markdown 이스케이프(\*, \_ 등) 제거
_ESCAPED = re.compile(r"\\([\\`*_{}\[\]()#+\-.!>~])")

_HEADING_SIZES = {1: 1.55, 2: 1.35, 3: 1.2, 4: 1.1, 5: 1.0, 6: 1.0}


def inline(text: str) -> str:
    # 1) 이스케이프된 기호를 placeholder로 보호 → 2) HTML escape → 3) 강조 → 4) 복원
    protected: List[str] = []

    def _protect(m: re.Match) -> str:
        protected.append(m.group(1))
        return f"\x00{len(protected) - 1}\x00"

    s = _ESCAPED.sub(_protect, text)
    s = html.escape(s, quote=False)
    s = _BOLD.sub(r"<b>\1</b>", s)
    s = _ITALIC.sub(r"<i>\1</i>", s)
    s = re.sub(r"\x00(\d+)\x00", lambda m: html.escape(protected[int(m.group(1))], quote=False), s)
    return s


def to_html(text: str, font_size: int) -> str:
    """텍스트 조각을 문단/제목/구분선 HTML 블록들로 변환."""
    out: List[str] = []
    para: List[str] = []

    def flush() -> None:
        if para:
            out.append('<p class="para">' + "<br>".join(inline(l) for l in para) + "</p>")
            para.clear()

    for line in text.replace("\r\n", "\n").replace("\r", "\n").split("\n"):
        if not line.strip():
            flush()
            continue
        if _HR.match(line):
            flush()
            out.append('<hr>')
            continue
        m = _HEADING.match(line)
        if m:
            flush()
            level = len(m.group(1))
            size = round(font_size * _HEADING_SIZES[level])
            out.append(f'<p class="heading"><span style="font-size:{size}px; font-weight:bold;">'
                       f'{inline(m.group(2))}</span></p>')
            continue
        para.append(line.strip())
    flush()
    return "\n".join(out)
