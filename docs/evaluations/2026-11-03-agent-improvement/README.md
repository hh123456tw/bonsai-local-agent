# API預算與Coding指引改善實測

先看[完整報告](REPORT.md)、[逐次Coding CSV](coding.csv)和[最終部署確認](FINALIZED.json)。這份資料保留所有失敗／未測試組；前一輪Benchmark另在[2026-11-03](../2026-11-03/REPORT.md)。

本輪比較原144K、通用指引144K、Windows指引144K，以及通用指引Draft5。實驗Profile只在此資料夾，沒有覆寫三套原穩定設定。指引採用決策及門檻見guidance-decision.json與windows-protocol.json；指引是在已知失敗上調整，並非獨立未見過的專案測試。

`raw/`、`logs/`、`runs/`保留合成任務的原始CLI、引擎及修改結果；沒有個人聊天、模型、引擎、DLL或憑證。`baseline/runtime/`、`tested-runtime/`、`deployed-runtime/`分別保存原部署、指引選擇前的測試版本、最終部署版本；rollback/保留中間程式快照，不建議直接把已知預算問題一起恢復。

## 壓縮與重跑

*.sse及raw/gpu.jsonl無損gzip壓縮；可在這份資料的獨立副本執行：

```powershell
python -c "import gzip,pathlib; [(p.with_suffix('').write_bytes(gzip.decompress(p.read_bytes()))) for p in pathlib.Path('.').rglob('*.gz')]"
```

重跑請另建全新實驗資料夾，複製scripts/與baseline/，確認lab.py中的ROOT／REPO及舊資料路徑正確，依REPORT的命令產生新的inventory／fixtures。不要覆寫這份歷史資料或重用已修改的runs。正式Agent經8081，測試前須確認沒有正式任務；一次只啟動一個模型控制器。

GUIDANCE在guidance_versions.py凍結，各run也保留實際文字與SHA。三個任務的使用者Prompt及外部驗收保持一致。FINALIZED是提交這份文件之前的當時狀態，不能拿之後的repo HEAD當成舊的來源commit。

.gitattributes保留本目錄的原始位元組／CRLF，script-manifest及fixture hashes可直接核對。packaging.json記錄套件雜湊、排除項及改寫的報告相對連結；gzip解壓後與原始量測一致。

## 測試執行再核對

[工具執行審計](test-execution-audit.json)對照36次紀錄（含歷史控制9次）的工具呼叫及結果：所有標為完成的案例，都有非零測試數、成功結束的測試工具輸出；並非只看Agent說自己有跑測試。
