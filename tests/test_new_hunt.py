import pathlib
import subprocess
import sys
import tempfile
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "skills" / "idea-hunt" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import new_hunt  # noqa: E402


def run(title, outdir):
    return subprocess.run([sys.executable, str(SCRIPTS / "new_hunt.py"), title, "--dir", str(outdir)],
                          capture_output=True, text=True)


class NewHuntTests(unittest.TestCase):
    def test_slugify(self):
        self.assertEqual(new_hunt.slugify("Legal Intake for SMBs!"), "legal-intake-for-smbs")
        self.assertEqual(new_hunt.slugify("!!!"), "hunt")

    def test_creates_file_in_custom_dir_with_substitutions(self):
        with tempfile.TemporaryDirectory() as d:
            out = pathlib.Path(d) / "nested" / "docs"
            r = run("Legal intake", out)
            self.assertEqual(r.returncode, 0)
            body = (out / "idea-hunt-legal-intake.md").read_text()
            self.assertIn("# idea-hunt: Legal intake", body)
            self.assertIn("slug `legal-intake`", body)
            self.assertNotIn("{{", body)

    def test_never_overwrites(self):
        with tempfile.TemporaryDirectory() as d:
            run("Legal intake", d)
            f = pathlib.Path(d) / "idea-hunt-legal-intake.md"
            f.write_text("my notes")
            r = run("Legal intake", d)
            self.assertIn("exists", r.stdout)
            self.assertEqual(f.read_text(), "my notes")


if __name__ == "__main__":
    unittest.main()
