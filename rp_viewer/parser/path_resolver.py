"""태그 경로 → 저장소 내부의 실제 파일 경로.

추측/유사 검색을 하지 않는다. 지정된 경로가 정확히 존재할 때만 성공한다.
저장소 루트 밖으로 나가는 경로(../, 절대경로, 다른 드라이브)는 차단한다.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

IMAGE_EXTENSIONS = {".png", ".jpg", ".jpeg", ".webp", ".gif"}


@dataclass
class ResolveResult:
    path: Optional[Path]  # 성공 시 실제 파일 경로
    error: Optional[str]  # 실패 사유 (경고 박스 제목)


def resolve_asset(repo_root: str | None, rel_path: str) -> ResolveResult:
    if not repo_root:
        return ResolveResult(None, "Repository folder not set")
    rel = rel_path.strip().replace("\\", "/")
    if not rel:
        return ResolveResult(None, "Empty asset path")
    # 절대경로 / 드라이브 지정 / UNC 경로는 거부
    if rel.startswith("/") or ":" in rel:
        return ResolveResult(None, "Blocked path (outside repository)")

    try:
        root = Path(repo_root).resolve(strict=True)
    except OSError:
        return ResolveResult(None, "Repository folder not found")

    try:
        target = (root / rel).resolve(strict=False)
    except OSError:
        return ResolveResult(None, "Invalid path")

    # normalize 이후 저장소 루트 밖이면 차단 (심볼릭 링크로 밖을 가리키는 경우도 포함)
    if not target.is_relative_to(root):
        return ResolveResult(None, "Blocked path (outside repository)")
    if target.suffix.lower() not in IMAGE_EXTENSIONS:
        return ResolveResult(None, "Unsupported file type")
    if not target.is_file():
        return ResolveResult(None, "Asset not found")
    return ResolveResult(target, None)
