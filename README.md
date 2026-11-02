# Bonsai Local Agent — Windows / RTX 3080 12GB

已在 Windows、i7-12700K、RTX 3080 12GB、32GB RAM、OpenCode CLI 2.2.5 驗證的本機程式 agent 設定。

**目前 DFlash 關閉，context window / KV 均為 32,768 token。思考開啟，單輪預算 1,536 token。**

## 安裝與使用

需求：Windows x64、NVIDIA CUDA 13 相容驅動、Visual C++ x64 Runtime、Python 3.11+、OpenCode CLI 2.x、7-Zip（只在安裝時解壓 curl 使用）。

```powershell
python -m pip install -r requirements.txt
python install.py --root C:\AI\bonsai
powershell -NoProfile -ExecutionPolicy Bypass -File C:\AI\bonsai\start.ps1
```

安裝器會下載引擎、模型、FFmpeg 和 curl，檢查已知引擎及模型 SHA-256；NVIDIA DLL 優先重用本機 Strata/Ollama 的 CUDA 13 執行庫，找不到才下載 NVIDIA 的 PyPI 套件。安裝本身不啟動模型、不改全域 OpenCode 設定；安裝後會建立桌面啟動與停止捷徑。模型下載約 9.52 GB，分段下載與組裝需額外暫存空間。

現有部署的檔案與狀態不提交 Git。模型、引擎、DLL、個人聊天、原失敗對話紀錄、憑證與本機路徑記憶均排除。

## 防循環的實際行為

- 已發布的 fusion-kvmem sm_86 引擎：思考重複懲罰 1.0、一般 presence 0。
- 橋接層設定思考預算，剝除舊 reasoning 欄位，設定 preserve_thinking=false。
- 相同工具連續執行兩次後，若模型仍要求同一工具，最多糾正重試兩次。
- 無法恢復時明確停止、回報未完成；本輪 24 次工具為上限，停止不算成功。
- 為檢查工具指令，橋接層會緩衝一輪回應；不是逐 token 即時顯示。
- OpenCode 使用獨立 config、Build，停用 Orca / Superpowers。

此套件**沒有編譯未合併的 PR #10**。它使用已發布引擎內既有的思考預算及思考懲罰，加上本機恢復橋接。PR #10 的逐請求 presence 切換沒有啟用。

## 驗證範圍

`python -m unittest discover -s tests` 驗證橋接策略。實機紀錄見 [validation.json](docs/validation.json)。

RTX 3080 12GB 實機：兩份歷史失敗對話的請求重播已脫離原重複指令；另以真實 OpenCode 讀檔、改檔與執行測試，完成 2D→3D 貪吃蛇核心及 pygame 版本錯誤修復，10 次工具呼叫、連續重複 0 次、64.1 秒，四項測試由外部重跑通過且測試檔未改。歷史重播未執行模型提出的工具，實際編程驗證不包含完整圖形遊戲。

快取路由後，停止到重新可生成約 8.42 秒；引擎權重約 6.70 GiB，32K 時引擎回報約 3.33 GiB 顯存餘裕。未驗證全部長任務，也尚未重新測 DFlash。

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
