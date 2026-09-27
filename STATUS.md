# STATUS
## 進行中
- [renketsu-sim] 公式模擬試験（上級）との照合で見つかった不足を改修中：本番モードを数値入力・大問×小問5問に作り直す
- [renketsu-sim] 開示の大問を追加中：経営指標・表示ルール、連結キャッシュ・フロー計算書、株主資本等変動計算書（自己株式・配当・会計方針変更）、包括利益（持分法OCI・子会社増資）、XBRL
- [renketsu-sim] 連結の論点を模試に近づける：貸付金と利息、貸倒引当金の調整と税効果、子会社の資本剰余金、のれん償却年数のランダム化、公式用語での仕訳入力
## 次にやること
- [renketsu-sim] GitHub にリポジトリ renketsu-sim を作って push し、Pages を GitHub Actions で公開する（本人作業。zip に手順あり）
- すずめとへびのプロダクト情報を有効にする（README の SQL を Supabase で実行し、Secret SUZUMEHEBI_SUPABASE_KEY を登録）
- 各リポジトリに STATUS.md を追加する（line-stock-bot, boki2-shogyo-notes, classic-concert, jpsi, sailfish-assets-）
- LINE 通知をドライランで確認する（Actions → dashboard → Run workflow → notify_dry_run にチェック）
## 確認待ちの判断
- main への push でもダッシュボードを再生成するようにした → 既定の行動: そのまま運用する（不要なら push トリガーを外す）
- [renketsu-sim] GitHub にリポジトリがまだ無いため、カードは「取得不可」になる → 既定の行動: リポジトリ作成までは進捗をこの STATUS.md に書き、作成後は renketsu-sim 側の STATUS.md に移す
