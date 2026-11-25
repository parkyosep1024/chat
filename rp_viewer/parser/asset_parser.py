"""본문 텍스트에서 [[KIND:value]] 태그를 찾아 세그먼트 목록으로 분리한다.

- 태그 종류(KIND)는 대문자/숫자/밑줄로 구성된다. (ASSET, BG, MUSIC, SFX ...)
- 파서는 태그의 의미를 해석하지 않는다. 어떤 태그를 어떻게 표시할지는 renderer가 결정한다.
- Markdown 처리보다 먼저 실행되므로 Markdown 문법이 태그 파싱을 깨뜨리지 않는다.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from typing import List, Union

# [[ ASSET : path ]] 처럼 공백이 섞여도 허용. 값에는 ']' 와 줄바꿈이 들어갈 수 없다.
TAG_PATTERN = re.compile(r"\[\[\s*([A-Z][A-Z0-9_]*)\s*:\s*([^\]\r\n]*?)\s*\]\]")

# ChatGPT 웹에서 복사할 때 Markdown 이스케이프가 붙는 경우가 있다. (예: Sherapic\_default.png)
# 경로 안에서만 해당 이스케이프를 원래 문자로 되돌린다.
_MD_ESCAPE = re.compile(r"\\([_*\[\]`~])")


@dataclass(frozen=True)
class TextSegment:
    text: str


@dataclass(frozen=True)
class TagSegment:
    kind: str   # 예: "ASSET"
    value: str  # 예: "assets/other/image/Haeyeon.png"
    raw: str    # 원문 태그 문자열 (미지원 태그를 그대로 보여줄 때 사용)


Segment = Union[TextSegment, TagSegment]


def clean_value(value: str) -> str:
    return _MD_ESCAPE.sub(r"\1", value.strip())


def parse(text: str) -> List[Segment]:
    """텍스트를 순서대로 TextSegment / TagSegment 리스트로 나눈다."""
    segments: List[Segment] = []
    pos = 0
    for m in TAG_PATTERN.finditer(text):
        if m.start() > pos:
            segments.append(TextSegment(text[pos:m.start()]))
        segments.append(TagSegment(kind=m.group(1), value=clean_value(m.group(2)), raw=m.group(0)))
        pos = m.end()
    if pos < len(text):
        segments.append(TextSegment(text[pos:]))
    return segments
