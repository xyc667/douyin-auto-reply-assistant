#!/usr/bin/env python3
"""Scan zip or directory for real sensitive data."""
import re
import sys
import zipfile
from pathlib import Path

PATTERNS = [
    ("API Key", re.compile(r"sk-(?:cp|ant)-[A-Za-z0-9_-]{30,}")),
    ("Session cookie", re.compile(r"sessionid=[a-f0-9]{20,}", re.I)),
    ("Douyin cookie field", re.compile(r"passport_assist_user=")),
    ("WEB_PROTECT ticket", re.compile(r'"ticket"\s*:\s*"hash\.')),
    ("Embedded PEM key", re.compile(r"-----BEGIN PRIVATE KEY-----[A-Za-z0-9+/=\r\n]{40,}-----END")),
]

SKIP_IF_ONLY = {"ec_privateKey", "WEB_PROTECT", "KEYS", "DY_COOKIES"}


def scan_text(path: str, text: str):
    hits = []
    for label, pat in PATTERNS:
        for m in pat.finditer(text):
            val = m.group(0)
            if label == "API Key" and "your-api-key" in val:
                continue
            hits.append((path, label, val[:24] + "..."))
    return hits


def scan_zip(zpath: Path):
    issues = []
    with zipfile.ZipFile(zpath) as z:
        for name in z.namelist():
            if name.endswith("/"):
                continue
            text = z.read(name).decode("utf-8", errors="ignore")
            issues.extend(scan_text(name, text))
    return issues


def scan_dir(dpath: Path, exclude_dirs=None):
    exclude_dirs = exclude_dirs or {".git", "node_modules", "__pycache__", ".venv", "venv"}
    issues = []
    for p in dpath.rglob("*"):
        if not p.is_file():
            continue
        if any(part in exclude_dirs for part in p.parts):
            continue
        if p.suffix in {".pyc", ".zip"}:
            continue
        try:
            text = p.read_text(encoding="utf-8", errors="ignore")
        except Exception:
            continue
        rel = p.relative_to(dpath)
        issues.extend(scan_text(str(rel), text))
    return issues


if __name__ == "__main__":
    proj = Path(__file__).parent
    zip_path = proj / "dist" / "douyin-auto-reply-assistant.zip"

    print("=== ZIP:", zip_path.name, "===")
    if zip_path.exists():
        zi = scan_zip(zip_path)
        if zi:
            for path, label, snip in zi:
                print(f"  LEAK [{label}] {path}: {snip}")
        else:
            print("  Clean: no real credentials found")
    else:
        print("  Not found")

    print("\n=== Project sensitive files (should NOT share) ===")
    for name in [".env", "config_ai.env", "accounts.json", "datas/reply_log.txt"]:
        p = proj / name
        print(f"  {name}: {'EXISTS (keep local)' if p.exists() else 'missing'}")

    print("\n=== Project scan (local dev folder) ===")
    pi = scan_dir(proj)
    # group by file
    by_file = {}
    for path, label, snip in pi:
        by_file.setdefault(path, []).append(label)
    for path in sorted(by_file):
        if any(x in path for x in [".env", "accounts.json", "config_ai.env"]):
            print(f"  EXPECTED [{', '.join(set(by_file[path]))}]: {path}")
        elif "fix_env" in path:
            pass
        else:
            print(f"  CHECK [{', '.join(set(by_file[path]))}]: {path}")
