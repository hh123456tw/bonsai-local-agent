# Bonsai 大窗口檔位

2026-11-03。此頁取代先前32K預設；先前驗證紀錄仍保留。

| 桌面捷徑 | 模式 | context / 實體KV池 | 短題測速 |
|---|---|---:|---:|
| Bonsai OpenCode 修正版 / DFlash144K | DFlash2、draft3 | 147456 / 147456 | 約181 tok/s |
| Bonsai OpenCode 基本版256K | 無投機解碼 | 262144 / 262144 | 約79 tok/s |
| 停止 Bonsai | 停止自有引擎及橋接，釋放顯存 | — | — |

選擇專案資料夾後進入CLI。固定Build、單請求、思考開啟（預算1536）、rk2v4-e8、4GiB主機快取、prefill256、CUDA graph關閉；不載入Orca。兩個檔位不會同時占GPU；忙碌時拒絕切換。

基本版256K是模型原生最大窗口。DFlash144約13萬token首讀111秒、後續快取追問約1.1秒，但隨機中段精確查找有誤答紀錄。較低精度KV的精確查找曾有誤答，開思考復查恢復；首次讀取24.6萬token約5分鐘。HTTP200不能當作答對，完整資料見known-issues-audit.zh-TW.md和tuning目錄。

OpenCode預留系統/工具、輸出及壓縮空間；標示context不是純使用者輸入容量。

安裝目錄C:\AI\bonsai；OpenCode連127.0.0.1:8081/v1，原始引擎在8080。啟動器會驗真實生成，檢查配置與自有PID。關閉CLI本身保留模型；不用時點停止Bonsai。

橋接最多糾正重試兩次，工具上限24；仍無進展會明確回報未完成，停止不算成功。輸出上限訊號不再被隱藏，日誌見guard-events.jsonl。橋接會緩衝一輪後才送出。

這是已發布引擎的部署調校，沒有宣稱已編譯未合併PR10，亦未完成Claude Code的Anthropic保護橋接。
