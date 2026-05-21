"""
publish.py — 一鍵發布新研究報告到 GitHub Pages

用法：
  python publish.py <HTML檔路徑> [--slug 自訂網址名稱]

範例：
  python publish.py "C:/Users/USER/Claude/Projects/researcher-us/整體產業研究/20260601_某篇報告.html"
  python publish.py report.html --slug 20260601-broadcom-deep-dive
"""

import sys, shutil, subprocess, re, json
from pathlib import Path
from datetime import date

HUB_DIR = Path(__file__).parent
INDEX_HTML = HUB_DIR / "index.html"


def run(cmd, cwd=None):
    result = subprocess.run(
        cmd,
        shell=True,
        cwd=cwd or HUB_DIR,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    if result.returncode != 0:
        print(f"[ERROR] {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def slugify(text):
    text = re.sub(r"[^\w一-鿿-]", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:60].lower()


def main():
    args = sys.argv[1:]
    if not args:
        print(__doc__)
        sys.exit(0)

    # 解析參數
    src = None
    slug = None
    i = 0
    while i < len(args):
        if args[i] == "--slug" and i + 1 < len(args):
            slug = args[i + 1]
            i += 2
        else:
            src = Path(args[i])
            i += 1

    if not src or not src.exists():
        print(f"[ERROR] 找不到檔案：{src}")
        sys.exit(1)

    today = date.today().strftime("%Y%m%d")
    if not slug:
        slug = f"{today}-{slugify(src.stem)}"

    dest_name = f"{slug}.html"
    dest = HUB_DIR / dest_name

    # 複製報告進 hub
    shutil.copy2(src, dest)
    print(f"[OK] 已複製：{dest_name}")

    # 提示使用者更新 index.html 的 REPORTS 陣列
    print()
    print("=" * 60)
    print("請在 index.html 的 REPORTS 陣列裡新增這一筆：")
    print("=" * 60)
    print(f"""  {{
    date: "{date.today().isoformat()}",
    type: "sector",   // sector | company | macro | strategy
    icon: "📄",
    title: "（請填入標題）",
    desc:  "（請填入摘要）",
    file:  "{dest_name}",
    tags:  [],
  }},""")
    print("=" * 60)
    print()

    # git commit & push
    run("git add -A")
    msg = f"feat: 新增報告 {dest_name}"
    run(f'git commit -m "{msg}"')
    run("git push")
    print(f"[OK] 已 push 到 GitHub")
    print()
    print(f"🔗 報告網址（約 1 分鐘後生效）：")
    print(f"   https://jasonfu1222.github.io/research/{dest_name}")
    print(f"   首頁：https://jasonfu1222.github.io/research/")


if __name__ == "__main__":
    main()
