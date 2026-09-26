#!/usr/bin/env python3
"""直近65分以内に完了したfailureのワークフロー実行があればLINEに1通まとめて通知する"""
import json
import os
from datetime import datetime, timedelta, timezone

import requests

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT, "build", "data.json")
WINDOW_MINUTES = 65
LINE_PUSH_URL = "https://api.line.me/v2/bot/message/push"


def recent_failures(data):
    now = datetime.now(timezone.utc)
    threshold = now - timedelta(minutes=WINDOW_MINUTES)
    failures = []
    for repo in data["repos"]:
        if not repo.get("ok"):
            continue
        for run in repo.get("workflow_runs", []):
            if run["conclusion"] != "failure":
                continue
            updated_at = datetime.fromisoformat(run["updated_at"].replace("Z", "+00:00"))
            if updated_at >= threshold:
                failures.append(
                    {"repo": repo["name"], "workflow": run["name"], "url": run["html_url"]}
                )
    return failures


def build_message(failures):
    lines = [f"⚠ Actions失敗 {len(failures)}件"]
    for f in failures:
        lines.append(f"・{f['repo']} / {f['workflow']}\n{f['url']}")
    return "\n".join(lines)


def send_line_push(message):
    token = os.environ["LINE_CHANNEL_ACCESS_TOKEN"]
    to = os.environ["LINE_ADMIN_USER_ID"]
    resp = requests.post(
        LINE_PUSH_URL,
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={"to": to, "messages": [{"type": "text", "text": message}]},
        timeout=15,
    )
    resp.raise_for_status()


def main():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    failures = recent_failures(data)
    if not failures:
        print("直近65分以内の失敗なし。通知しません。")
        return

    message = build_message(failures)
    if os.environ.get("NOTIFY_DRY_RUN") == "1":
        print("[DRY RUN] 送信予定の文面:")
        print(message)
        return

    send_line_push(message)
    print(f"LINE通知を送信しました（{len(failures)}件）")


if __name__ == "__main__":
    main()
