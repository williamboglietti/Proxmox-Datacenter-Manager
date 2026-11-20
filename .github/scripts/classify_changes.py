"""Classify a Git diff and validate the files reserved for documentation."""

import subprocess
import sys
from pathlib import PurePosixPath

ROOT_DOCS = {"README.md", "README.fr.md"}
TEXT_EXTENSIONS = {".md", ".rst", ".txt"}
SIGNATURES = {
    ".gif": (b"GIF87a", b"GIF89a"),
    ".jpeg": (b"\xff\xd8\xff",),
    ".jpg": (b"\xff\xd8\xff",),
    ".pdf": (b"%PDF-",),
    ".png": (b"\x89PNG\r\n\x1a\n",),
}


def git(*args):
    return subprocess.check_output(["git", *args])


def valid_document(path, oid):
    suffix = PurePosixPath(path).suffix.lower()
    if suffix not in TEXT_EXTENSIONS and suffix not in SIGNATURES:
        return False

    data = git("cat-file", "blob", oid)
    if suffix in TEXT_EXTENSIONS:
        try:
            content = data.decode("utf-8-sig")
        except UnicodeDecodeError:
            return False
        return "\x00" not in content and not content.lstrip().startswith("#!")
    return data.startswith(SIGNATURES[suffix])


def main(base, head):
    subprocess.run(["git", "diff", "--check", base, head, "--"], check=True)
    diff = git("diff", "--raw", "--no-renames", "--no-abbrev", "-z", base, head, "--")
    records = diff.split(b"\0")[:-1]
    docs_only = bool(records)
    for metadata, raw_path in zip(records[::2], records[1::2]):
        _, mode, _, oid, status = metadata.decode("ascii").split()
        path = raw_path.decode("utf-8", errors="surrogateescape")
        if path not in ROOT_DOCS and not path.startswith("docs/"):
            docs_only = False
            continue

        # A deletion may remove a file that was previously misplaced.
        if status != "D" and (mode != "100644" or not valid_document(path, oid)):
            sys.exit(f"Fichier non autorisé dans la documentation : {path!r}")

    print(f"docs_only={str(docs_only).lower()}")


if __name__ == "__main__":
    main(*sys.argv[1:])
