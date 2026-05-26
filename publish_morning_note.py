"""
publish_morning_note.py — 將晨報 HTML 推送到 GitHub Pages

用法：
  python publish_morning_note.py --date YYYY-MM-DD

來源路徑（自動推算）：
  C:\\Users\\USER\\Claude\\Projects\\每日簡報_daily-briefs\\晨報\\晨報_YYYY-MM-DD.html

目標：
  research-site/morning-notes/晨報_YYYY-MM-DD.html
  research-site/index.html（MORNING_NOTES 陣列自動注入）
"""

import sys
import re
import shutil
import subprocess
from pathlib import Path
from datetime import date, datetime

SRC_DIR  = Path(r"C:\Users\USER\Claude\Projects\每日簡報_daily-briefs\晨報")
HUB_DIR  = Path(__file__).parent
INDEX    = HUB_DIR / "index.html"
DEST_DIR = HUB_DIR / "morning-notes"
MARKER   = "// ← publish_morning_note.py 會自動在這裡插入新紀錄"


def run(cmd: str):
    result = subprocess.run(
        cmd, shell=True, cwd=HUB_DIR,
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        print(f"[ERROR] {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def inject(date_str: str, filename: str) -> bool:
    content = INDEX.read_text(encoding="utf-8")
    if f'"{date_str}"' in content:
        print(f"[SKIP] {date_str} 已在 index.html 中，略過注入")
        return False
    new_entry = f'\n  {{"date": "{date_str}", "file": "{filename}"}},\n  {MARKER}'
    content = content.replace(MARKER, new_entry, 1)
    INDEX.write_text(content, encoding="utf-8")
    return True


def main():
    args = sys.argv[1:]
    if "--date" not in args:
        print("[ERROR] 用法：python publish_morning_note.py --date YYYY-MM-DD")
        sys.exit(1)

    idx = args.index("--date")
    date_str = args[idx + 1]

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"[ERROR] 日期格式應為 YYYY-MM-DD，收到：{date_str}")
        sys.exit(1)

    src = SRC_DIR / f"晨報_{date_str}.html"
    if not src.exists():
        print(f"[ERROR] 找不到 HTML：{src}")
        print("       請先執行 generate_morning_note.py 或加 --html-only 旗標")
        sys.exit(1)

    DEST_DIR.mkdir(exist_ok=True)
    filename = f"晨報_{date_str}.html"
    dest = DEST_DIR / filename
    shutil.copy2(src, dest)
    print(f"[OK] 複製：{filename}")

    injected = inject(date_str, filename)
    if injected:
        print(f"[OK] index.html 已更新")

    run("git add -A")
    run(f'git commit -m "feat: 發布晨報 {date_str}"')
    run("git push")
    print(f"[OK] 已推送到 GitHub")
    print(f"     https://jasonfu1222.github.io/research/")


if __name__ == "__main__":
    main()
