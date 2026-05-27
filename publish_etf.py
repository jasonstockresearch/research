"""
publish_etf.py — 將主動式 ETF 追蹤日報 HTML 推送到 GitHub Pages

用法：
  python publish_etf.py --date YYYY-MM-DD

來源：
  C:\\Users\\USER\\Claude\\Projects\\ETF追蹤專案\\reports\\ETF監測報告_YYYY-MM-DD.html

目標：
  research-site/etf/etf_YYYYMMDD.html
  research-site/index.html（ETF_REPORTS 陣列自動注入）
"""

import sys
import re
import shutil
import subprocess
import json
from pathlib import Path
from datetime import datetime

SRC_DIR  = Path(r"C:\Users\USER\Claude\Projects\ETF追蹤專案\reports")
HUB_DIR  = Path(__file__).parent
INDEX    = HUB_DIR / "index.html"
DEST_DIR = HUB_DIR / "etf"
MARKER   = "// ← publish_etf.py 會自動在這裡插入新紀錄"


def run(cmd: str):
    result = subprocess.run(
        cmd, shell=True, cwd=HUB_DIR,
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        print(f"[ERROR] {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def _count_radar(html_path: Path):
    """從 HTML 報告中粗略計算雷達訊號數（用於首頁摘要）。"""
    try:
        text = html_path.read_text(encoding="utf-8")
        buy  = len(re.findall(r"新增雷達.*?<tbody>(.*?)</tbody>", text, re.S))
        sell = len(re.findall(r"賣出雷達.*?<tbody>(.*?)</tbody>", text, re.S))
        add  = len(re.findall(r"加碼雷達.*?<tbody>(.*?)</tbody>", text, re.S))
        cut  = len(re.findall(r"減碼雷達.*?<tbody>(.*?)</tbody>", text, re.S))
        # 更精確：數 <tr> 數量
        def count_rows(section_name):
            m = re.search(rf"{section_name}.*?<tbody>(.*?)</tbody>", text, re.S)
            if not m:
                return 0
            return m.group(1).count("<tr>")
        return {
            "buy":  count_rows("新增雷達"),
            "sell": count_rows("賣出雷達"),
            "add":  count_rows("加碼雷達"),
            "cut":  count_rows("減碼雷達"),
        }
    except Exception:
        return {"buy": 0, "sell": 0, "add": 0, "cut": 0}


def inject(date_str: str, filename: str, counts: dict) -> bool:
    content = INDEX.read_text(encoding="utf-8")
    start = content.find("const ETF_REPORTS = [")
    end   = content.find("];", start) if start != -1 else -1
    if start == -1:
        print("[ERROR] 找不到 ETF_REPORTS 陣列")
        return False
    etf_section = content[start:end]
    if f'"date": "{date_str}"' in etf_section:
        print(f"[SKIP] {date_str} 已在 ETF_REPORTS 中，略過注入")
        return False
    new_entry = (
        f'\n  {{"date": "{date_str}", "file": "{filename}", '
        f'"buy": {counts["buy"]}, "sell": {counts["sell"]}, '
        f'"add": {counts["add"]}, "cut": {counts["cut"]}}},\n  {MARKER}'
    )
    content = content.replace(MARKER, new_entry, 1)
    INDEX.write_text(content, encoding="utf-8")
    return True


def main():
    args = sys.argv[1:]
    if "--date" not in args:
        print("[ERROR] 用法：python publish_etf.py --date YYYY-MM-DD")
        sys.exit(1)

    idx = args.index("--date")
    date_str = args[idx + 1]

    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"[ERROR] 日期格式應為 YYYY-MM-DD，收到：{date_str}")
        sys.exit(1)

    src = SRC_DIR / f"ETF監測報告_{date_str}.html"
    if not src.exists():
        print(f"[ERROR] 找不到 HTML：{src}")
        print("       請先執行 python main.py report")
        sys.exit(1)

    DEST_DIR.mkdir(exist_ok=True)
    date_compact = date_str.replace("-", "")
    filename = f"etf_{date_compact}.html"
    dest = DEST_DIR / filename
    shutil.copy2(src, dest)
    print(f"[OK] 複製：{filename}")

    counts = _count_radar(dest)
    injected = inject(date_str, filename, counts)
    if injected:
        print(f"[OK] index.html 已更新")

    run("git add -A")
    run(f'git commit -m "feat: 發布ETF追蹤日報 {date_str}"')
    run("git push")
    print(f"[OK] 已推送到 GitHub")
    print(f"     https://jasonfu1222.github.io/research/")
    print(f"直連日報：https://jasonfu1222.github.io/research/etf/{filename}")


if __name__ == "__main__":
    main()
