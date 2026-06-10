"""
publish_us_tools.py — 合併美股四工具 HTML 日報並推送到 GitHub Pages

用法：
  python publish_us_tools.py --date YYYY-MM-DD

來源（美股研究工具系統\output\）：
  form4_YYYYMMDD.html
  sector_YYYYMMDD.html
  radar_YYYYMMDD.html
  13dg_YYYYMMDD.html
  13f_YYYYMMDD.html  （若存在則納入）

目標：
  research-site/us-tools/us_tools_YYYYMMDD.html
  research-site/index.html（US_TOOLS_REPORTS 陣列自動注入）
"""

import sys
import re
import shutil
import subprocess
from pathlib import Path
from datetime import datetime

TOOLS_OUTPUT = Path(r"C:\Users\USER\Claude\Projects\美股研究工具系統\output")
HUB_DIR      = Path(__file__).parent
INDEX        = HUB_DIR / "index.html"
DEST_DIR     = HUB_DIR / "us-tools"
MARKER       = "// ← publish_us_tools.py 會自動在這裡插入新紀錄"

SECTIONS = [
    ("form4",  "A — Form 4 內部人交易"),
    ("sector", "C — 板塊 ETF 資金流向"),
    ("radar",  "D — 美股趨勢雷達"),
    ("13dg",   "E — 13D/13G 機構申報"),
    ("13f",    "G — 13F 狼群偵測（季報快照）"),
]


def run(cmd: str):
    result = subprocess.run(
        cmd, shell=True, cwd=HUB_DIR,
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        print(f"[ERROR] {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def extract_parts(html_path: Path):
    """Returns (styles_without_body_rule, body_content)"""
    text = html_path.read_text(encoding="utf-8", errors="replace")
    styles = re.findall(r"<style[^>]*>(.*?)</style>", text, re.S)
    combined = "\n".join(styles)
    # Remove body { ... } rules — combined page has its own body style
    combined = re.sub(r"\bbody\s*\{[^}]*\}", "", combined)
    m = re.search(r"<body[^>]*>(.*?)</body>", text, re.S)
    body = m.group(1).strip() if m else '<p style="color:#8b949e">（資料不可用）</p>'
    return combined, body


def build_combined_html(date_str: str, compact: str) -> str:
    """Build the combined HTML from individual tool files."""
    sections_html = []
    all_styles = []
    nav_links = []
    have_sections = []

    for key, label in SECTIONS:
        src = TOOLS_OUTPUT / f"{key}_{compact}.html"
        if not src.exists():
            # 13f fallback: find most recent 13f HTML
            if key == "13f":
                candidates = sorted(TOOLS_OUTPUT.glob("13f_*.html"), reverse=True)
                if candidates:
                    src = candidates[0]
                    label += f"（{candidates[0].stem.split('_')[1][:4]}-{candidates[0].stem.split('_')[1][4:6]}-{candidates[0].stem.split('_')[1][6:]}）"
                else:
                    continue  # skip 13f entirely if no file found
            else:
                body = f'<p style="padding:20px;color:#8b949e">今日 {label} 資料尚未生成</p>'
                style = ""
        if src.exists():
            style, body = extract_parts(src)

        anchor = f"ust-{key.replace('/', '-')}"
        nav_links.append(f'<a href="#{anchor}">{label.split("—")[1].strip() if "—" in label else label}</a>')
        all_styles.append(style)
        sections_html.append(f"""
<div id="{anchor}">
  <div class="ust-section-header">{label}</div>
  <div class="ust-content">{body}</div>
</div>
<div class="ust-sep"></div>""")
        have_sections.append(key)

    nav_html = "\n  ".join(nav_links)
    styles_html = "\n".join(all_styles)
    body_html = "\n".join(sections_html)

    return f"""<!DOCTYPE html>
<html lang="zh-TW">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>美股工具日報 {compact}</title>
<style>
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: #0d1117; color: #e6edf3; font-family: "Microsoft JhengHei", "PingFang TC", sans-serif; }}
.ust-topbar {{ background: #0d1117; border-bottom: 1px solid #21262d; padding: 12px 20px 10px; }}
.ust-topbar h1 {{ font-size: 16px; font-weight: 800; color: #e6edf3; display: inline; }}
.ust-topbar span {{ font-size: 12px; color: #8b949e; margin-left: 12px; }}
.ust-nav {{ display: flex; gap: 0; background: #161b22; border-bottom: 1px solid #30363d; padding: 0 20px; position: sticky; top: 0; z-index: 100; overflow-x: auto; }}
.ust-nav a {{ color: #8b949e; font-size: 12px; font-weight: 600; padding: 10px 16px; text-decoration: none; border-bottom: 2px solid transparent; white-space: nowrap; transition: all 0.15s; }}
.ust-nav a:hover {{ color: #e6edf3; }}
.ust-section-header {{ background: #1e3a5f; color: #79c0ff; font-size: 11px; font-weight: 700; letter-spacing: 2px; text-transform: uppercase; padding: 10px 20px; border-bottom: 1px solid #30363d; }}
.ust-content {{ padding: 0; }}
.ust-sep {{ height: 6px; background: #161b22; border-top: 1px solid #21262d; border-bottom: 1px solid #21262d; }}
{styles_html}
</style>
</head>
<body>
<div class="ust-topbar">
  <h1>美股工具日報</h1>
  <span>{date_str}</span>
</div>
<nav class="ust-nav">
  {nav_html}
</nav>
{body_html}
</body>
</html>"""


def inject(date_str: str, filename: str) -> bool:
    content = INDEX.read_text(encoding="utf-8")
    start = content.find("const US_TOOLS_REPORTS = [")
    end   = content.find("];", start) if start != -1 else -1
    if start == -1:
        print("[WARN] 找不到 US_TOOLS_REPORTS 陣列，略過注入")
        return False
    section = content[start:end]
    if f'"date": "{date_str}"' in section:
        print(f"[SKIP] {date_str} 已在 US_TOOLS_REPORTS 中")
        return False
    new_entry = f'\n  {{"date": "{date_str}", "file": "{filename}"}},\n  {MARKER}'
    content = content.replace(MARKER, new_entry, 1)
    INDEX.write_text(content, encoding="utf-8")
    return True


def main():
    args = sys.argv[1:]
    if "--date" not in args:
        print("[ERROR] 用法：python publish_us_tools.py --date YYYY-MM-DD")
        sys.exit(1)
    idx = args.index("--date")
    date_str = args[idx + 1]
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        print(f"[ERROR] 日期格式應為 YYYY-MM-DD，收到：{date_str}")
        sys.exit(1)

    compact = date_str.replace("-", "")
    DEST_DIR.mkdir(exist_ok=True)
    filename = f"us_tools_{compact}.html"
    dest = DEST_DIR / filename

    html = build_combined_html(date_str, compact)
    dest.write_text(html, encoding="utf-8")
    print(f"[OK] 生成：{filename}")

    injected = inject(date_str, filename)
    if injected:
        print(f"[OK] index.html 已更新")

    run("git add -A")
    run(f'git commit -m "feat: 美股工具日報 {date_str}"')
    run("git push")
    print(f"[OK] 已推送到 GitHub")
    print(f"直連：https://jasonfu1222.github.io/research/us-tools/{filename}")


if __name__ == "__main__":
    main()
