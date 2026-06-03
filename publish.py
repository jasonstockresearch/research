"""
publish.py — 一鍵發布新研究報告到 GitHub Pages（含自動更新首頁目錄）

用法：
  python publish.py <HTML檔路徑>
    [--slug   自訂網址名稱]
    [--title  報告標題]
    [--desc   一句摘要]
    [--type   sector|company|macro|strategy]
    [--icon   emoji圖示]
    [--tags   "tag1,tag2"]

範例（Claude 呼叫時帶完整參數，使用者完全不需手動改任何檔案）：
  python publish.py report.html \
    --slug 20260601-broadcom-deep-dive \
    --title "Broadcom 深度研究：Custom ASIC 護城河分析" \
    --desc "Broadcom AVGO 的三大業務支柱..." \
    --type company \
    --icon 📡 \
    --tags "美股,半導體,AVGO"
"""

import sys, shutil, subprocess, re
from pathlib import Path
from datetime import date

HUB_DIR = Path(r"C:\Users\USER\Claude\Projects\研究報告站_research-site")
INDEX_HTML = HUB_DIR / "index.html"

ICONS = {
    "sector": "🏭", "company": "🏢", "macro": "🌐", "strategy": "🎯",
}


def run(cmd, cwd=None):
    result = subprocess.run(
        cmd, shell=True, cwd=cwd or HUB_DIR,
        capture_output=True, text=True, encoding="utf-8",
    )
    if result.returncode != 0:
        print(f"[ERROR] {result.stderr.strip()}")
        sys.exit(1)
    return result.stdout.strip()


def slugify(text):
    text = re.sub(r"[^\w]", "-", text)
    text = re.sub(r"-+", "-", text).strip("-")
    return text[:60].lower()


def inject_into_index(entry: dict) -> bool:
    """在 index.html 的 REPORTS 陣列最前面插入新報告。"""
    content = INDEX_HTML.read_text(encoding="utf-8")
    marker = "const REPORTS = ["
    pos = content.find(marker)
    if pos == -1:
        return False

    tags_js = ", ".join(f'"{t}"' for t in entry["tags"])
    new_entry = (
        f'\n  {{\n'
        f'    date: "{entry["date"]}",\n'
        f'    type: "{entry["type"]}",\n'
        f'    icon: "{entry["icon"]}",\n'
        f'    title: "{entry["title"]}",\n'
        f'    desc:  "{entry["desc"]}",\n'
        f'    file:  "{entry["file"]}",\n'
        f'    tags:  [{tags_js}],\n'
        f'  }},'
    )

    insert_at = pos + len(marker)
    content = content[:insert_at] + new_entry + content[insert_at:]
    INDEX_HTML.write_text(content, encoding="utf-8")
    return True


def parse_args(args):
    kw = {}
    i = 0
    positional = []
    while i < len(args):
        if args[i].startswith("--") and i + 1 < len(args):
            kw[args[i][2:]] = args[i + 1]
            i += 2
        else:
            positional.append(args[i])
            i += 1
    return positional, kw


def main():
    raw = sys.argv[1:]
    if not raw:
        print(__doc__)
        sys.exit(0)

    positional, kw = parse_args(raw)

    if not positional:
        print("[ERROR] 請提供 HTML 檔路徑")
        sys.exit(1)

    src = Path(positional[0])
    if not src.exists():
        print(f"[ERROR] 找不到檔案：{src}")
        sys.exit(1)

    today = date.today()
    rtype = kw.get("type", "sector")
    slug  = kw.get("slug") or f"{today.strftime('%Y%m%d')}-{slugify(src.stem)}"
    title = kw.get("title", src.stem)
    desc  = kw.get("desc", "")
    icon  = kw.get("icon", ICONS.get(rtype, "📄"))
    tags  = [t.strip() for t in kw.get("tags", "").split(",") if t.strip()]

    dest_name = f"{slug}.html"
    dest = HUB_DIR / dest_name

    # 1. 複製報告（src == dst 時跳過，檔案已在正確位置）
    if src.resolve() != dest.resolve():
        shutil.copy2(src, dest)
        print(f"[OK] 複製完成：{dest_name}")
    else:
        print(f"[OK] 檔案已在目標位置：{dest_name}")

    # 2. 自動寫入 index.html
    entry = dict(date=today.isoformat(), type=rtype, icon=icon,
                 title=title, desc=desc, file=dest_name, tags=tags)
    if inject_into_index(entry):
        print(f"[OK] 首頁目錄已自動更新")
    else:
        print("[WARN] 無法自動更新 index.html，請手動在 REPORTS 陣列新增：")
        print(f'  {{ date:"{today}", type:"{rtype}", icon:"{icon}", title:"{title}", desc:"{desc}", file:"{dest_name}", tags:[{", ".join(repr(t) for t in tags)}] }},')

    # 3. git commit & push（報告 + index.html 一起）
    run("git add -A")
    run(f'git commit -m "feat: 發布報告 {title[:40]}"')
    run("git push")
    print(f"[OK] 已 push 到 GitHub")
    print()
    print(f"報告網址（約 1 分鐘後生效）：")
    print(f"  https://jasonstockresearch.github.io/research/{dest_name}")
    print(f"首頁：https://jasonstockresearch.github.io/research/")


if __name__ == "__main__":
    main()
