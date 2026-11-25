"""기본 테스트.  실행:  py -m unittest discover -s tests   (rp_viewer 폴더에서)"""
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PySide6.QtGui import QGuiApplication, QImage  # noqa: E402

from config.settings import Settings  # noqa: E402
from parser.asset_parser import TagSegment, TextSegment, parse  # noqa: E402
from parser.path_resolver import resolve_asset  # noqa: E402
from renderer.story_renderer import StoryRenderer  # noqa: E402

app = QGuiApplication.instance() or QGuiApplication(["test", "-platform", "offscreen"])


class ParserTest(unittest.TestCase):
    def test_multiple_tags_in_order(self):
        text = "A\n\n[[ASSET:a/b.png]]\n\nB\n\n[[ASSET: c/d.png ]]\n\nC"
        segs = parse(text)
        tags = [s for s in segs if isinstance(s, TagSegment)]
        self.assertEqual([t.value for t in tags], ["a/b.png", "c/d.png"])
        self.assertIsInstance(segs[0], TextSegment)
        self.assertEqual(segs[1].value, "a/b.png")
        self.assertTrue(segs[2].text.strip() == "B")

    def test_spaces_and_md_escape(self):
        self.assertEqual(parse("[[ ASSET :  x/Sherapic\\_default.png  ]]")[0].value, "x/Sherapic_default.png")

    def test_future_kinds_parsed(self):
        kinds = [s.kind for s in parse("[[BG:a.png]][[MUSIC:b.mp3]][[ASSET:c.png]]")]
        self.assertEqual(kinds, ["BG", "MUSIC", "ASSET"])

    def test_markdown_does_not_break(self):
        segs = parse("**굵게 [[ASSET:a/b_c*d.png]] 끝**")
        self.assertEqual([s.value for s in segs if isinstance(s, TagSegment)], ["a/b_c*d.png"])


class ResolverTest(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name) / "repo"
        (self.root / "assets").mkdir(parents=True)
        img = QImage(40, 20, QImage.Format_RGB32)
        img.fill(0xff3366)
        img.save(str(self.root / "assets" / "ok.png"))
        img.save(str(Path(self.tmp.name) / "outside.png"))

    def tearDown(self):
        self.tmp.cleanup()

    def test_ok(self):
        self.assertIsNotNone(resolve_asset(str(self.root), "assets/ok.png").path)
        self.assertIsNotNone(resolve_asset(str(self.root), "assets\\ok.png").path)
        self.assertIsNotNone(resolve_asset(str(self.root), "./assets/../assets/ok.png").path)

    def test_missing(self):
        r = resolve_asset(str(self.root), "assets/none.png")
        self.assertIsNone(r.path)
        self.assertEqual(r.error, "Asset not found")

    def test_blocked(self):
        for bad in ["../outside.png", "assets/../../outside.png",
                    str(Path(self.tmp.name) / "outside.png"), "C:/Windows/win.ini",
                    "/Windows/win.ini", "\\\\server\\share\\a.png", "../../Windows/System32/x.png"]:
            r = resolve_asset(str(self.root), bad)
            self.assertIsNone(r.path, bad)
            self.assertIn("Blocked", r.error, bad)

    def test_non_image_rejected(self):
        (self.root / "card.json").write_text("{}")
        self.assertEqual(resolve_asset(str(self.root), "card.json").error, "Unsupported file type")

    def test_render(self):
        s = Settings(repo_root=str(self.root))
        r = StoryRenderer().render("첫 줄\n\n[[ASSET:assets/ok.png]]\n\n**굵게**\n\n[[ASSET:assets/x.png]]\n\n[[ASSET:../outside.png]]",
                                   s, view_width=800)
        self.assertEqual((r.found, r.missing), (1, 2))
        self.assertNotIn("[[ASSET", r.html)
        self.assertIn("<b>굵게</b>", r.html)
        self.assertIn("Asset not found", r.html)
        self.assertIn('width="40"', r.html)  # 작은 이미지는 확대하지 않음

    def test_large_image_shrinks(self):
        big = QImage(3000, 6000, QImage.Format_RGB32)
        big.fill(0)
        big.save(str(self.root / "assets" / "tall.png"))
        s = Settings(repo_root=str(self.root), image_max_width_ratio=0.85)
        r = StoryRenderer().render("[[ASSET:assets/tall.png]]", s, view_width=1000)
        self.assertIn('width="850" height="1700"', r.html)


if __name__ == "__main__":
    unittest.main()
