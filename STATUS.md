# STATUS
## 進行中
- [renketsu-sim] 本番モードを数値入力・大問×小問5問に作り直し中（標準想定45問／上級想定50問／ミニ15問）と、開示ドリル画面の追加
- [renketsu-sim] 完了：連結の総合問題（貸付金と利息、貸倒引当金の調整と税効果、子会社の資本剰余金、のれん償却年数ランダム）、公式用語での仕訳入力、公式形式（貸方は( )）の精算表表示
- [renketsu-sim] 完了：開示の大問（経営指標2種、連結CF、自己株式・配当・会計方針変更、純資産からのS/S・包括利益、XBRL）
- [renketsu-sim] 完了：公式模擬試験（上級）の問1〜7・問9・問10の数値をエンジンに入れ、公式解答と一致することをテストで確認（テスト33件すべて成功）
## 次にやること
- [renketsu-sim] GitHub にリポジトリ renketsu-sim を作って push し、Pages を GitHub Actions で公開する（本人作業。zip に手順あり）
- すずめとへびのプロダクト情報を有効にする（README の SQL を Supabase で実行し、Secret SUZUMEHEBI_SUPABASE_KEY を登録）
- 各リポジトリに STATUS.md を追加する（line-stock-bot, boki2-shogyo-notes, classic-concert, jpsi, sailfish-assets-）
- LINE 通知をドライランで確認する（Actions → dashboard → Run workflow → notify_dry_run にチェック）
## 確認待ちの判断
- main への push でもダッシュボードを再生成するようにした → 既定の行動: そのまま運用する（不要なら push トリガーを外す）
- [renketsu-sim] GitHub にリポジトリがまだ無いため、カードは「取得不可」になる → 既定の行動: リポジトリ作成までは進捗をこの STATUS.md に書き、作成後は renketsu-sim 側の STATUS.md に移す
