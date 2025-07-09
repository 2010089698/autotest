import anyio, sys, pathlib, textwrap
from claude_code_sdk import query, ClaudeCodeOptions

ROOT = pathlib.Path(__file__).parent

async def ask_ai(prompt: str, *git_tools):
    opts = ClaudeCodeOptions(
        cwd=ROOT,
        max_turns=3,
        allowed_tools=["Read", "Write", "Bash"] + list(git_tools),
        permission_mode="acceptEdits",
    )
    async for _ in query(prompt=prompt, options=opts):
        pass  # AI がファイル編集・git 実行を済ませる

async def main():
    stage = sys.argv[1]               # plan / red / green
    request = " ".join(sys.argv[3:])  # plan 用の要望文

    if stage == "plan":
        prompt = textwrap.dedent(f"""
        あなたは t_wada 開発法で動く AI プランナーです。

        ## ユーザー要望
        {request}

        ### やること
        1. 要望を 3〜7 個の小さな TODO（チェックボックス記法）に分割し TEST_LIST.md に追記
        2. `git add TEST_LIST.md` → `git commit -m "plan: {request[:30]}..."` → `git push`
        """)
        await ask_ai(prompt, "Bash(git add*)", "Bash(git commit*)", "Bash(git push*)")

    elif stage == "red":
        prompt = """
        TEST_LIST.md の最初の未完了 TODO を選び、
        *必ず失敗する* pytest テストを 1 本だけ追加し push してください。
        コミットメッセージ: "red: create failing test"
        """
        await ask_ai(prompt, "Bash(git add*)", "Bash(git commit*)", "Bash(git push*)")

    elif stage == "green":
        logs = pathlib.Path("logs.txt").read_text()
        prompt = f"""
        次の失敗ログを最小限の実装で通過させ、その後安全にリファクタを行って push してください。
        ```
        {logs}
        ```
        コミットメッセージ: "green: make tests pass"
        """
        await ask_ai(prompt, "Bash(git add*)", "Bash(git commit*)", "Bash(git push*)")

anyio.run(main())
