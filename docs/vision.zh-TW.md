# Bonsai 看圖模式

已於2026-11-03在這台 RTX 3080 12GB 完成實測。Bonsai 能看圖：原本部署沒啟用視覺，也沒有讓橋接接受圖片。已安裝的同一個 `.ninfer` 檔包含視覺元件，無需下載另一個模型；見[模型作者的元件與啟動說明](https://huggingface.co/WaveCut/Ternary-Bonsai-2-27B-NInfer-v3)。

## 如何使用

1. 結束目前的 Agent 任務。
2. 雙擊桌面 **Bonsai Claude Code 看圖96K** 或 **Bonsai OpenCode 看圖96K**，選擇專案資料夾。
3. Claude Code 可要求「用 Read 讀取這張截圖，解釋錯誤」。OpenCode 可附加圖片；CLI 亦可用 `run --file 圖片路徑 "請解釋這張圖"`。

原本桌面捷徑仍使用原本檔位。切回純文字工作，使用原本 **Bonsai Claude Code**（144K）；需要更長文字則使用基本版256K。切換時若正在生成或準備圖片，啟動器會拒絕重啟，請等任務結束。服務由本專案共用，請勿在另一個客戶端執行任務時切換。

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File C:\AI\bonsai\start-claude.ps1 -Profile dflash96vision
# OpenCode 改用 start.ps1，其餘相同。
```

## 設定與取捨

|項目|看圖模式|
|---|---|
|Profile|`dflash96vision`，獨立新增|
|Context / KV|98,304，`rk2v4-e8`|
|DFlash2 / CUDA Graph|draft 3 / OFF|
|視覺權重|`overlay`：平時放系統記憶體，讀圖時暫借 GPU 記憶體|
|每圖視覺 token 上限|2,048；大圖縮小可能漏掉細字，請裁切重要區域|
|圖片前處理|cache 128 MiB、live 上限2,048 MiB、2 workers；這是主機端媒體容量設定，並非預留2 GiB顯存|
|Claude 自動壓縮門檻|73,728；預留24,576，圖片也占 Context|
|Agent API|8081保護橋接，兩種協定共用，序列執行|

96K 是本次保守新增的容量，**沒有測出它是看圖的最大容量，也沒有驗證填滿96K後的視覺正確率**。這輪不重跑之前的長文與 Coding 效能評估。原144K、128K Graph及256K六個設定檔均通過SHA比對，沒有覆寫。

## 實測結果

|測試|結果|
|---|---|
|OpenAI 圖片A、B、再A|3/3：圖形、顏色與PIN都正確；換圖未誤用前圖|
|Anthropic 錯誤畫面|讀出 FAILED、E317、tax_code、128.40|
|Anthropic Read工具圖片回傳|圖形、顏色與PIN正確|
|Anthropic 圖片SSE|內容正確，含message_stop|
|含圖片count_tokens|成功，原生計數480 tokens|
|真實Claude Code啟動器|只呼叫1次Read，2輪完成，4.70秒；正確讀出綠色三角形、紫色長方形、8462|
|真實OpenCode附件|7.17秒完成，四項畫面文字都正確|

6個短API請求完整耗時0.27–1.13秒（包含熱前綴，不能當冷啟動平均）。API與兩個CLI短測試抽樣顯存最低餘裕990 MiB，最高溫52°C；250ms取樣可能漏掉瞬間峰值。這些是少量合成圖驗證，不能代表任意照片、細字、複雜圖表或長時間任務都可靠。

第一個實驗把媒體live容量設成256 MiB，前端啟動檢查明確拒絕，未發生OOM；依錯誤改為引擎預設2,048 MiB後成功，失敗日誌一併保留。

## 橋接邊界

支援 OpenAI `image_url`、Anthropic user圖片及`tool_result`內圖片；Anthropic接受PNG/JPEG/WebP/GIF的base64或HTTP(S)URL，單張base64解碼上限16 MiB，整個請求上限64 MiB。實測僅PNG內嵌；URL、其他格式、動圖多幀、影片及大型多圖**未實測**。文件區塊、Files API與雲端內建工具仍不支援。

完整一輪檢查後才輸出SSE，並非逐token即時串流。保留防循環檢查、客戶端輸出額度、工具錯誤檢查；`max_tool_calls=null`，OpenCode沒有額外steps固定上限。

## 證據與重跑

[本輪原始資料](evaluations/2026-11-03-vision/FINALIZED.json)、[API已知答案結果](evaluations/2026-11-03-vision/image-results.json)、[腳本與合成圖片](evaluations/2026-11-03-vision/)。Claude完整輸出包含Read回傳的圖片，OpenCode完整輸出保留附件結果；模型與引擎SHA、原設定SHA均在資料內。

本專案已安裝且空閒時，先啟動看圖模式，再於本repo執行：

```powershell
python C:\AI\bonsai\bonsai_ensure.py --profile dflash96vision
python docs/evaluations/2026-11-03-vision/scripts/test_images.py
python docs/evaluations/2026-11-03-vision/scripts/test_clients.py
python -m unittest discover -s tests
```

前兩個實測腳本會寫入同資料夾並使用GPU，請勿與正式Agent任務同時跑。測試不下載套件、模型，也不修改模型權重。
