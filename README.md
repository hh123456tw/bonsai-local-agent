# Bonsai Local Agent — Windows / RTX 3080 12GB

已在 Windows、i7-12700K、RTX 3080 12GB、32GB RAM、OpenCode CLI 2.2.5 驗證的本機程式 agent 設定。

**預設 DFlash2 144K（147,456 token）；另提供基本版 256K（262,144 token）。兩個檔位的實體 KV 池都等於 context window，使用 rk2v4-e8。思考開啟，單輪預算 1,536 token。**

較低精度 KV 有品質取捨。256K 無思考測試曾在隨機中段記錄查找中誤答；開思考復查答對，但需完整重讀約323秒。原誤答保留，見 [長文驗證紀錄](docs/tuning/base256-long.json) 與 [開思考復查](docs/tuning/base256-thinking-recheck.json)。容量可用不代表所有長文查找都正確。

## 安裝與使用

需求：Windows x64、NVIDIA CUDA 13 相容驅動、Visual C++ x64 Runtime、Python 3.11+、OpenCode CLI 2.x。

```powershell
python -m pip install -r requirements.txt
python install.py --root C:\AI\bonsai
powershell -NoProfile -ExecutionPolicy Bypass -File C:\AI\bonsai\start.ps1
```

安裝器會下載引擎、模型、FFmpeg 和 curl，檢查已知引擎及模型 SHA-256；NVIDIA DLL 優先重用本機 Strata/Ollama 的 CUDA 13 執行庫，找不到才下載 NVIDIA 的 PyPI 套件。安裝本身不啟動模型、不改全域 OpenCode 設定；安裝後會建立桌面啟動與停止捷徑。預設啟動 DFlash144；基本版使用「Bonsai OpenCode 基本版256K」。切換時若模型忙碌會拒絕，避免中斷工作。模型下載約 9.52 GB，分段下載與組裝需額外暫存空間。

現有部署的檔案與狀態不提交 Git。模型、引擎、DLL、個人聊天、原失敗對話紀錄、憑證與本機路徑記憶均排除。

## 防循環的實際行為

- 已發布的 fusion-kvmem sm_86 引擎：思考重複懲罰 1.0、一般 presence 0。
- 橋接層設定思考預算，剝除舊 reasoning 欄位，設定 preserve_thinking=false。
- 相同工具連續執行兩次後，若模型仍要求同一工具，最多糾正重試兩次。
- 無法恢復時明確停止、回報未完成；本輪 24 次工具為上限，停止不算成功。輸出預設16384，保留客戶端請求至32768；length會記錄為截斷事件。
- 為檢查工具指令，橋接層會緩衝一輪回應；不是逐 token 即時顯示。
- OpenCode 使用獨立 config、Build，停用 Orca / Superpowers。

此套件**沒有編譯未合併的 PR #10**。它使用已發布引擎內既有的思考預算及思考懲罰，加上本機恢復橋接。PR #10 的逐請求 presence 切換沒有啟用。

## 驗證範圍

`python -m unittest discover -s tests` 驗證橋接策略。先前32K基準見 [validation.json](docs/validation.json)；最新容量與已知問題對照見 [audit](docs/known-issues-audit.zh-TW.md) 和 [tuning](docs/tuning/)。

RTX 3080 12GB 實機：兩份歷史失敗對話的請求重播已脫離原重複指令；另以真實 OpenCode 讀檔、改檔與執行測試，完成 2D→3D 貪吃蛇核心及 pygame 版本錯誤修復，10 次工具呼叫、連續重複 0 次、64.1 秒，四項測試由外部重跑通過且測試檔未改。歷史重播未執行模型提出的工具，實際編程驗證不包含完整圖形遊戲。

上述64.1秒是先前32K基本版的基準，不是新檔位測速。新檔位短題256 token：DFlash144約181 tok/s、基本版256約79 tok/s；啟動時顯存餘裕分別約539 / 530 MiB。兩者關CUDA graph，prefill chunk 256；主機快取均4GiB。DFlash後續啟動實測也有約447.5MiB餘裕，Windows其他GPU程式會影響餘裕。

完整首次讀取24.6萬token約302秒；同模式後續快取追問約0.6～0.8秒。OpenCode會為系統/工具、輸出與壓縮預留空間（DFlash buffer24576、基本版32768），不能將整個標示窗口當成純使用者輸入。

重跑GPU長測（先切到對應檔位）：
```powershell
python tools/long_context_check.py 147456 dflash144 --thinking
python tools/long_context_check.py 262144 base256 --thinking
```
自動測試只驗橋接策略，不在GitHub CI載入模型。完整長任務品質仍需依實際專案驗證。

最新DFlash144實際改檔：17次工具呼叫、連續重複0、65.3秒，四項測試外部重跑通過且測試檔未改。4GiB host cache將13萬token後續追問從約39秒降到約1.1秒，但同一個隨機中段精確查找仍誤答；詳見 [完整摘要](docs/tuning/summary.json)。

## 可以接 Claude 嗎？

Claude Code 可以以 Anthropic 相容 Messages API 連到本機模型，但模型仍是 Bonsai，並不會變成 Claude。

原始 NInfer 引擎的 `http://127.0.0.1:8080` 支援 `/v1/messages`；目前防循環橋接的 `http://127.0.0.1:8081/v1` 只支援 OpenAI Chat Completions。**直接讓 Claude Code 連 8080 會繞過工具循環恢復層，因此本版沒有將它標為已驗證的 Claude Code 整合。** 不要把 8081 的 OpenAI URL 直接填進 ANTHROPIC_BASE_URL。

參考：[Claude Code gateway 設定](https://code.claude.com/docs/en/llm-gateway-connect)、[模型設定](https://code.claude.com/docs/en/model-config)。Claude 聊天網頁/App 與 Claude Code 是不同的客戶端。

## 上游與授權

本倉僅含自行撰寫的橋接、安裝及啟動腳本與設定，採 MIT；不重新分發任何第三方引擎、模型或 DLL。各下載資產仍適用其原始授權。

- [NInfer Fusion KVMem](https://github.com/1314521gjy/ninfer-fusion-kvmem)（Apache-2.0）
- [防循環實測 / issue #3](https://github.com/1314521gjy/ninfer-fusion-kvmem/issues/3)
- [PR #10](https://github.com/1314521gjy/ninfer-fusion-kvmem/pull/10)
- [模型](https://huggingface.co/WaveCut/Ternary-Bonsai-2-27B-NInfer-v3)
- [FFmpeg builds](https://github.com/BtbN/FFmpeg-Builds)、[curl Windows](https://curl.se/windows/)、[NVIDIA CUDA](https://docs.nvidia.com/cuda/)
