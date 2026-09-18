#!/usr/bin/env python3
"""Package every skill in this repo for download.

A skill is any top-level folder with a SKILL.md. Each one is validated and
zipped to dist/<name>.skill and dist/<name>.zip (same archive, two names: .zip
is what claude.ai's skill upload documents, .skill is what skill-creator
produces). The skill folder sits at the root of the archive, as claude.ai
requires:

    make-it-visual.zip
    └── make-it-visual/
        └── SKILL.md

evals/ and examples/ are left out: they are for people browsing the repo, and
SKILL.md never points Claude at them.

    python scripts/build_skills.py            # build all skills into dist/
    python scripts/build_skills.py --check    # validate only
"""

import re
import sys
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DIST = ROOT / "dist"
SKIP_DIRS = {"evals", "examples", "__pycache__", "node_modules", ".git"}
SKIP_FILES = {".DS_Store", "Thumbs.db"}
# Fixed timestamp so the same sources always produce byte-identical archives.
ZIP_DATE = (2020, 1, 1, 0, 0, 0)


def frontmatter(skill_md):
    text = skill_md.read_text(encoding="utf-8").replace("\r\n", "\n")
    match = re.match(r"^---\n(.*?)\n---\n", text, re.S)
    if not match:
        return None
    fields = {}
    for line in match.group(1).splitlines():
        key, sep, value = line.partition(":")
        if sep and not line.startswith((" ", "\t")):
            fields[key.strip()] = value.strip().strip("\"'")
    return fields


def validate(folder):
    """Return a list of problems; empty means the skill is uploadable."""
    fields = frontmatter(folder / "SKILL.md")
    if fields is None:
        return ["SKILL.md has no --- frontmatter block"]
    problems = []
    name, description = fields.get("name", ""), fields.get("description", "")
    if not re.fullmatch(r"[a-z0-9]+(-[a-z0-9]+)*", name) or len(name) > 64:
        problems.append(f"name '{name}' must be kebab-case, 64 characters max")
    if name != folder.name:
        problems.append(f"name '{name}' must match the folder name '{folder.name}'")
    if not description:
        problems.append("description is missing")
    elif len(description) > 1024:
        problems.append(f"description is {len(description)} characters (max 1024)")
    elif "<" in description or ">" in description:
        problems.append("description can't contain angle brackets")
    nested = [p for p in files(folder) if p.name == "SKILL.md" and p.parent != folder]
    if nested:
        problems.append(f"extra SKILL.md files would be rejected on upload: {nested}")
    return problems


def files(folder):
    for path in sorted(folder.rglob("*")):
        rel = path.relative_to(folder)
        if path.is_file() and not SKIP_DIRS.intersection(rel.parts) and path.name not in SKIP_FILES:
            yield path


def package(folder):
    DIST.mkdir(exist_ok=True)
    target = DIST / f"{folder.name}.skill"
    with zipfile.ZipFile(target, "w", zipfile.ZIP_DEFLATED) as zf:
        for path in files(folder):
            info = zipfile.ZipInfo(path.relative_to(ROOT).as_posix(), ZIP_DATE)
            info.compress_type = zipfile.ZIP_DEFLATED
            info.external_attr = 0o644 << 16
            zf.writestr(info, path.read_bytes())
    (DIST / f"{folder.name}.zip").write_bytes(target.read_bytes())
    return target


def main():
    check_only = "--check" in sys.argv[1:]
    skills = sorted(p.parent for p in ROOT.glob("*/SKILL.md"))
    if not skills:
        sys.exit("No skills found (expected <folder>/SKILL.md at the repo root)")
    failed = False
    for folder in skills:
        problems = validate(folder)
        if problems:
            failed = True
            print(f"FAIL {folder.name}")
            for problem in problems:
                print(f"    {problem}")
        elif check_only:
            print(f"ok   {folder.name}")
        else:
            target = package(folder)
            print(f"ok   {folder.name} -> {target.relative_to(ROOT).as_posix()} ({target.stat().st_size / 1024:.1f} KB)")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
