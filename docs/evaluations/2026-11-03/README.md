# 2026-11-03 RTX 3080／Bonsai 實機評估

先看[完整報告](REPORT.md)。本資料為固定歷史測試，包含失敗及未測項目；沒有把實驗候選部署為穩定Profile。

- [推論CSV](benchmark.csv)、[Coding CSV](coding.csv)、[Context CSV](context.csv)
- [設定差異](profile-differences.json)、[Hermes方案](HERMES_PLAN.md)
- `raw/`、`logs/`：合成題目／可拋棄專案的原始量測、CLI與引擎紀錄，沒有個人聊天紀錄。
- `fixtures/`、`runs/`、`prompts/`、`profiles/`、`scripts/`：起始資料、實際修改、標準答案、獨立參數與重跑工具。

模型、引擎、DLL、個人Claude設定目錄及憑證不在這份資料中。模型與引擎只記錄大小、來源及雜湊。

## 解壓與重跑

SSE及GPU原始逐次紀錄以gzip無損壓縮；其他核心JSONL直接提供。若要在報告原始腳本中驗證所有檔案連結，先將本目錄複製到獨立工作資料夾，再在該副本執行：

```powershell
python -c "import gzip,pathlib; [(p.with_suffix('').write_bytes(gzip.decompress(p.read_bytes()))) for p in pathlib.Path('.').rglob('*.gz')]"
```

正式重跑另建全新實驗資料夾，從這裡複製`scripts/`，依REPORT的指令重新產生inventory／fixtures／prompts，不要直接覆寫這份歷史資料。原始腳本依本機`C:/AI/bonsai`及實驗目錄的相鄰專案路徑設計；搬到其他位置時，先確認`lab.py`中的ROOT／REPO。驗證腳本的起始repo commit及「乾淨」條件也是測試當時的快照，不能拿這次新增文件後的repo當成當時的HEAD。

重跑會切換模型服務；須先確認沒有正式工作，且一次只執行一個控制器。工具任務始終經8081保護橋接，原生Benchmark才走8080。原三套穩定設定不被這份提交修改。

`script-manifest.json`保留實測腳本的原始檔案雜湊。本目錄透過.gitattributes保留原始位元組與LF／CRLF，避免破壞實測雜湊；API Prompt雜湊以實際送出的UTF-8、LF訊息計算。
