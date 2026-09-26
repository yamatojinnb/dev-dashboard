# dev-dashboard

個人開発プロジェクト横断の状態ダッシュボード。毎時（cron）と手動実行（workflow_dispatch）で GitHub Actions が
各リポジトリの状態を集め、パスワード保護された1枚の HTML として GitHub Pages に公開する。

公開URL: https://yamatojinnb.github.io/dev-dashboard/

## 構成

```
repos.yml                       監視対象リポジトリの一覧
scripts/collect.py               GitHub API から各リポジトリの状態を集めて build/data.json に保存
scripts/render.py                build/data.json から build/plain/index.html を生成
scripts/notify_line.py           直近65分以内のfailureがあればLINEにpush通知
.github/workflows/dashboard.yml  上記を実行し、StatiCryptで暗号化してGitHub Pagesへ公開
```

集めたデータ（build/ 以下）はコミットしない。ワークフロー内でのみ生成・破棄される。

## repos.yml への追加方法

`repos.yml` に以下の3行を1件追加するだけ。

```yaml
  - name: 表示名
    repo: owner/repo
    description: カードに表示する説明文
```

取得に失敗したリポジトリ（存在しない・権限がないなど）は「取得不可」と表示され、他のリポジトリの処理は止まらない。

## 集める情報

- 各ワークフローの最新実行（名前・結果・日時・URL）
- 未マージPR（タイトル・経過日数・URL）
- デフォルトブランチの最終コミット（日時・メッセージ1行目）
- ルートの `STATUS.md` の「## 進行中」「## 次にやること」「## 確認待ちの判断」（無ければ「STATUS.md なし」）

## バッジの色

- 赤: 失敗中のワークフローがある
- 黄: 確認待ちの判断がある、または7日以上放置された未マージPRがある
- 緑: 上記以外
- グレー（取得不可）: リポジトリ情報の取得に失敗

## パスワード保護

生成した `index.html` は [StatiCrypt](https://github.com/robinmoisson/staticrypt) v3（`npx`）で
`secrets.DASHBOARD_PASSWORD` を使って暗号化してから公開する。「このデバイスを記憶する」は30日間有効。
暗号化前の生HTMLはワークフロー内で削除し、成果物・ログには残さない。

## LINE通知

直近65分以内に完了した failure のワークフロー実行があれば、`LINE_ADMIN_USER_ID` 宛てに1通にまとめて push 通知する。
失敗が無ければ送信しない。`NOTIFY_DRY_RUN=1`（`workflow_dispatch` の `notify_dry_run` 入力から設定）のときは送信せず、
文面をログに出力するのみ。

## Secrets（リポジトリ設定）

| Secret | 内容 |
| --- | --- |
| `DASHBOARD_TOKEN` | GitHub API 読み取り用トークン。`gh auth token` の値。**`gh` からログアウトすると失効するため、失効した場合は `gh auth token \| gh secret set DASHBOARD_TOKEN -R yamatojinnb/dev-dashboard` を再実行すること** |
| `LINE_CHANNEL_ACCESS_TOKEN` | LINE Messaging API のチャネルアクセストークン |
| `LINE_ADMIN_USER_ID` | 通知を送るLINEユーザーID |
| `DASHBOARD_PASSWORD` | ダッシュボードの閲覧パスワード（StatiCryptで暗号化に使用） |

## 手動実行・動作確認

```
gh workflow run dashboard.yml -R yamatojinnb/dev-dashboard
gh run watch -R yamatojinnb/dev-dashboard
```

## プロダクト情報（Supabase の集計値）

repos.yml に `supabase_url` と `supabase_key_env` を書いたリポジトリは、カードに「プロダクト情報」を表示する。
キーは repos.yml に書かず、`supabase_key_env` で指定した名前の Secret に publishable key を登録する。

### すずめとへび（マリモ育成）の設定

1. Supabase の SQL Editor で次を1回実行する（件数と最新値だけを返す関数。写真そのものやコメントは返さない）

```sql
create or replace function public.dashboard_stats()
returns json
language sql
security definer
set search_path = public, storage
as $$
  select json_build_object(
    'photos_yamato', (select count(*) from storage.objects where bucket_id = 'photos' and name like 'yamato/%' and name not like '%.emptyFolderPlaceholder'),
    'photos_sakura', (select count(*) from storage.objects where bucket_id = 'photos' and name like 'sakura/%' and name not like '%.emptyFolderPlaceholder'),
    'photos_trash',  (select count(*) from storage.objects where bucket_id = 'photos' and name like 'trash/%'  and name not like '%.emptyFolderPlaceholder'),
    'marimo_size_mm',       (select size_mm from public.marimo where id = 1),
    'marimo_water_quality', (select water_quality from public.marimo where id = 1),
    'water_total',          (select count(*) from public.log where action = 'water'),
    'last_water_yamato',    (select max(local_date) from public.log where action = 'water' and actor = 'yamato'),
    'last_water_sakura',    (select max(local_date) from public.log where action = 'water' and actor = 'sakura')
  );
$$;
revoke all on function public.dashboard_stats() from public;
grant execute on function public.dashboard_stats() to anon;
```

2. dev-dashboard の Secret `SUZUMEHEBI_SUPABASE_KEY` に、Supabase の publishable key（Project Settings → API Keys）を登録する
3. 次回の更新（毎時、または main への push）で表示される
