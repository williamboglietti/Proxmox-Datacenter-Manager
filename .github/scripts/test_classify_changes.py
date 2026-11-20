import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

SCRIPT = Path(__file__).with_name("classify_changes.py").resolve()


class ClassifyChangesTest(unittest.TestCase):
    def setUp(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        self.repo = Path(temp.name)
        self.git("init", "-q")
        self.git("config", "user.name", "Test")
        self.git("config", "user.email", "test@example.invalid")
        self.write("README.md", b"# PDM\n")
        self.write("docs/old.md", b"# Old\n")
        self.git("add", ".")
        self.git("commit", "-qm", "Base")

    def git(self, *args):
        subprocess.run(["git", *args], cwd=self.repo, check=True)

    def write(self, name, data):
        path = self.repo / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(data)
        return path

    def classify(self):
        self.git("add", "-A")
        self.git("commit", "-qm", "Change")
        return subprocess.run(
            [sys.executable, str(SCRIPT), "HEAD^", "HEAD"],
            cwd=self.repo, capture_output=True, text=True,
        )

    def assert_classification(self, docs_only):
        result = self.classify()
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertEqual(result.stdout.strip(), f"docs_only={str(docs_only).lower()}")

    def test_documentation_with_attachment_and_removal(self):
        self.write("README.md", b"# PDM guide\n")
        self.write("docs/guide space.md", b"# Guide\n")
        self.write("docs/manual.pdf", b"%PDF-1.7\n")
        (self.repo / "docs/old.md").unlink()
        self.assert_classification(True)

    def test_mixed_change_requires_image_validation(self):
        self.write("docs/guide.md", b"# Guide\n")
        self.write("Dockerfile", b"FROM debian:trixie-slim\n")
        self.assert_classification(False)

    def test_rejects_configuration_inside_docs(self):
        self.write("docs/settings.yml", b"setting: true\n")
        result = self.classify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("docs/settings.yml", result.stderr)

    def test_rejects_executable_markdown(self):
        self.write("docs/script.md", b"# Documentation\n").chmod(0o755)
        result = self.classify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("docs/script.md", result.stderr)

    def test_rejects_disguised_attachment(self):
        self.write("docs/manual.pdf", b"#!/bin/sh\necho test\n")
        result = self.classify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("docs/manual.pdf", result.stderr)

    def test_rejects_symlink_in_docs(self):
        (self.repo / "docs/link.md").symlink_to("../README.md")
        result = self.classify()
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("docs/link.md", result.stderr)

    def test_rejects_whitespace_errors(self):
        self.write("docs/guide.md", b"# Guide \n")
        self.assertNotEqual(self.classify().returncode, 0)


if __name__ == "__main__":
    unittest.main()
