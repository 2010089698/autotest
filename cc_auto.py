#!/usr/bin/env python3
"""
cc_auto.py — Claude Code SDK launcher for
plan / red / green stages in the fully-auto workflow
"""

import anyio
import sys
import pathlib
import textwrap
from claude_code_sdk import query, ClaudeCodeOptions

ROOT = pathlib.Path(__file__).parent.resolve()

# ──────────────────────────────────────────────────────────
# helper: send a prompt to Claude Code with optional git perms
# ──────────────────────────────────────────────────────────
async def ask_ai(prompt: str, *git_tools: str) -> None:
    opts = ClaudeCodeOptions(
        cwd=ROOT,
        max_turns=3,
        allowed_tools=["Read", "Write", "Bash", *git_tools],
        permission_mode="acceptEdits",
    )
    async for _ in query(prompt=prompt, options=opts):
        pass  # files are written by Claude Code itself


# ──────────────────────────────────────────────────────────
# main entry
# ──────────────────────────────────────────────────────────
async def main() -> None:
    if len(sys.argv) < 2:
        print("usage: python cc_auto.py [plan|red|green] [--msg 'text'] [--logs path]")
        return

    stage = sys.argv[1]

    if stage == "plan":
        # collect request text after --msg
        try:
            msg_index = sys.argv.index("--msg")
            request = " ".join(sys.argv[msg_index + 1 :])
        except ValueError:
            request = "（要望が指定されていません）"

        prompt = textwrap.dedent(
            f"""
            あなたは t_wada メソッドで開発する AI プランナーです。

            ## ユーザー要望
            {request}

            ### やること
            1. 要望を 3〜7 個の小さな TODO（`- [ ] ...`）に分割して TEST_LIST.md に追記
            2. git add TEST_LIST.md → git commit -m "plan: {request[:30]}…" → git push
            """
        )
        await ask_ai(prompt, "Bash(git add*)", "Bash(git commit*)", "Bash(git push*)")

    elif stage == "red":
        prompt = textwrap.dedent(
            """
            TEST_LIST.md の最初の未完了 TODO を選び、
            わざと失敗する pytest テストを 1 本だけ追加し push してください。
            コミットメッセージ: "red: create failing test"
            """
        )
        await ask_ai(prompt, "Bash(git add*)", "Bash(git commit*)", "Bash(git push*)")

    elif stage == "green":
        # --logs <path> で失敗ログを受け取る
        try:
            logs_index = sys.argv.index("--logs")
            logs_path = pathlib.Path(sys.argv[logs_index + 1])
            logs = logs_path.read_text()
        except (ValueError, IndexError, FileNotFoundError):
            print("Error: --logs <path> が指定されていないか、ファイルが読めません")
            return

        prompt = textwrap.dedent(
            f"""
            次の失敗ログを最小限の実装で通過させ、その後安全にリファクタを行って push してください。
            ```
            {logs}
            ```
            コミットメッセージ: "green: make tests pass"
            """
        )
        await ask_ai(prompt, "Bash(git add*)", "Bash(git commit*)", "Bash(git push*)")

    else:
        print(f"unknown stage: {stage}")
        print("usage: python cc_auto.py [plan|red|green] ..." )


# ──────────────────────────────────────────────────────────
# run
# ──────────────────────────────────────────────────────────
if __name__ == "__main__":
    anyio.run(main)  # ← ここは呼び出しではなく関数を渡す
