import contextlib
import io
import pathlib
import subprocess
import sys
import tempfile
import unittest
from unittest import mock

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "skills" / "idea-hunt" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import new_hunt  # noqa: E402


def run(title, outdir):
    return subprocess.run([sys.executable, str(SCRIPTS / "new_hunt.py"), title, "--dir", str(outdir)],
                          capture_output=True, text=True, encoding="utf-8")


def artifacts(d):
    return sorted(p.name for p in pathlib.Path(d).glob("idea-hunt-*.md"))


class SlugTests(unittest.TestCase):
    def test_ascii_slugs_unchanged(self):
        self.assertEqual(new_hunt.slugify("Legal Intake for SMBs!"), "legal-intake-for-smbs")

    def test_punctuation_only_titles_stay_distinct(self):
        self.assertTrue(new_hunt.slugify("!!!").startswith("hunt-"))
        self.assertNotEqual(new_hunt.slugify("!!!"), new_hunt.slugify("???"))

    def test_different_scripts_stay_distinct(self):
        self.assertNotEqual(new_hunt.slugify("कानूनी सेवाएं"), new_hunt.slugify("法律事務所"))

    def test_titles_differing_only_in_combining_marks_stay_distinct(self):
        self.assertNotEqual(new_hunt.slugify("काम"), new_hunt.slugify("कीम"))

    def test_slug_is_bounded_and_keeps_long_titles_distinct(self):
        a, b = "a" * 300, "a" * 299 + "b"
        for title in (a, "法" * 300):
            self.assertLessEqual(len(new_hunt.slugify(title).encode("utf-8")), new_hunt.MAX_SLUG_BYTES)
        self.assertNotEqual(new_hunt.slugify(a), new_hunt.slugify(b))


class CliTests(unittest.TestCase):
    def test_creates_file_in_custom_dir_with_substitutions(self):
        with tempfile.TemporaryDirectory() as d:
            out = pathlib.Path(d) / "nested" / "docs"
            r = run("Legal intake", out)
            self.assertEqual(r.returncode, 0)
            body = (out / "idea-hunt-legal-intake.md").read_text(encoding="utf-8")
            self.assertIn("# idea-hunt: Legal intake", body)
            self.assertIn("slug `legal-intake`", body)
            self.assertNotIn("{{", body)

    def test_same_title_resumes_and_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            run("Legal intake", d)
            f = pathlib.Path(d) / "idea-hunt-legal-intake.md"
            f.write_text(f.read_text(encoding="utf-8") + "\nmy notes", encoding="utf-8")
            r = run("Legal intake", d)
            self.assertIn("resuming", r.stdout)
            self.assertTrue(f.read_text(encoding="utf-8").endswith("my notes"))
            self.assertEqual(artifacts(d), ["idea-hunt-legal-intake.md"])

    def test_resume_survives_editing_the_heading(self):
        with tempfile.TemporaryDirectory() as d:
            run("Legal intake", d)
            f = pathlib.Path(d) / "idea-hunt-legal-intake.md"
            f.write_text(f.read_text(encoding="utf-8").replace("# idea-hunt: Legal intake", "# my hunt"),
                         encoding="utf-8")
            self.assertIn("resuming", run("Legal intake", d).stdout)
            self.assertEqual(len(artifacts(d)), 1)

    def test_different_title_with_same_slug_is_not_silently_resumed(self):
        with tempfile.TemporaryDirectory() as d:
            run("Legal Intake", d)
            r = run("legal intake", d)
            self.assertEqual(r.returncode, 0)
            self.assertIn("different title", r.stdout)
            self.assertEqual(len(artifacts(d)), 2)
            self.assertIn("resuming", run("legal intake", d).stdout)
            self.assertEqual(len(artifacts(d)), 2)

    def test_titles_with_distinct_whitespace_are_not_silently_resumed(self):
        with tempfile.TemporaryDirectory() as d:
            run("Legal intake", d)
            r = run("Legal  intake", d)
            self.assertEqual(r.returncode, 0)
            self.assertIn("different title", r.stdout)
            self.assertEqual(len(artifacts(d)), 2)

    def test_combining_mark_titles_get_separate_files(self):
        with tempfile.TemporaryDirectory() as d:
            run("काम", d)
            run("कीम", d)
            self.assertEqual(len(artifacts(d)), 2)

    def test_long_titles_do_not_crash(self):
        with tempfile.TemporaryDirectory() as d:
            for title in ("a" * 300, "法" * 300):
                r = run(title, d)
                self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(len(artifacts(d)), 2)

    def test_filesystem_failure_is_one_line_error(self):
        with tempfile.TemporaryDirectory() as d:
            blocker = pathlib.Path(d) / "afile"
            blocker.write_text("x", encoding="utf-8")
            r = run("Legal intake", blocker / "docs")
            self.assertNotEqual(r.returncode, 0)
            self.assertNotIn("Traceback", r.stderr)
            self.assertEqual(len(r.stderr.strip().splitlines()), 1)

    def test_create_is_exclusive_even_if_exists_check_lies(self):
        with tempfile.TemporaryDirectory() as d:
            f = pathlib.Path(d) / "idea-hunt-legal-intake.md"
            f.write_text("my notes", encoding="utf-8")
            with mock.patch.object(pathlib.Path, "exists", return_value=False), \
                    mock.patch.object(sys, "argv", ["new_hunt.py", "Legal intake", "--dir", d]), \
                    contextlib.redirect_stdout(io.StringIO()), contextlib.redirect_stderr(io.StringIO()):
                new_hunt.main()
            self.assertEqual(f.read_text(encoding="utf-8"), "my notes")


if __name__ == "__main__":
    unittest.main()
