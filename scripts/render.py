#!/usr/bin/env python3
"""build/data.json から index.html（暗号化前・生データ）を生成する"""
import html
import json
import os
from datetime import datetime, timedelta, timezone

JST = timezone(timedelta(hours=9))
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_FILE = os.path.join(ROOT, "build", "data.json")
OUT_FILE = os.path.join(ROOT, "build", "plain", "index.html")

STATUS_ORDER = {"red": 0, "unknown": 1, "yellow": 2, "green": 3}
STATUS_LABEL = {"red": "失敗あり", "unknown": "取得不可", "yellow": "要確認", "green": "正常"}


def esc(s):
    return html.escape(str(s), quote=True)


def workflow_label(run):
    if run["status"] != "completed":
        return "実行中"
    return {"success": "成功", "failure": "失敗"}.get(run["conclusion"], run["conclusion"] or "不明")


def repo_status(repo):
    if not repo.get("ok"):
        return "unknown"
    if any(r["conclusion"] == "failure" for r in repo.get("workflow_runs", [])):
        return "red"
    status_md = repo.get("status_md")
    pending = bool(status_md and status_md.get("確認待ちの判断"))
    stale_pr = any(pr["days_open"] >= 7 for pr in repo.get("open_prs", []))
    if pending or stale_pr:
        return "yellow"
    return "green"


def to_jst(iso_str):
    dt = datetime.fromisoformat(iso_str.replace("Z", "+00:00"))
    return dt.astimezone(JST).strftime("%Y-%m-%d %H:%M")


PRODUCT_LABELS = [
    ("photos_yamato", "写真（やまと）", "枚"),
    ("photos_sakura", "写真（さくら）", "枚"),
    ("photos_trash", "ゴミ箱の写真", "枚"),
    ("marimo_size_mm", "マリモの大きさ", "mm"),
    ("marimo_water_quality", "水質", ""),
    ("water_total", "水やり累計", "回"),
    ("last_water_yamato", "最終水やり（やまと）", ""),
    ("last_water_sakura", "最終水やり（さくら）", ""),
]


def render_product_stats(stats):
    if stats is None:
        return ""
    if "error" in stats:
        body = f"<p class='muted'>{esc(stats['error'])}</p>"
    else:
        lis = "".join(
            f"<li>{label}: <strong>{esc(stats[key])}</strong>{unit}</li>"
            for key, label, unit in PRODUCT_LABELS
            if stats.get(key) is not None
        )
        body = f"<ul>{lis}</ul>" if lis else "<p class='muted'>データなし</p>"
    return f"""
          <div class="block">
            <h3>プロダクト情報</h3>
            {body}
          </div>"""


def render_repo_card(repo):
    status = repo_status(repo)
    name = esc(repo["name"])
    repo_url = esc(repo["html_url"])
    desc = esc(repo.get("description", ""))

    if not repo.get("ok"):
        body = f'<p class="muted">取得不可（{esc(repo.get("error", ""))}）</p>'
        return f"""
        <section class="card status-{status}">
          <header class="card-head">
            <span class="badge badge-{status}">{STATUS_LABEL[status]}</span>
            <h2><a href="{repo_url}">{name}</a></h2>
          </header>
          <p class="desc">{desc}</p>
          {body}
          {render_product_stats(repo.get("product_stats"))}
        </section>"""

    wf_items = "".join(
        f'<li><a href="{esc(r["html_url"])}">{esc(r["name"])}</a> — '
        f'{workflow_label(r)}（{esc(to_jst(r["updated_at"]))}）</li>'
        for r in repo.get("workflow_runs", [])
    ) or "<li class='muted'>ワークフローなし</li>"

    pr_items = "".join(
        f'<li><a href="{esc(pr["html_url"])}">{esc(pr["title"])}</a> — {pr["days_open"]}日経過</li>'
        for pr in repo.get("open_prs", [])
    ) or "<li class='muted'>未マージPRなし</li>"

    commit = repo.get("last_commit")
    commit_html = (
        f'<a href="{esc(commit["html_url"])}">{esc(commit["message"])}</a>'
        f' （{esc(to_jst(commit["date"]))}）'
        if commit else "<span class='muted'>取得不可</span>"
    )

    status_md = repo.get("status_md")
    if status_md is None:
        status_html = "<p class='muted'>STATUS.md なし</p>"
    else:
        def section(title):
            items = status_md.get(title) or []
            if not items:
                return ""
            lis = "".join(f"<li>{esc(i)}</li>" for i in items)
            return f"<div class='status-section'><strong>{title}</strong><ul>{lis}</ul></div>"

        status_html = section("進行中") + section("次にやること") + section("確認待ちの判断")
        status_html = status_html or "<p class='muted'>記載なし</p>"

    return f"""
        <section class="card status-{status}">
          <header class="card-head">
            <span class="badge badge-{status}">{STATUS_LABEL[status]}</span>
            <h2><a href="{repo_url}">{name}</a></h2>
          </header>
          <p class="desc">{desc}</p>
          <div class="block">
            <h3>ワークフロー</h3>
            <ul>{wf_items}</ul>
          </div>
          <div class="block">
            <h3>未マージPR</h3>
            <ul>{pr_items}</ul>
          </div>
          <div class="block">
            <h3>最終コミット</h3>
            <p>{commit_html}</p>
          </div>
          <div class="block">
            <h3>STATUS.md</h3>
            {status_html}
          </div>
          {render_product_stats(repo.get("product_stats"))}
        </section>"""


def main():
    with open(DATA_FILE, encoding="utf-8") as f:
        data = json.load(f)

    repos = sorted(data["repos"], key=lambda r: STATUS_ORDER[repo_status(r)])

    failing_workflows = sum(
        1 for r in data["repos"] if r.get("ok")
        for run in r.get("workflow_runs", []) if run["conclusion"] == "failure"
    )
    open_prs = sum(len(r.get("open_prs", [])) for r in data["repos"] if r.get("ok"))
    pending_decisions = sum(
        len((r.get("status_md") or {}).get("確認待ちの判断", []))
        for r in data["repos"] if r.get("ok")
    )
    last_updated = to_jst(data["generated_at"])

    cards_html = "".join(render_repo_card(r) for r in repos)

    page = f"""<!doctype html>
<html lang="ja">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>dev-dashboard</title>
<style>
  :root {{
    --bg: #f5f6f8; --card-bg: #ffffff; --text: #1a1c20; --muted: #6b7280;
    --border: #e2e5e9; --red: #dc2626; --red-bg: #fde8e8;
    --yellow: #b45309; --yellow-bg: #fef3c7; --green: #15803d; --green-bg: #dcfce7;
    --gray: #4b5563; --gray-bg: #e5e7eb; --link: #2563eb;
  }}
  @media (prefers-color-scheme: dark) {{
    :root {{
      --bg: #14161a; --card-bg: #1e2126; --text: #e5e7eb; --muted: #9ca3af;
      --border: #2c3038; --red: #f87171; --red-bg: #3f1d1d;
      --yellow: #fbbf24; --yellow-bg: #3f2f0d; --green: #4ade80; --green-bg: #163a24;
      --gray: #9ca3af; --gray-bg: #2c3038; --link: #60a5fa;
    }}
  }}
  * {{ box-sizing: border-box; }}
  body {{
    margin: 0; padding: 16px; background: var(--bg); color: var(--text);
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", "Hiragino Sans", "Yu Gothic", sans-serif;
    line-height: 1.6;
  }}
  a {{ color: var(--link); }}
  .container {{ max-width: 720px; margin: 0 auto; }}
  h1 {{ font-size: 1.3rem; margin: 0 0 12px; }}
  .summary {{
    display: grid; grid-template-columns: repeat(2, 1fr); gap: 8px; margin-bottom: 20px;
  }}
  .summary .stat {{
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 10px;
    padding: 12px; text-align: center;
  }}
  .summary .stat .num {{ font-size: 1.6rem; font-weight: 700; }}
  .summary .stat .label {{ font-size: 0.8rem; color: var(--muted); }}
  .updated {{ font-size: 0.8rem; color: var(--muted); margin-bottom: 20px; text-align: right; }}
  .card {{
    background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px;
    padding: 16px; margin-bottom: 14px;
  }}
  .card-head {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
  .card-head h2 {{ font-size: 1.05rem; margin: 0; }}
  .desc {{ color: var(--muted); font-size: 0.85rem; margin: 6px 0 12px; }}
  .badge {{
    display: inline-block; font-size: 0.75rem; font-weight: 600; padding: 2px 8px;
    border-radius: 999px;
  }}
  .badge-red {{ color: var(--red); background: var(--red-bg); }}
  .badge-yellow {{ color: var(--yellow); background: var(--yellow-bg); }}
  .badge-green {{ color: var(--green); background: var(--green-bg); }}
  .badge-unknown {{ color: var(--gray); background: var(--gray-bg); }}
  .block {{ margin-top: 10px; }}
  .block h3 {{ font-size: 0.85rem; margin: 0 0 4px; color: var(--muted); }}
  .block ul {{ margin: 0; padding-left: 1.2em; font-size: 0.9rem; }}
  .muted {{ color: var(--muted); }}
  .status-section {{ margin-bottom: 6px; font-size: 0.9rem; }}
  footer {{ text-align: center; color: var(--muted); font-size: 0.75rem; margin: 24px 0 8px; }}
</style>
</head>
<body>
  <div class="container">
    <h1>dev-dashboard</h1>
    <div class="summary">
      <div class="stat"><div class="num">{failing_workflows}</div><div class="label">失敗中ワークフロー</div></div>
      <div class="stat"><div class="num">{open_prs}</div><div class="label">未マージPR</div></div>
      <div class="stat"><div class="num">{pending_decisions}</div><div class="label">確認待ちの判断</div></div>
      <div class="stat"><div class="num">{len(repos)}</div><div class="label">監視対象</div></div>
    </div>
    <div class="updated">最終更新: {last_updated} (JST)</div>
    {cards_html}
    <footer>generated by dev-dashboard</footer>
  </div>
</body>
</html>
"""
    os.makedirs(os.path.dirname(OUT_FILE), exist_ok=True)
    with open(OUT_FILE, "w", encoding="utf-8") as f:
        f.write(page)
    print(f"rendered -> {OUT_FILE}")


if __name__ == "__main__":
    main()
