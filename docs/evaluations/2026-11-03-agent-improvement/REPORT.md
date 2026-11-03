# Bonsai Agent改善報告：API預算與改檔指引

2026-11-03，RTX3080 12GB。這份報告只比較本輪修正；[上一輪完整Benchmark](../2026-11-03/REPORT.md)另存，歷史與新樣本沒有混算。

**目前採用：144K／Graph OFF／draft3＋通用改檔指引。** 本輪9/9通過；含失敗成本約160秒／成功件，歷史控制為8/9、154秒。完成件數較好，尚未證明整體任務速度提升。Windows指引7/9與Draft5的8/9均不作日常預設。

## 已確定的修正

- 相同OpenAI請求要求16 token並關思考：修正前實際2048 token、10.969秒；修正後16 token、0.422秒。這是預算被尊重，不是Decode吞吐變快。
- 實機API檢查：通過，14個案例。支援max_completion_tokens別名、顯式關思考、合法思考預算；不合法或衝突額度回400。
- 輸出預設16384、上限32768；一般大額度的1536思考預算保留。原生引擎啟用思考至少1024，校驗額外預留256答案token；不足就清楚拒絕，不偷加額度。
- 一般截斷保留length；截斷工具批次／無效JSON不放行並回502。空白且用完額度不再當循環重試。既有重複工具糾正、權限及max_tool_calls=null保留。
- 新增Claude Code追加指引：Edit／Write優先、避免巢狀Bash改檔、錯誤後改變做法、逐項核對需求及測試。只改指引，沒有放寬工具權限；不保證模型遵守。

## Coding：先看完成率與總時間

Bug／功能／八模組重構各三次；同起始檔、同使用者任務Prompt、同外部驗收。新版多了固定system指引與橋接安全修正，因此只比較整體配方，不把差異歸因於單一改動。Claude走Anthropic路徑，原本就能尊重小輸出額度；OpenAI小預算修正不能直接解釋Claude任務耗時。

| 組別 | 實測次數 | 未測試 | 完成 | 含驗收總秒 | 含失敗秒/成功件 | 工具呼叫合計 | 工具錯誤合計 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 舊版144K | 9 | 0 | 8/9 | 1235.63 | 154.45 | 321 | 88 |
| 通用指引144K | 9 | 0 | 9/9 | 1441.41 | 160.16 | 312 | 75 |
| Windows指引144K | 9 | 0 | 7/9 | 1751.95 | 250.28 | 343 | 74 |
| 通用指引Draft5 | 9 | 0 | 8/9 | 1806.56 | 225.82 | 411 | 120 |


| 組別 | 任務 | 完成 | 未測試 | 成功總秒中位 | 含失敗秒/成功件 | 工具中位 | 工具錯誤合計 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| 舊版144K | bug | 3/3 | 0 | 11.44 | 12.56 | 8.00 | 5 |
| 舊版144K | feature | 2/3 | 0 | 291.02 | 376.48 | 53.00 | 43 |
| 舊版144K | refactor | 3/3 | 0 | 144.89 | 148.32 | 46.00 | 40 |
| 通用指引144K | bug | 3/3 | 0 | 13.69 | 12.57 | 7.00 | 3 |
| 通用指引144K | feature | 3/3 | 0 | 230.70 | 245.29 | 42.00 | 39 |
| 通用指引144K | refactor | 3/3 | 0 | 233.05 | 222.61 | 43.00 | 33 |
| Windows指引144K | bug | 3/3 | 0 | 13.28 | 13.39 | 7.00 | 0 |
| Windows指引144K | feature | 3/3 | 0 | 194.31 | 189.64 | 37.00 | 13 |
| Windows指引144K | refactor | 1/3 | 0 | 281.61 | 1142.89 | 66.00 | 61 |
| 通用指引Draft5 | bug | 3/3 | 0 | 11.70 | 10.84 | 7.00 | 2 |
| 通用指引Draft5 | feature | 2/3 | 0 | 194.33 | 438.92 | 57.00 | 48 |
| 通用指引Draft5 | refactor | 3/3 | 0 | 321.27 | 298.73 | 79.00 | 70 |


主要時間為CLI啟動到外部驗收／公開測試結束，包含工具與逾時收尾；不含引擎起跑及降溫。外部驗收、既有測試、保護檔案、CLI正常結束且真的執行測試，全部成立才算成功。480秒仍只是本實驗監督逾時，沒有改成正式工具總上限。

## 每次任務與資源

| Run | 完成 | 總秒 | 工具 | 工具錯誤 | 橋接重試 | 連續重複 | 外部驗收 | 保護檔變更 | 餘裕MiB | 最高°C | 錯誤 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dflash144-bug-0 | True | 14.62 | 8 | 2 | 0 | 0 | 4/4 | [] | 379.0 | 60.0 |  |
| dflash144-feature-0 | True | 321.11 | 65 | 17 | 0 | 0 | 9/9 | [] | 377.0 | 87.0 |  |
| dflash144-refactor-0 | True | 95.58 | 27 | 4 | 0 | 0 | 10/10 | [] | 320.0 | 87.0 |  |
| dflash144-bug-1 | True | 9.41 | 6 | 0 | 0 | 0 | 4/4 | [] | 344.0 | 82.0 |  |
| dflash144-feature-1 | True | 184.05 | 42 | 10 | 0 | 0 | 9/9 | [] | 344.0 | 88.0 |  |
| dflash144-refactor-1 | True | 339.20 | 77 | 23 | 1 | 1 | 10/10 | [] | 376.0 | 89.0 |  |
| dflash144-bug-2 | True | 13.69 | 7 | 1 | 0 | 0 | 4/4 | [] | 378.0 | 83.0 |  |
| dflash144-feature-2 | True | 230.70 | 37 | 12 | 1 | 1 | 9/9 | [] | 378.0 | 90.0 |  |
| dflash144-refactor-2 | True | 233.05 | 43 | 6 | 0 | 4 | 10/10 | [] | 378.0 | 89.0 |  |
| graph128draft5-bug-0 | True | 12.53 | 9 | 2 | 0 | 0 | 4/4 | [] | 542.0 | 80.0 |  |
| graph128draft5-feature-0 | True | 145.94 | 37 | 7 | 0 | 1 | 9/9 | [] | 542.0 | 89.0 |  |
| graph128draft5-refactor-0 | True | 130.97 | 45 | 12 | 0 | 0 | 10/10 | [] | 542.0 | 89.0 |  |
| graph128draft5-bug-1 | True | 8.30 | 6 | 0 | 0 | 0 | 4/4 | [] | 549.0 | 82.0 |  |
| graph128draft5-feature-1 | True | 242.72 | 61 | 9 | 0 | 0 | 9/9 | [] | 547.0 | 89.0 |  |
| graph128draft5-refactor-1 | True | 321.27 | 79 | 24 | 2 | 5 | 10/10 | [] | 547.0 | 90.0 |  |
| graph128draft5-bug-2 | True | 11.70 | 7 | 0 | 0 | 0 | 4/4 | [] | 549.0 | 83.0 |  |
| graph128draft5-feature-2 | False | 489.19 | 57 | 32 | 0 | 0 | 7/9 | [] | 547.0 | 91.0 | Supervised timeout during agent; no completed/unowned CLI PID terminated |
| graph128draft5-refactor-2 | True | 443.95 | 110 | 34 | 7 | 13 | 10/10 | [] | 547.0 | 91.0 |  |
| dflash144windows-bug-0 | True | 13.28 | 7 | 0 | 0 | 0 | 4/4 | [] | 385.0 | 85.0 |  |
| dflash144windows-feature-0 | True | 216.70 | 47 | 5 | 0 | 1 | 9/9 | [] | 385.0 | 90.0 |  |
| dflash144windows-refactor-0 | True | 281.61 | 59 | 17 | 1 | 3 | 10/10 | [] | 383.0 | 89.0 |  |
| dflash144windows-bug-1 | True | 11.88 | 7 | 0 | 0 | 0 | 4/4 | [] | 385.0 | 83.0 |  |
| dflash144windows-feature-1 | True | 194.31 | 37 | 6 | 0 | 1 | 9/9 | [] | 385.0 | 89.0 |  |
| dflash144windows-refactor-1 | False | 488.27 | 82 | 28 | 0 | 3 | 10/10 | [] | 126.0 | 89.0 | Supervised timeout during agent; no completed/unowned CLI PID terminated |
| dflash144windows-bug-2 | True | 15.00 | 7 | 0 | 0 | 0 | 4/4 | [] | 283.0 | 80.0 |  |
| dflash144windows-feature-2 | True | 157.89 | 31 | 2 | 0 | 0 | 9/9 | [] | 179.0 | 82.0 |  |
| dflash144windows-refactor-2 | False | 373.02 | 66 | 16 | 1 | 1 | 9/10 | [] | 87.0 | 83.0 |  |


完整輸入／輸出token（輸入含cache）、重複工具、停止原因及資源見[coding.csv](coding.csv)。250ms抽樣量整張卡，含桌面程式，可能漏掉瞬時峰值；本輪沒有改原450W功耗上限、風扇或顯存設定。

## 工具使用有沒有改變

| 組別 | Read | Write | Edit | Bash | Bash含python -c/heredoc | Bash含寫檔字樣 |
| --- | --- | --- | --- | --- | --- | --- |
| 舊版144K | 59 | 0 | 36 | 226 | 86 | 56 |
| 通用指引144K | 84 | 1 | 27 | 199 | 88 | 58 |
| Windows指引144K | 68 | 0 | 28 | 246 | 141 | 48 |
| 通用指引Draft5 | 65 | 2 | 18 | 326 | 165 | 72 |


最後兩欄為命令文字的可重現規則分類，可能包含正當的檢查／測試，不直接當錯誤或循環。重複呼叫也可能是必要的重跑測試。指引只在實際採用率和外部驗收有改善時才算有效，不能只看提示文字。

### 工具錯誤分類

| 組別 | 需授權／遭拒 | Python語法 | 不存在工具 | 匯入 | 找不到檔案 | 測試／其他命令 |
| --- | --- | --- | --- | --- | --- | --- |
| 舊版144K | 21 | 4 | 0 | 0 | 25 | 38 |
| 通用指引144K | 19 | 3 | 2 | 1 | 8 | 42 |
| Windows指引144K | 2 | 2 | 1 | 0 | 6 | 63 |
| 通用指引Draft5 | 31 | 12 | 2 | 0 | 2 | 73 |


例如通用指引的一回重構反覆使用python3、/tmp、/usr/bin，出現13次需要授權的工具錯誤；Windows指引因此另列一個實驗組，明示python、既有工作目錄及獨立測試命令，沒有放寬Bash權限。它是在觀察這批任務後定向調整的指引，仍需未見過的真實專案驗證，不能宣稱已證明通用Coding能力。分類依原始工具結果文字，可在error-analysis.json稽核；測試失敗也可能是正常診斷。

### 本輪實際覆蓋的輸入與資源

| 組別 | 單次最大完整輸入token | 最低餘裕MiB | 最高°C | 峰值W | 工具JSON拒絕事件 | CLI API重試事件 |
| --- | --- | --- | --- | --- | --- | --- |
| 舊版144K | 未統計 | 542.0 | 90.0 | 447.27 | 0 | 0 |
| 通用指引144K | 41754 | 320.0 | 90.0 | 449.36 | 0 | 0 |
| Windows指引144K | 32907 | 87.0 | 90.0 | 448.91 | 0 | 0 |
| 通用指引Draft5 | 73812 | 542.0 | 91.0 | 450.95 | 0 | 0 |


單次輸入取引擎完成RPC日誌，含已快取前綴；它與累計輸入token或設定窗口不同。舊控制缺少此最大值時標未統計，不補猜。這輪沒有重測96K以上的長文精確找回，也沒有證明新的指引修復了上輪長文誤答。任務仍是固定的小型英文Python專案，未做長期真實專案驗證。

### 客戶端壓縮成本

| Run | 觸發 | 壓縮前客戶端token | 壓縮後token | 耗時秒 |
| --- | --- | --- | --- | --- |
| graph128draft5-feature-2.claude.jsonl | auto | 77314 | 6863 | 74.14 |


這是Claude Code原始compact_boundary事件，不是引擎配置容量。觀測到的壓縮成本已包含於任務時間；本輪沒有調整壓縮門檻，也不把壓縮或不同工具路徑的成本當成Draft5的單一因果效果。

## 採用與回退

- 指引預設：通用改檔指引。完整決策與各組統計見[guidance-decision.json](guidance-decision.json)。
- Draft5啟動條件：144K至少完成8/9，實際完成9/9；本輪已進入實測，它維持獨立實驗配置。
- 每個配置仍只有三次／任務，不是大規模統計證明。舊版與新版分時執行，未完全等溫或隨機化；不可把小差異宣稱為普遍勝率或GPU參數的因果效果。
- Draft5維持獨立131072／Graph ON／draft5／chunk256；第一個啟動／OOM失敗即停止該Profile，不降低Context刷分、不停用防循環、不覆寫原Profile。
- 舊版原始部署程式在baseline/runtime，本輪中間部署快照在rollback；回退須先確認8081與引擎沒有正式工作，只重啟自有橋接。舊版會恢復已知小輸出額度問題，不建議因指引無效而把API修正一起撤掉。

## 可重現

先在新的獨立資料夾放scripts；確認ROOT指向本機部署、REPO位置正確，而且沒有正式任務。保留原始資料，不在這份已修改的runs上重跑。

```powershell
python scripts/lab.py inventory
python scripts/fixtures.py
python scripts/api_smoke.py
python scripts/run_study.py
python scripts/run_windows.py
python scripts/report.py
```

run_study先跑144K九次並稽核；完成至少8/9且沒有未測任務時，才進Draft5九次（仍會在首次啟動失敗停止）。要重跑歷史控制，需明確使用舊runtime／無新增指引，不能把新版當成舊版。

- [protocol.json](protocol.json)、[tested-source.json](tested-source.json)、[fixture-comparison.json](fixture-comparison.json)：實測來源、設定及任務一致性。
- [api-validation.json](api-validation.json)：實際HTTP上限、思考、工具與串流驗證。
- [raw/coding.jsonl](raw/coding.jsonl)、[raw/coding-audit.jsonl](raw/coding-audit.jsonl)、[coding.csv](coding.csv)：原始任務與稽核。
- [logs/](logs/)、[runs/](runs/)、[fixtures/](fixtures/)：引擎、實際修改與外部驗收。
- [FINALIZED.json](FINALIZED.json)：全部測試結束後的模型、設定、部署及服務還原稽核。

## 最後驗收與保留的限制

- 35項自動unit／HTTP測試及安裝器dry-run通過；真實Claude啟動器與OpenCode各完成一次新Bug專案，外部測試通過、保護檔案未改。這兩次是整合冒煙檢查，未混入27次Coding比較。
- 已還原144K／Graph OFF／draft3，六份穩定Profile、原引擎參數、模型及引擎雜湊一致；工具總上限仍null，防循環保留。新開原桌面Claude Code捷徑即可使用通用指引。
- 權限審計發現Windows實驗一回提出pip升級的複合命令；工具在執行前預檢拒絕，未執行。沒有為跑分放寬授權，未下載其他模型或安裝新Harness。完整紀錄見[dependency-review.json](dependency-review.json)。
- 仍會有工具試錯、語法與語意錯誤；這組已知小專案不是無人監督、長期真實專案的可靠性認證。CLI原始美元成本是SDK估算，不是本機實際帳單。
- 下一步先用未見過的真實專案驗證通用指引，再單獨核對Claude的壓縮預留與成本，以及未宣告工具／反覆授權錯誤的有界糾正。這些仍未實作或量化收益，不繼續調提示挑本批測試分數。

核心修正[3ab5cc6的GitHub Actions](https://github.com/hh123456tw/bonsai-local-agent/actions/runs/41625773526)已success；[CI紀錄](ci-validation.json)。
