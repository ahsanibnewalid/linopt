import ast
import pathlib
import unittest

ROOT = pathlib.Path(__file__).resolve().parents[1]
SOURCE = ROOT / "linopt.py"


class LinOptSafetyTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.source = SOURCE.read_text(encoding="utf-8")
        cls.tree = ast.parse(cls.source)

    def test_source_parses(self):
        self.assertIsNotNone(self.tree)

    def test_subprocess_calls_do_not_enable_shell(self):
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Call) and isinstance(node.func, ast.Attribute):
                if isinstance(node.func.value, ast.Name) and node.func.value.id == "subprocess":
                    for keyword in node.keywords:
                        self.assertFalse(
                            keyword.arg == "shell" and isinstance(keyword.value, ast.Constant)
                            and keyword.value.value is True,
                            "subprocess must not use shell=True",
                        )

    def test_weekly_maintenance_does_not_autoremove_packages(self):
        self.assertIn("/usr/bin/apt-get autoclean -y", self.source)
        self.assertIn("/usr/bin/journalctl --vacuum-size=100M", self.source)
        self.assertNotIn("/usr/bin/apt-get autoremove -y", self.source)

    def test_icon_uses_theme_name(self):
        self.assertIn('self.set_icon_name("linopt")', self.source)
        self.assertNotIn("linopt-icon.png", self.source)

    def test_privileged_package_action_requires_confirmation(self):
        self.assertIn("APT cleanup cancelled.", self.source)
        self.assertIn("Remove unused packages and clean the APT cache?", self.source)


if __name__ == "__main__":
    unittest.main()
