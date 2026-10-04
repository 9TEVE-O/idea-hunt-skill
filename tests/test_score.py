import json
import pathlib
import subprocess
import sys
import unittest

SCRIPTS = pathlib.Path(__file__).resolve().parent.parent / "skills" / "idea-hunt" / "scripts"
sys.path.insert(0, str(SCRIPTS))
import score  # noqa: E402


def cand(name, **over):
    s = dict(painkiller=2, ai_native=2, reachable_owner=2, urgency=2, buildable=2, moat=2)
    s.update(over)
    return {"name": name, "scores": s}


class ScoreTests(unittest.TestCase):
    def test_perfect_survives(self):
        self.assertTrue(score.evaluate(cand("a"))["survives"])

    def test_zero_is_hard_fail_even_with_high_total(self):
        r = score.evaluate(cand("a", moat=0))
        self.assertEqual(r["total"], 10)
        self.assertFalse(r["survives"])

    def test_low_total_rejected(self):
        r = score.evaluate(cand("a", painkiller=1, ai_native=1, reachable_owner=1, urgency=1, buildable=1, moat=1))
        self.assertEqual(r["total"], 6)
        self.assertFalse(r["survives"])

    def test_threshold_boundary(self):
        r = score.evaluate(cand("a", painkiller=1, ai_native=1, reachable_owner=1, urgency=1))
        self.assertEqual(r["total"], 8)
        self.assertTrue(r["survives"])

    def test_invalid_score_and_missing_gate(self):
        with self.assertRaises(ValueError):
            score.evaluate(cand("a", moat=3))
        with self.assertRaises(ValueError):
            score.evaluate({"name": "a", "scores": {"painkiller": 2}})

    def test_rejects_non_integer_and_malformed_input(self):
        for bad in (True, 1.0, "2", None):
            with self.assertRaises(ValueError):
                score.evaluate(cand("a", moat=bad))
        for bad in (1, "x", {"name": 3}, {"name": "a", "scores": []}):
            with self.assertRaises(ValueError):
                score.evaluate(bad)

    def test_cli_malformed_list_exits_2_without_traceback(self):
        r = subprocess.run([sys.executable, str(SCRIPTS / "score.py")], input="[1]",
                           capture_output=True, text=True)
        self.assertEqual(r.returncode, 2)
        self.assertNotIn("Traceback", r.stderr)

    def test_table_names_cannot_break_markdown_rows(self):
        out = score.render([score.evaluate(cand("a|b\nc\\d"))])
        row = [l for l in out.splitlines() if l.startswith("| a")][0]
        self.assertIn("a\\|b c\\\\d", row)
        self.assertEqual(len([l for l in out.splitlines() if l.startswith("|")]), 3)

    def test_cli_exit_codes(self):
        ok = subprocess.run([sys.executable, str(SCRIPTS / "score.py")], input=json.dumps([cand("a")]),
                            capture_output=True, text=True)
        self.assertEqual(ok.returncode, 0)
        self.assertIn("SURVIVES", ok.stdout)
        bad = subprocess.run([sys.executable, str(SCRIPTS / "score.py")], input="{}",
                             capture_output=True, text=True)
        self.assertEqual(bad.returncode, 2)


if __name__ == "__main__":
    unittest.main()
