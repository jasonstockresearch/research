r"""
publish_us_trackers.py — 發布美股工具「近N日累積追蹤」常駐頁到 GitHub Pages

與 publish_us_tools.py 的差異：追蹤頁是**單一常駐頁**（每天覆蓋更新，非每日一份），
研究站三個 tab（Form4追蹤/板塊資金流/趨勢雷達）以 iframe 常駐嵌入固定檔名，故本腳本
只需複製 + push，不需注入 index.html 陣列（tab 已固定）。

前置：美股研究工具系統\trackers.py all 已產出 output\*_track.html（update_today 會先跑）。
用法：python publish_us_trackers.py
"""
import shutil
import subprocess
import sys
from pathlib import Path

TOOLS_OUTPUT = Path(r"C:\Users\USER\Claude\Projects\美股研究工具系統\output")
HUB_DIR = Path(__file__).parent
DEST_DIR = HUB_DIR / "us-tools"
FILES = ["form4_track.html", "sector_track.html", "radar_track.html"]


def run(cmd, allow_fail=False):
    r = subprocess.run(cmd, shell=True, cwd=HUB_DIR, capture_output=True,
                       text=True, encoding="utf-8")
    if r.returncode != 0 and not allow_fail:
        print(f"[ERROR] {cmd}\n{r.stderr.strip()}")
        sys.exit(1)
    return r


def main():
    DEST_DIR.mkdir(exist_ok=True)
    copied = 0
    for name in FILES:
        src = TOOLS_OUTPUT / name
        if not src.exists():
            print(f"[WARN] 來源不存在，略過：{name}（trackers.py 是否跑過？）")
            continue
        shutil.copy2(src, DEST_DIR / name)
        copied += 1
        print(f"[OK] 複製 {name}")
    if copied == 0:
        print("[ERROR] 無任何追蹤頁可發布")
        sys.exit(1)

    run("git add -A")
    commit = run('git commit -m "chore: 更新美股工具追蹤頁"', allow_fail=True)
    if "nothing to commit" in (commit.stdout + commit.stderr):
        print("[SKIP] 內容無變化，不推送")
        return
    run("git push")
    print(f"[OK] 已推送 {copied} 個追蹤頁")
    print("直連：https://jasonstockresearch.github.io/research/us-tools/form4_track.html")


if __name__ == "__main__":
    main()
