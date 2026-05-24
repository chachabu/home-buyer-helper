#!/usr/bin/env python3
"""自动 git add + commit + push（买房助手）"""
import subprocess
import os
import sys

SKILL_DIR = os.path.dirname(os.path.abspath(__file__))

def git_push(msg="auto: 房源数据更新"):
    try:
        r = subprocess.run(["git", "add", "-A"], cwd=SKILL_DIR, capture_output=True, text=True, timeout=10)
        if r.returncode != 0:
            print(f"  ⚠️ git add 失败: {r.stderr[:200]}", file=sys.stderr)
            return False
        # 检查是否有变化
        r2 = subprocess.run(["git", "diff", "--cached", "--quiet"], cwd=SKILL_DIR)
        if r2.returncode == 0:
            return True  # 无变化，不算失败
        r3 = subprocess.run(["git", "commit", "-m", msg], cwd=SKILL_DIR, capture_output=True, text=True, timeout=10)
        if r3.returncode != 0:
            print(f"  ⚠️ git commit 失败: {r3.stderr[:200]}", file=sys.stderr)
            return False
        r4 = subprocess.run(["git", "push"], cwd=SKILL_DIR, capture_output=True, text=True, timeout=30)
        if r4.returncode != 0:
            print(f"  ⚠️ git push 失败: {r4.stderr[:200]}", file=sys.stderr)
            return False
        return True
    except Exception as e:
        print(f"  ⚠️ git 异常: {e}", file=sys.stderr)
        return False

if __name__ == "__main__":
    ok = git_push(sys.argv[1] if len(sys.argv) > 1 else "auto: data update")
    sys.exit(0 if ok else 1)
