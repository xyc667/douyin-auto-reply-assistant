#!/usr/bin/env python3
import re
import subprocess
from pathlib import Path

cwd = Path(__file__).parent
files = subprocess.run(["git", "ls-files"], cwd=cwd, capture_output=True, text=True).stdout.strip().splitlines()

patterns = [
    ("API Key", re.compile(r"sk-(?:cp|ant)-[A-Za-z0-9_-]{30,}")),
    ("Session cookie", re.compile(r"sessionid=[a-f0-9]{20,}", re.I)),
    ("passport cookie", re.compile(r"passport_assist_user=")),
    ('WEB_PROTECT ticket', re.compile(r'"ticket"\s*:\s*"hash\.')),
    ("PEM private key", re.compile(r"-----BEGIN PRIVATE KEY-----")),
    ("Real API key env", re.compile(r"(?:ANTHROPIC_API_KEY|MINIMAX_API_KEY)=sk-")),
]

issues = []
for name in files:
    p = cwd / name
    if not p.is_file():
        continue
    text = p.read_text(encoding="utf-8", errors="ignore")
    for label, pat in patterns:
        m = pat.search(text)
        if not m:
            continue
        val = m.group(0)
        if "your-api-key" in val or "sk-ant-xxx" in val:
            continue
        issues.append((name, label))

print(f"Tracked files: {len(files)}")
if issues:
    print("ISSUES:")
    for f, l in issues:
        print(f"  [{l}] {f}")
else:
    print("OK: no real credentials in git-tracked files")

for name in [".env.example", "config_ai.env.example"]:
    p = cwd / name
    if p.exists():
        t = p.read_text(encoding="utf-8")
        ok = not any(x in t for x in ["sk-cp-", "sessionid=", "BEGIN PRIVATE KEY", "passport_assist"])
        print(f"{name}: {'clean template' if ok else 'CHECK FAILED'}")

for name in [".env", "config_ai.env", "accounts.json", "datas/reply_log.txt"]:
    tracked = name in files
    local = (cwd / name).exists()
    print(f"{name}: on disk={local}, in git={tracked}")
