# RP Viewer

ChatGPT 웹에서 복사한 RP 본문을 붙여넣으면 `[[ASSET:상대경로]]` 태그 위치에
로컬 저장소의 이미지를 표시하는 Windows용 뷰어.

이 프로그램은 AI가 아니다. 태그에 적힌 경로를 **그대로** 저장소 루트 기준으로 찾아 표시할 뿐이며,
유사 파일 검색·대체 이미지·자동 판별을 하지 않는다.

## 설치 / 실행

```powershell
py -m pip install -r requirements.txt
py main.py
```

## 사용법

1. `저장소 폴더 선택` → RP 저장소 루트(예: `card.json`이 있는 폴더) 선택. 다음 실행 시 자동 복원.
2. ChatGPT 답변을 왼쪽 입력창에 붙여넣거나 `클립보드에서 붙여넣기` 클릭.
3. 자동 렌더링 ON이면 입력 후 약 400ms 뒤 갱신, OFF면 `렌더링` 버튼.
4. Preview의 이미지를 클릭하면 원본 크기 팝업 (Esc로 닫기, GIF는 팝업에서 애니메이션 재생).

## 태그 규칙

```text
[[ASSET:assets/other/image/Haeyeon.png]]
[[ASSET: assets/other/image/Haeyeon.png ]]   ← 공백 허용
```

- 지원 확장자: png, jpg, jpeg, webp, gif
- `\` 구분자도 허용, ChatGPT 복사 시 붙는 `\_` 같은 Markdown 이스케이프는 경로에서 제거
- 파일 없음 → `⚠ Asset not found` 경고 박스
- `../`, 절대경로, 다른 드라이브 등 저장소 밖 경로 → `⚠ Blocked path` 경고 박스
- `[[BG:...]]` 등 아직 처리기가 없는 태그는 원문 그대로 텍스트로 표시

## 설정 파일

`%APPDATA%\RPViewer\settings.json` (예: `C:\Users\<사용자>\AppData\Roaming\RPViewer\settings.json`)

- 소스 실행(`py main.py`)과 EXE 실행이 같은 파일을 공유한다.
- 실행 위치·작업 디렉터리와 무관. 첫 실행 후 생성되며 직접 편집 가능.
- `repo_root`는 항상 절대경로로 저장된다.

| 키 | 의미 |
|---|---|
| `repo_root` | 저장소 루트 |
| `auto_render` | 자동 렌더링 |
| `font_size`, `font_family` | 본문 글꼴 |
| `image_max_width_ratio` | Preview 너비 대비 이미지 최대 너비 (0.2~1.0) |
| `render_debounce_ms` | 자동 렌더링 지연 |
| `window_geometry`, `window_maximized`, `splitter_sizes` | 창 상태 |

## 구조

```text
main.py                     진입점
config/settings.py          JSON 설정
parser/asset_parser.py      [[KIND:value]] 태그 분리 (태그 의미는 해석하지 않음)
parser/path_resolver.py     상대경로 → 저장소 내부 파일 (보안 검사)
renderer/markdown_lite.py   최소 Markdown (**, *, #, ---)
renderer/story_renderer.py  세그먼트 → HTML, 태그 종류별 처리기(TAG_HANDLERS)
ui/main_window.py           메인 창 / 버튼
ui/preview.py               Preview (QTextBrowser)
ui/image_viewer.py          원본 보기 팝업
ui/settings_dialog.py       설정 창
tests/test_basic.py         테스트:  py -m unittest discover -s tests
```

## 새 태그 추가 (예: BG)

`renderer/story_renderer.py`에서 `_render_bg(self, seg, result, ctx) -> str` 메서드를 만들고
`TAG_HANDLERS`에 `"BG": self._render_bg`를 등록한다. 파서는 수정할 필요 없다.

## EXE 빌드

`build_exe.bat` 더블클릭 (의존성 설치 → 테스트 → PyInstaller `--onedir` 빌드).
소스를 고친 뒤 다시 실행하면 `dist\RPViewer\`가 새로 만들어진다.

```text
dist\RPViewer\
├─ RPViewer.exe      ← 실행 파일 (콘솔 없음)
└─ _internal\        ← Python/Qt 런타임. EXE와 항상 같이 있어야 함
```

- 다른 PC로 옮길 때는 `dist\RPViewer` 폴더 전체를 복사한다. (Python 설치 불필요, Windows 10/11 64bit)
- 이미지 에셋은 EXE에 포함되지 않는다. 실행 후 `저장소 폴더 선택`으로 RP 저장소를 지정한다.
- 바탕화면 바로가기: `RPViewer.exe` 우클릭 → `더 많은 옵션 표시` → `보내기` → `바탕 화면에 바로 가기 만들기`.
  (EXE 파일만 바탕화면으로 복사하면 `_internal`을 못 찾아 실행되지 않는다.)
