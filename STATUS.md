# STATUS
## 進行中
- [renketsu-sim] 公式模擬試験に合わせた改修は完了。プレビュー（Artifact）と zip を更新済み。本人の確認待ち
## 次にやること
- [renketsu-sim] GitHub にリポジトリ renketsu-sim を作って push し、Pages を GitHub Actions で公開する（本人作業。zip の README に手順あり）。push 後は renketsu-sim 側の STATUS.md がこのカードに表示される
- [renketsu-sim] 模擬試験の問8型（有報の文章の穴埋め、利息・配当の表示区分）を追加する
- すずめとへびのプロダクト情報を有効にする（README の SQL を Supabase で実行し、Secret SUZUMEHEBI_SUPABASE_KEY を登録）
- 各リポジトリに STATUS.md を追加する（line-stock-bot, boki2-shogyo-notes, classic-concert, jpsi, sailfish-assets-）
- LINE 通知をドライランで確認する（Actions → dashboard → Run workflow → notify_dry_run にチェック）
## 確認待ちの判断
- main への push でもダッシュボードを再生成するようにした → 既定の行動: そのまま運用する（不要なら push トリガーを外す）
- [renketsu-sim] GitHub にリポジトリがまだ無いため、カードは「取得不可」になる → 既定の行動: リポジトリ作成までは進捗をこの STATUS.md に書き、作成後は renketsu-sim 側の STATUS.md に移す
- [renketsu-sim] 標準レベル想定の本番セット（連結会計6大問＋連結開示3大問）は受験要項からの推測 → 既定の行動: このまま運用し、公式情報が見つかれば合わせる
