#!/usr/bin/env python3
"""打包「抖音私信助手整合版」精简 zip（不含账号/密钥等个人配置）"""
import shutil
import zipfile
from pathlib import Path

SRC = Path(__file__).parent
OUT_DIR = SRC.parent / "DouYin_Spider_整合版"
ZIP_PATH = SRC.parent / "DouYin_Spider_整合版.zip"

EXCLUDE_NAMES = {
    "accounts.json",
    ".env",
    "config_ai.env",
    "accounts.json.bak",
}

EXCLUDE_DIRS = {"__pycache__", "node_modules", ".git", ".venv", "venv"}

ROOT_FILES = [
    "抖音私信助手_整合版.py",
    "启动私信助手_整合版.bat",
    "ai_auto_reply.py",
    "account_manager.py",
    "account_gui.py",
    "auto_login.py",
    "start_login.bat",
    "get_web_protect.js",
    "get_web_protect.html",
    "requirements.txt",
    "package.json",
    ".env.example",
    "config_ai.env.example",
    "README_整合版.txt",
]

DIRS = ["builder", "dy_apis", "utils", "static"]


def should_skip(path: Path) -> bool:
    if path.name in EXCLUDE_NAMES:
        return True
    if any(part in EXCLUDE_DIRS for part in path.parts):
        return True
    if path.suffix == ".pyc":
        return True
    return False


def main():
    if OUT_DIR.exists():
        shutil.rmtree(OUT_DIR)
    if ZIP_PATH.exists():
        ZIP_PATH.unlink()
    OUT_DIR.mkdir(parents=True)

    for name in ROOT_FILES:
        if name in EXCLUDE_NAMES:
            continue
        src = SRC / name
        if src.exists():
            shutil.copy2(src, OUT_DIR / name)

    for d in DIRS:
        dst = OUT_DIR / d
        for item in (SRC / d).rglob("*"):
            if should_skip(item):
                continue
            rel = item.relative_to(SRC / d)
            target = dst / rel
            if item.is_dir():
                target.mkdir(parents=True, exist_ok=True)
            else:
                target.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(item, target)

    (OUT_DIR / "examples").mkdir(exist_ok=True)
    (OUT_DIR / "datas").mkdir(exist_ok=True)
    kb_example = SRC / "examples" / "knowledge_base.example.json"
    if kb_example.exists():
        shutil.copy2(kb_example, OUT_DIR / "examples" / "knowledge_base.example.json")
        shutil.copy2(kb_example, OUT_DIR / "datas" / "knowledge_base.json")
    (OUT_DIR / "datas" / "blacklist.txt").write_text("", encoding="utf-8")

    with zipfile.ZipFile(ZIP_PATH, "w", zipfile.ZIP_DEFLATED) as zf:
        for p in sorted(OUT_DIR.rglob("*")):
            if p.is_file():
                zf.write(p, p.relative_to(OUT_DIR))

    count = sum(1 for _ in OUT_DIR.rglob("*") if _.is_file())
    print(f"OK: {ZIP_PATH}")
    print(f"Size: {ZIP_PATH.stat().st_size / 1024:.1f} KB, files: {count}")
    print("Excluded:", ", ".join(sorted(EXCLUDE_NAMES)))


if __name__ == "__main__":
    main()
