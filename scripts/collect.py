#!/usr/bin/env python3
"""repos.yml に列挙された各リポジトリの状態をGitHub APIから集めて build/data.json に保存する"""
import base64
import json
import os
import re
from datetime import datetime, timezone

import requests

API_BASE = "https://api.github.com"
# Windows の PowerShell からパイプで登録すると先頭に BOM(\ufeff) や改行が付くことがあるため取り除く
TOKEN = os.environ["DASHBOARD_TOKEN"].strip().lstrip("\ufeff").strip()
HEADERS = {
    "Authorization": f"Bearer {TOKEN}",
    "Accept": "application/vnd.github+json",
    "X-GitHub-Api-Version": "2022-11-28",
    "User-Agent": "dev-dashboard",
}
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT, "build", "data.json")


def parse_repos_yml(path):
    """name/repo/description の3キーだけの単純なリストを想定した最小限のYAMLパーサー"""
    repos = []
    current = None
    with open(path, encoding="utf-8") as f:
        for raw in f:
            line = raw.rstrip("\n")
            if not line.strip() or line.strip().startswith("#"):
                continue
            m = re.match(r"^\s*-\s*name:\s*(.+)$", line)
            if m:
                if current:
                    repos.append(current)
                current = {"name": m.group(1).strip(), "repo": "", "description": ""}
                continue
            m = re.match(r"^\s*repo:\s*(.+)$", line)
            if m and current is not None:
                current["repo"] = m.group(1).strip()
                continue
            m = re.match(r"^\s*description:\s*(.*)$", line)
            if m and current is not None:
                current["description"] = m.group(1).strip()
                continue
            m = re.match(r"^\s*([a-z_]+):\s*(.*)$", line)
            if m and current is not None:
                current[m.group(1)] = m.group(2).strip()
    if current:
        repos.append(current)
    return repos


def api_get(path, params=None):
    resp = requests.get(f"{API_BASE}{path}", headers=HEADERS, params=params, timeout=15)
    resp.raise_for_status()
    return resp.json()


def days_since(iso_str):
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return (datetime.now(timezone.utc) - dt).days


def collect_workflow_runs(owner, repo):
    """ワークフローごとの最新実行を1件ずつ集める"""
    data = api_get(f"/repos/{owner}/{repo}/actions/runs", {"per_page": 50})
    latest = {}
    for run in data.get("workflow_runs", []):
        name = run["name"]
        if name not in latest:
            latest[name] = {
                "name": name,
                "status": run["status"],
                "conclusion": run["conclusion"],
                "updated_at": run["updated_at"],
                "html_url": run["html_url"],
            }
    return list(latest.values())


def collect_open_prs(owner, repo):
    prs = api_get(f"/repos/{owner}/{repo}/pulls", {"state": "open", "per_page": 50})
    return [
        {
            "title": pr["title"],
            "days_open": days_since(pr["created_at"]),
            "html_url": pr["html_url"],
        }
        for pr in prs
    ]


def collect_last_commit(owner, repo, default_branch):
    commit = api_get(f"/repos/{owner}/{repo}/commits/{default_branch}")
    return {
        "message": commit["commit"]["message"].split("\n")[0],
        "date": commit["commit"]["committer"]["date"],
        "html_url": commit["html_url"],
    }


def collect_status_md(owner, repo):
    resp = requests.get(
        f"{API_BASE}/repos/{owner}/{repo}/contents/STATUS.md", headers=HEADERS, timeout=15
    )
    if resp.status_code == 404:
        return None
    resp.raise_for_status()
    content = base64.b64decode(resp.json()["content"]).decode("utf-8")

    sections = {"進行中": [], "次にやること": [], "確認待ちの判断": []}
    current = None
    for line in content.splitlines():
        stripped = line.strip()
        m = re.match(r"^##\s*(進行中|次にやること|確認待ちの判断)\s*$", stripped)
        if m:
            current = m.group(1)
            continue
        if current and stripped.startswith(("-", "*")):
            sections[current].append(stripped.lstrip("-*").strip())
    return sections


def collect_product_stats(entry):
    """repos.yml に supabase_url / supabase_key_env があれば、Supabase の dashboard_stats() を呼んで集計値を取る。
    キーは repos.yml には書かず、supabase_key_env で指定した名前の環境変数（Actions の Secret）から読む。"""
    url = entry.get("supabase_url")
    key_env = entry.get("supabase_key_env")
    if not url or not key_env:
        return None
    key = os.environ.get(key_env, "").strip().lstrip("\ufeff").strip()
    if not key:
        return {"error": f"未設定（Secret {key_env} を登録すると表示されます）"}
    try:
        resp = requests.post(
            f"{url.rstrip('/')}/rest/v1/rpc/dashboard_stats",
            headers={"apikey": key, "Content-Type": "application/json"},
            json={},
            timeout=15,
        )
        if resp.status_code == 404:
            return {"error": "dashboard_stats() が未作成です（README の手順でSQLを実行）"}
        resp.raise_for_status()
        return resp.json()
    except Exception as e:
        return {"error": f"取得失敗（{type(e).__name__}）"}


def collect_repo(entry):
    owner, repo = entry["repo"].split("/", 1)
    result = {
        "name": entry["name"],
        "repo": entry["repo"],
        "description": entry["description"],
        "html_url": f"https://github.com/{entry['repo']}",
        "ok": True,
    }
    try:
        repo_info = api_get(f"/repos/{owner}/{repo}")
        result["workflow_runs"] = collect_workflow_runs(owner, repo)
        result["open_prs"] = collect_open_prs(owner, repo)
        result["last_commit"] = collect_last_commit(owner, repo, repo_info["default_branch"])
        result["status_md"] = collect_status_md(owner, repo)
    except Exception as e:
        result["ok"] = False
        result["error"] = str(e)
    result["product_stats"] = collect_product_stats(entry)
    return result


def main():
    entries = parse_repos_yml(os.path.join(ROOT, "repos.yml"))
    repos_data = [collect_repo(entry) for entry in entries]
    os.makedirs(os.path.dirname(DATA_FILE), exist_ok=True)
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"generated_at": datetime.now(timezone.utc).isoformat(), "repos": repos_data},
            f,
            ensure_ascii=False,
            indent=2,
        )
    print(f"collected {len(repos_data)} repos -> {DATA_FILE}")


if __name__ == "__main__":
    main()
