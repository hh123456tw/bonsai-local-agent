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

橋接最多糾正重試兩次，工具總次數目前無上限（仍可設定有限額度）；仍無進展會明確回報未完成，停止不算成功。輸出上限訊號不再被隱藏，日誌見guard-events.jsonl。橋接會緩衝一輪後才送出。

這是已發布引擎的部署調校，沒有宣稱已編譯未合併PR10。

Claude Code 已接入同一套防循環橋接。桌面「Bonsai Claude Code」使用 DFlash144K，「Bonsai Claude Code 基本版256K」使用基本版；雙擊後選擇專案資料夾。若要換專案，關閉該 CLI 後重新點捷徑選擇資料夾。關閉 CLI 會保留模型，不用時點「停止 Bonsai」。

Anthropic base URL 是 `http://127.0.0.1:8081`（不加 `/v1`），提供 Messages、SSE 與 count_tokens。獨立啟動器設定模型 bonsai2-27b、思考預算1536，移除舊思考回傳，預留壓縮空間；不更動平常的 Claude 登入和全域設定。只啟用 Read/Write/Edit/Bash/Glob/Grep，不載入個人 MCP 或外掛；一般工具授權仍由 CLI 管理。

支援文字及客戶端工具，不支援圖片、文件區塊、雲端內建工具。串流會先緩衝一輪做檢查，長文首讀可能等數分鐘；請求逾時設為900秒。模型仍是 Bonsai，不是 Claude。新環境可能需要完成 CLI 的介面初始選項，無須填入雲端 API 金鑰。CLI 的 unknown model 提示及估算美元金額不是雲端帳單；本機窗口已明確設定。

若看到舊「24次工具」訊息，來源是本機橋接。現可編輯 `C:\AI\bonsai\guard-config.json` 的 `max_tool_calls`，下一次請求生效；目前設定null取消總次數上限；若改為有限額度，達上限可由使用者輸入「繼續」開新輪接續，沒有啟用無限自動重開。詳見 [來源與接續說明](tool-budget.zh-TW.md)。

新增可選「Bonsai Claude Code 加速128K」：DFlash2與CUDA Graph開啟，完整KV/context131072、壓縮窗口106496。原144K與256K捷徑保留，預設未變。速度、啟動失敗與容量取捨見 [CUDA Graph實測](cuda-graph.zh-TW.md)。
