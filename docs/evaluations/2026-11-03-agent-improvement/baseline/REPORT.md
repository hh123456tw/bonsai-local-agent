# RTX 3080 12GB／Bonsai 2 27B 完整評估報告

測試日：2026-11-03，Asia/Taipei。本報告僅引用本輪產生的資料；歷史190／209 tok/s及單次Agent成功紀錄沒有混入本輪統計。

## 先看結論

- **日常Coding暫選dflash144**：144K OFF完成8/9，128K Graph完成6/9。只代表這三個小型Python任務的結果；仍需外部測試與審查。
- **極速只列實驗候選graph128draft5**：512-token短題冷樣本中位數220.72 tok/s；原128K Graph/draft3為201.79，144K OFF為182.49。尚未把這個新候選部署為日常配置。
- **同128K控制組**：Graph ON 201.79、OFF 182.64 tok/s，觀測差10.48%；測試順序與熱條件未完全控制，不視為精確因果估計。
- **大窗口不等於可靠長文記憶**：DFlash兩組在32K／64K這組七項查找全對，96K起出現誤答；這次常見於後段及結尾，不能籠統歸為中段遺忘。256K模式仍只驗到約120K輸入。
- 三套原穩定Profile保留；未增加正式工具總次數限制、未停用防循環、未安裝Hermes。所有改動與測試只在獨立實驗資料夾。

## 1. 環境與保護措施

- CPU：12th Gen Intel(R) Core(TM) i7-12700K；RAM可用實體位元組：34088275968。
- OS：Microsoft Windows 11 專業版，build 26200。
- GPU／驅動初始狀態：`NVIDIA GeForce RTX 3080, 610.88, 12288 MiB, 11614 MiB, 478 MiB, 37, 32.31 W`。
- Python：3.11.9 (tags/v3.11.9:de54cf5, Apr  2 2024, 10:12:12) [MSC v.1938 64 bit (AMD64)]；Claude Code：2.1.316 (Claude Code)；OpenCode：opencode v2.2.5。
- 模型：Ternary-Bonsai-2-27B-ninfer-v3.ninfer，9520051456 bytes；SHA256 `cdc4810b0ff17c40d0f62cf214b6e0bcd08346e9eb05ca53371507037793c14a`。
- 引擎：現有Fusion KVMem sm86二進位，build字串為unknown；不推測未標示的版本。SHA256 `cd6be5e8ca872a1044aaab4c219be38d2787ee852429e2dd9b073e635dcf5d3f`，820153856 bytes。
- 專案起始commit：`e0ed5de21701b5eb1afbb7cd90257a61196fdbc9`。
- 穩定Profile雜湊比對：True；原啟動參數保留／恢復：True。
- 實驗Profile都在本資料夾profiles；未改模型權重、未安裝Harness或大型依賴。重啟前檢查slots，僅停止engine.pid對應且ExecutablePath符合的自有程序；橋接保持原有保護。

引擎來源：安裝器釘選雜湊與[engine-v0.11.0-kvmem-20261008的sm86資產](https://github.com/1314521gjy/ninfer-fusion-kvmem/releases/download/engine-v0.11.0-kvmem-20261008/ninfer-serve-86.exe)一致。這是可追溯的發行資產標籤；二進位本身沒有提供完整commit/build字串。
模型檔9,520,051,456 bytes＝9.520 GB＝8.866 GiB。這是本機實際v3檔案大小，並非7GB多；不能把其他模型版本、打包大小或載入時顯存占用當成此檔大小。

## 2. 方法與解讀限制

- A：每組獨立重啟，先用不同Prompt暖機，再送相同測試Prompt；各冷／熱至少三次。冷樣本以cache_n=0驗證，熱樣本必須真的有快取命中。舊的45-token短Prompt補測前資料保留但排除統計。
- A原生8080串流：temperature=0、seed=42、思考關閉；ignore_eos=true用來固定256／512／1024輸出。這是吞吐測試，不是自然結束的日常回答。TTFT計第一個非空文字／思考delta，不是HTTP首位元組。
- GPU每250ms由nvidia-smi抽樣整張卡，包含Windows與其他GPU程序，可能漏掉瞬時峰值。非嚴格恆溫環境；功耗、溫度及測試次序均應一起看。
- B：真實Claude Code經8081，原思考1536與橋接temperature=0.3政策不變；CLI未提供可固定的seed，以三次重複顯示隨機性。外部驗收、既有測試、保護檔案與實際執行測試同時通過才算完成。
- C：每個Profile／長度用一個冷資料集與三次同前綴追問；追問是相依樣本，不冒稱三個獨立冷資料集。六個位置加一項帶干擾值的兩段關聯，各自精確比對。原生API未經Harness壓縮。
- 原生TTFT與8081緩衝SSE不同：橋接先等完整一輪再檢查工具；引擎先吐字不表示CLI已能顯示。
- OOM、啟動或API錯誤會停止該組並記錄，不以無限重試挑成功值；沒有數據的項目標「未測試」。

## 3. Benchmark總覽

下表短題Decode取512輸出的冷樣本中位數；其餘Prefill／TTFT／Latency統一取約32K輸入、256輸出的冷樣本。不同Context／檔位差距是整體配方差距；只有相同128K的Graph控制組才較能分離Graph因素。

| Profile | Context | Graph | Draft | Chunk | 短題n | Decode tok/s | 32K Prefill tok/s | 32K TTFT秒 | 32K總秒 | 32K接受率 | 最低餘裕MiB | 最高°C | 啟動成功 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dflash144 | 147456 | OFF | 3 | 256 | 3 | 182.49 | 1933.91 | 16.92 | 18.59 | 58.9% | 392 | 90 | 30/30 |
| dflash128graph | 131072 | ON | 3 | 256 | 3 | 201.79 | 1902.75 | 17.22 | 18.78 | 58.9% | 524 | 89 | 38/39 |
| base256 | 262144 | OFF | 0 | 256 | 3 | 85.22 | 1976.20 | 16.55 | 19.98 | — | 530 | 90 | 26/26 |
| control128off | 131072 | OFF | 3 | 256 | 3 | 182.64 | 1931.26 | 16.95 | 18.62 | 58.9% | 759 | 90 | 21/21 |
| graph128draft2 | 131072 | ON | 2 | 256 | 3 | 174.34 | 未測試 | 未測試 | 未測試 | — | 717 | 81 | 3/3 |
| graph128draft4 | 131072 | ON | 4 | 256 | 3 | 203.25 | 未測試 | 未測試 | 未測試 | — | 713 | 80 | 3/3 |
| graph128draft5 | 131072 | ON | 5 | 256 | 3 | 220.72 | 1908.00 | 17.14 | 18.72 | 42.1% | 203 | 87 | 12/12 |
| graph128chunk128 | 131072 | ON | 3 | 128 | 0 | 未測試 | 未測試 | 未測試 | 未測試 | — | 741 | 81 | 3/3 |
| graph128chunk512 | 131072 | ON | 3 | 512 | 0 | 未測試 | 未測試 | 未測試 | 未測試 | — | 631 | 81 | 3/3 |
| graph128draft5chunk512 | 131072 | ON | 5 | 512 | 1 | 215.37 | 未測試 | 未測試 | 未測試 | — | 263 | 83 | 1/2 |

### 3.1 每種輸入與輸出長度的冷／熱結果

所有數值為中位數；三次樣本的完整值、實際token數、功耗與VRAM見[benchmark.csv](../../2026-11-03/benchmark.csv)。cache_valid=false的第二次請求不是已驗證熱快取，不與真熱快取混算。

| Profile | 輸入 | 輸出 | 快取 | n | 快取分類有效n | Decode | Prefill | TTFT秒 | 總秒 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dflash144 | short | 256 | cold | 3 | 3 | 183.77 | 1609.71 | 0.11 | 1.50 |
| dflash144 | short | 256 | hot | 3 | 3 | 184.10 | 439.05 | 0.02 | 1.41 |
| dflash144 | short | 512 | cold | 3 | 3 | 182.49 | 1605.58 | 0.12 | 2.92 |
| dflash144 | short | 512 | hot | 3 | 3 | 182.42 | 495.59 | 0.02 | 2.83 |
| dflash144 | short | 1024 | cold | 3 | 3 | 189.44 | 1533.23 | 0.11 | 5.50 |
| dflash144 | short | 1024 | hot | 3 | 3 | 189.49 | 430.13 | 0.03 | 5.44 |
| dflash144 | 8192 | 256 | cold | 3 | 3 | 165.94 | 2223.71 | 3.66 | 5.20 |
| dflash144 | 8192 | 256 | hot | 3 | 3 | 166.49 | 421.54 | 0.03 | 1.56 |
| dflash144 | 32768 | 256 | cold | 3 | 3 | 152.96 | 1933.91 | 16.92 | 18.59 |
| dflash144 | 32768 | 256 | hot | 3 | 3 | 153.70 | 281.68 | 0.05 | 1.70 |
| dflash144 | 65536 | 256 | cold | 3 | 3 | 129.51 | 1608.70 | 40.70 | 42.67 |
| dflash144 | 65536 | 256 | hot | 3 | 3 | 129.61 | 229.73 | 0.06 | 2.03 |
| dflash144 | 98304 | 256 | cold | 3 | 3 | 129.36 | 1378.50 | 71.31 | 73.28 |
| dflash144 | 98304 | 256 | hot | 3 | 3 | 128.99 | 141.05 | 0.09 | 2.06 |
| dflash128graph | short | 256 | cold | 3 | 3 | 202.05 | 1601.28 | 0.11 | 1.38 |
| dflash128graph | short | 256 | hot | 3 | 3 | 203.61 | 435.30 | 0.05 | 1.30 |
| dflash128graph | short | 512 | cold | 3 | 3 | 201.79 | 1616.10 | 0.09 | 2.64 |
| dflash128graph | short | 512 | hot | 3 | 3 | 201.79 | 439.46 | 0.03 | 2.55 |
| dflash128graph | short | 1024 | cold | 3 | 3 | 209.03 | 1620.99 | 0.11 | 5.00 |
| dflash128graph | short | 1024 | hot | 3 | 3 | 208.97 | 439.63 | 0.03 | 4.92 |
| dflash128graph | 8192 | 256 | cold | 3 | 3 | 157.68 | 2125.85 | 3.84 | 5.47 |
| dflash128graph | 8192 | 256 | hot | 3 | 3 | 177.67 | 376.78 | 0.03 | 1.48 |
| dflash128graph | 32768 | 256 | cold | 3 | 3 | 162.77 | 1902.75 | 17.22 | 18.78 |
| dflash128graph | 32768 | 256 | hot | 3 | 3 | 163.30 | 263.65 | 0.05 | 1.61 |
| dflash128graph | 65536 | 256 | cold | 3 | 3 | 138.53 | 1581.69 | 41.41 | 43.25 |
| dflash128graph | 65536 | 256 | hot | 3 | 3 | 139.80 | 189.53 | 0.08 | 1.89 |
| dflash128graph | 98304 | 256 | cold | 3 | 3 | 136.83 | 1380.65 | 71.19 | 73.05 |
| dflash128graph | 98304 | 256 | hot | 3 | 3 | 138.34 | 141.48 | 0.09 | 1.94 |
| base256 | short | 256 | cold | 3 | 3 | 85.37 | 1466.14 | 0.12 | 3.11 |
| base256 | short | 256 | hot | 3 | 3 | 84.97 | 249.48 | 0.03 | 3.03 |
| base256 | short | 512 | cold | 3 | 3 | 85.22 | 1463.16 | 0.11 | 6.11 |
| base256 | short | 512 | hot | 3 | 3 | 85.08 | 247.56 | 0.03 | 6.03 |
| base256 | short | 1024 | cold | 3 | 3 | 85.06 | 1472.82 | 0.12 | 12.14 |
| base256 | short | 1024 | hot | 3 | 3 | 84.85 | 250.18 | 0.03 | 12.08 |
| base256 | 8192 | 256 | cold | 3 | 3 | 82.00 | 2324.14 | 3.51 | 6.62 |
| base256 | 8192 | 256 | hot | 3 | 3 | 82.02 | 238.46 | 0.05 | 3.16 |
| base256 | 32768 | 256 | cold | 3 | 3 | 74.54 | 1976.20 | 16.55 | 19.98 |
| base256 | 32768 | 256 | hot | 3 | 3 | 74.60 | 210.27 | 0.06 | 3.47 |
| base256 | 65536 | 256 | cold | 3 | 3 | 66.61 | 1641.25 | 39.92 | 43.75 |
| base256 | 65536 | 256 | hot | 3 | 3 | 66.64 | 182.70 | 0.06 | 3.89 |
| base256 | 98304 | 256 | cold | 3 | 3 | 60.21 | 1400.93 | 70.16 | 74.42 |
| base256 | 98304 | 256 | hot | 3 | 3 | 60.26 | 162.35 | 0.09 | 4.33 |
| control128off | short | 256 | cold | 3 | 3 | 182.71 | 1599.52 | 0.11 | 1.50 |
| control128off | short | 256 | hot | 3 | 3 | 183.97 | 444.11 | 0.03 | 1.42 |
| control128off | short | 512 | cold | 3 | 3 | 182.64 | 1514.98 | 0.11 | 2.91 |
| control128off | short | 512 | hot | 3 | 3 | 182.65 | 444.63 | 0.05 | 2.84 |
| control128off | short | 1024 | cold | 3 | 3 | 189.44 | 1609.44 | 0.11 | 5.50 |
| control128off | short | 1024 | hot | 3 | 3 | 189.19 | 444.40 | 0.03 | 5.44 |
| control128off | 8192 | 256 | cold | 3 | 3 | 165.91 | 2228.53 | 3.66 | 5.19 |
| control128off | 8192 | 256 | hot | 3 | 3 | 166.00 | 419.32 | 0.03 | 1.58 |
| control128off | 32768 | 256 | cold | 3 | 3 | 152.58 | 1931.26 | 16.95 | 18.62 |
| control128off | 32768 | 256 | hot | 3 | 3 | 153.70 | 271.00 | 0.05 | 1.70 |
| control128off | 65536 | 256 | cold | 3 | 3 | 129.22 | 1608.95 | 40.70 | 42.69 |
| control128off | 65536 | 256 | hot | 3 | 3 | 130.25 | 186.91 | 0.08 | 2.03 |
| control128off | 98304 | 256 | cold | 3 | 3 | 128.64 | 1377.85 | 71.33 | 73.31 |
| control128off | 98304 | 256 | hot | 3 | 3 | 129.53 | 141.87 | 0.09 | 2.06 |
| graph128draft2 | short | 512 | cold | 3 | 3 | 174.34 | 1606.70 | 0.12 | 3.05 |
| graph128draft2 | short | 512 | hot | 3 | 3 | 174.30 | 440.65 | 0.01 | 2.95 |
| graph128draft4 | short | 512 | cold | 3 | 3 | 203.25 | 1619.97 | 0.12 | 2.64 |
| graph128draft4 | short | 512 | hot | 3 | 3 | 204.15 | 433.97 | 0.03 | 2.53 |
| graph128draft5 | short | 256 | cold | 3 | 3 | 207.47 | 1556.83 | 0.11 | 1.33 |
| graph128draft5 | short | 256 | hot | 3 | 3 | 209.19 | 410.95 | 0.02 | 1.24 |
| graph128draft5 | short | 512 | cold | 3 | 3 | 220.72 | 1604.48 | 0.09 | 2.42 |
| graph128draft5 | short | 512 | hot | 3 | 3 | 220.41 | 438.64 | 0.02 | 2.34 |
| graph128draft5 | short | 1024 | cold | 3 | 3 | 232.32 | 1600.42 | 0.11 | 4.52 |
| graph128draft5 | short | 1024 | hot | 3 | 3 | 234.00 | 417.52 | 0.03 | 4.41 |
| graph128draft5 | 32768 | 256 | cold | 3 | 3 | 161.91 | 1908.00 | 17.14 | 18.72 |
| graph128draft5 | 32768 | 256 | hot | 3 | 3 | 167.73 | 344.63 | 0.05 | 1.56 |
| graph128chunk128 | 8192 | 256 | cold | 3 | 3 | 192.76 | 1861.46 | 4.36 | 5.69 |
| graph128chunk128 | 8192 | 256 | hot | 3 | 3 | 192.86 | 416.29 | 0.03 | 1.34 |
| graph128chunk512 | 8192 | 256 | cold | 3 | 3 | 190.13 | 2535.92 | 3.20 | 4.55 |
| graph128chunk512 | 8192 | 256 | hot | 3 | 3 | 191.31 | 423.48 | 0.03 | 1.36 |
| graph128draft5chunk512 | short | 512 | cold | 1 | 1 | 215.37 | 1488.13 | 0.11 | 2.48 |
| graph128draft5chunk512 | short | 512 | hot | 1 | 1 | 214.61 | 460.29 | 0.02 | 2.41 |

### 3.2 失敗與未測項目

| Profile／組別 | 狀態 |
| --- | --- |
| graph128draft5chunk512-short-512-1 | Startup failure; group stopped: ['2026-11-03 14:41:11.963  ERROR startup failed / finalizing target / 33.7 ms', '2026-11-03 14:41:12.007  ERROR engine init / FAILED while constructing the service: requested Engine runtime reservation requires 2714174464 bytes, but only 2674962432 bytes are available for runtime capacity', '2026-11-03 14:41:12.007  FATAL server failed during startup / requested Engine runtime reservation requires 2714174464 bytes, but only 2674962432 bytes are available for runtime capacity'] |



### 3.3 所有階段的啟動失敗

總覽的啟動成功數包含A／B／C／補測各階段；餘裕及溫度欄只匯總原生A請求抽樣。Coding／多輪的最低餘裕另列。失敗時未反覆重啟同一組來挑成功值。

| Profile | 階段標籤 | 錯誤 |
| --- | --- | --- |
| graph128draft5chunk512 | graph128draft5chunk512-short-512-1 | 2026-11-03 14:41:11.963  ERROR startup failed / finalizing target / 33.7 ms; 2026-11-03 14:41:12.007  ERROR engine init / FAILED while constructing the service: requested Engine runtime reservation requires 2714174464 bytes, but only 2674962432 bytes are available for runtime capacity; 2026-11-03 14:41:12.007  FATAL server failed during startup / requested Engine runtime reservation requires 2714174464 bytes, but only 2674962432 bytes are available for runtime capacity |
| dflash128graph | multiturn-dflash128graph-120k | 2026-11-03 17:14:59.426  ERROR startup failed / finalizing target / 22.1 ms; 2026-11-03 17:14:59.470  ERROR engine init / FAILED while constructing the service: requested Engine runtime reservation requires 2625894400 bytes, but only 2583916544 bytes are available for runtime capacity; 2026-11-03 17:14:59.470  FATAL server failed during startup / requested Engine runtime reservation requires 2625894400 bytes, but only 2583916544 bytes are available for runtime capacity |


## 4. 真實Coding Agent結果

Task1：inclusive日期Bug；Task2：多幣別與日期過濾功能、須新增至少三個測試；Task3：八模組金額重構，檢查真實使用共用邏輯且保留公開行為。沒有在正式repo做破壞性測試。

| Profile | 任務 | 次數 | 完成 | 成功耗時中位秒 | 含失敗攤提秒/成功件 | 工具中位 | 工具錯誤合計 | 橋接重試合計 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dflash128graph | bug | 3 | 3/3 | 11.23 | 10.90 | 7 | 1 | 0 |
| dflash128graph | feature | 3 | 0/3 | 無成功樣本 | 無成功樣本 | 65 | 70 | 4 |
| dflash128graph | refactor | 3 | 3/3 | 119.72 | 131.09 | 40 | 29 | 0 |
| dflash144 | bug | 3 | 3/3 | 11.44 | 12.56 | 8 | 5 | 0 |
| dflash144 | feature | 3 | 2/3 | 291.02 | 376.48 | 53 | 43 | 0 |
| dflash144 | refactor | 3 | 3/3 | 144.89 | 148.32 | 46 | 40 | 0 |


含失敗攤提＝該組全部執行時間÷成功件數；零成功時沒有可用成功耗時。工具錯誤可能包含正常診斷期間的失敗，不等同最終任務失敗。非連續重複也可能是必要的重測，不直接稱為循環。 主比較時間包含CLI讀寫／工具／測試及外部驗收、公開測試和逾時收尾；不含建置fixture、引擎啟動或降溫。逐次表「秒」另列CLI本身耗時，coding.csv同時保留兩種時間。

| Run | 完成 | 秒 | 工具 | 總模型輸入token | 含cached token | 模型輸出token | 工具錯誤 | 橋接重試 | 橋接停止 | 連續重複 | 全部重用 | 外部測試 | 保護檔變更 | 餘裕MiB | °C | 錯誤 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dflash128graph-bug-0 | True | 11.01 | 7 | 13445 | 10404 | 1540 | 0 | 0 | 0 | 0 | 1 | 4/4 | [] | 716 | 80 |  |
| dflash128graph-feature-0 | False | 480.19 | 77 | 1187887 | 1137394 | 87872 | 31 | 0 | 0 | 1 | 7 | 8/9 | [] | 710 | 89 | Supervised timeout during agent; no completed/unowned CLI PID terminated |
| dflash144-bug-0 | True | 11.24 | 8 | 16511 | 13256 | 1531 | 1 | 0 | 0 | 0 | 1 | 4/4 | [] | 553 | 82 |  |
| dflash144-feature-0 | True | 279.67 | 52 | 736217 | 706362 | 45628 | 9 | 0 | 0 | 0 | 7 | 9/9 | [] | 545 | 89 |  |
| dflash144-refactor-0 | True | 84.86 | 29 | 189874 | 177246 | 13989 | 6 | 0 | 0 | 0 | 2 | 10/10 | [] | 551 | 88 |  |
| dflash144-bug-1 | True | 9.77 | 6 | 10427 | 7438 | 1250 | 0 | 0 | 0 | 0 | 0 | 4/4 | [] | 553 | 81 |  |
| dflash144-feature-1 | False | 170.64 | 53 | 548929 | 525077 | 28252 | 13 | 0 | 0 | 0 | 6 | 8/9 | [] | 545 | 89 |  |
| dflash144-refactor-1 | True | 214.55 | 56 | 420002 | 403333 | 36959 | 22 | 0 | 0 | 0 | 5 | 10/10 | [] | 542 | 88 |  |
| dflash128graph-bug-1 | True | 11.22 | 8 | 17153 | 13765 | 1619 | 1 | 0 | 0 | 0 | 1 | 4/4 | [] | 720 | 83 |  |
| dflash128graph-feature-1 | False | 141.52 | 53 | 425557 | 404132 | 25753 | 18 | 0 | 0 | 0 | 6 | 8/9 | [] | 713 | 89 |  |
| dflash128graph-refactor-1 | True | 110.33 | 40 | 340852 | 323347 | 20213 | 11 | 0 | 0 | 0 | 4 | 10/10 | [] | 719 | 88 |  |
| dflash128graph-bug-2 | True | 9.77 | 6 | 10574 | 7492 | 1241 | 0 | 0 | 0 | 0 | 0 | 4/4 | [] | 721 | 82 |  |
| dflash128graph-feature-2 | False | 480.17 | 65 | 1813050 | 1567176 | 65808 | 21 | 4 | 0 | 5 | 11 | 未能載入驗收 | [] | 713 | 91 | Supervised timeout during agent; no completed/unowned CLI PID terminated |
| dflash128graph-refactor-2 | True | 119.42 | 42 | 323862 | 306394 | 20846 | 15 | 0 | 0 | 0 | 0 | 10/10 | [] | 718 | 88 |  |
| dflash144-bug-2 | True | 16.05 | 11 | 21258 | 17416 | 2491 | 4 | 0 | 0 | 0 | 0 | 4/4 | [] | 544 | 84 |  |
| dflash144-feature-2 | True | 301.80 | 60 | 1142272 | 1098796 | 50923 | 21 | 0 | 0 | 0 | 3 | 9/9 | [] | 551 | 90 |  |
| dflash144-refactor-2 | True | 144.64 | 46 | 391871 | 370597 | 25764 | 12 | 0 | 0 | 0 | 5 | 10/10 | [] | 542 | 89 |  |
| dflash128graph-refactor-3 | True | 162.64 | 35 | 223946 | 208574 | 29231 | 3 | 0 | 0 | 1 | 4 | 10/10 | [] | 137 | 89 |  |


Token優先採各任務時間窗內引擎完成RPC日誌，包含橋接重試與客戶端斷線後的收尾；CLI原始usage另保留。輸入含cache，不能再把cached欄加一次。逾時後補做外部驗收不會把逾時改判成功。

### 4.1 失敗是怎麼發生的

- 128K Graph的feature三次皆未完成：兩次到480秒監督逾時，另一回外部驗收8/9，新增報表把pending款項納入USD總額（5.40而非1.00）。逾時後一回測試檔有SyntaxError，另一回模組匯入缺少normalize_currency；不把逾時的半成品判成功。
- 144K OFF的feature完成2/3，失敗那回同樣把pending款項算進報表。這是語意錯誤，單靠更快Decode或增加Context不能保證修好。
- 重構中可見Bash quoting與受控權限造成多次錯誤／重試。工具輸出中的錯誤次數並非全部是循環；準確連續重複、跨步重用、橋接恢復和最終驗收分開記錄。
- CSV的all_duplicate_calls及Markdown「全部重用」包含連續及非連續相同呼叫，是所有重複簽章額外次數。重用可為正常重跑測試，不能直接等同鬼打牆。
- 每組只有三次，任務和模型路徑差異可能影響結果；本輪不能證明Graph本身導致程式品質下降。完整修改及外部測試輸出均可稽核。

## 5. Context準確率

S=開頭、E=前段、M=中間、L=後段、Z=結尾、R=固定seed隨機位置、X=跨段關聯。冷欄每項是一題；後續欄是同資料三次重送的答對數／3。不得把窗口容量等同有效記憶能力。

| Profile | 目標token | 實際輸入 | 冷S/E/M/L/Z/R/X | 後續各項答對n/3 | 冷Prefill秒 | 冷TTFT秒 | 後續總秒 | 後續快取命中 | 冷可解析JSON | 輸出截斷 | 疑似輸入截斷 | API錯誤 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dflash128graph | 32768 | 32709 | 1/1/1/1/1/1/1 | 3/3/3/3/3/3/3 | 16.87 | 16.91 | 8.67 | 99.92% | True | False | False |  |
| dflash128graph | 65536 | 65472 | 1/1/1/1/1/1/1 | 3/3/3/3/3/3/3 | 40.65 | 40.70 | 7.91 | 99.96% | True | False | False |  |
| dflash128graph | 98304 | 98263 | 1/1/1/0/0/1/1 | 3/3/3/0/1/3/3 | 71.15 | 71.22 | 11.72 | 99.97% | True | False | False |  |
| dflash128graph | 122880 | 122830 | 1/1/1/1/1/0/0 | 3/2/3/2/3/0/2 | 98.54 | 98.59 | 13.22 | 99.98% | True | False | False |  |
| dflash144 | 32768 | 32709 | 1/1/1/1/1/1/1 | 3/3/3/3/3/3/3 | 16.84 | 16.84 | 9.38 | 99.92% | True | False | False |  |
| dflash144 | 65536 | 65472 | 1/1/1/1/1/1/1 | 3/3/3/3/3/3/3 | 40.50 | 40.51 | 8.50 | 99.96% | True | False | False |  |
| dflash144 | 98304 | 98263 | 1/1/1/0/0/1/1 | 3/3/3/0/1/3/3 | 71.14 | 71.16 | 12.36 | 99.97% | True | False | False |  |
| dflash144 | 122880 | 122830 | 1/1/1/1/1/0/0 | 3/2/3/2/3/0/2 | 98.63 | 98.70 | 13.84 | 99.98% | True | False | False |  |
| base256 | 32768 | 32709 | 1/1/1/1/1/1/1 | 3/3/3/3/3/3/3 | 16.43 | 16.45 | 39.42 | 0.00% | True | False | False |  |
| base256 | 65536 | 65472 | 1/1/1/1/1/1/1 | 3/3/3/3/3/3/3 | 39.78 | 39.81 | 65.78 | 0.00% | True | False | False |  |
| base256 | 98304 | 98263 | 1/1/0/1/1/1/1 | 3/3/3/2/2/1/2 | 70.10 | 70.14 | 98.72 | 0.00% | True | False | False |  |
| base256 | 122880 | 122830 | 1/1/1/1/1/0/0 | 3/2/3/3/3/0/0 | 96.17 | 96.23 | 127.11 | 0.00% | True | False | False |  |


Context原文沒有醒目的位置標籤，查找的是提問指定的普通row_ID值；跨段題需經別名指到目標，另有干擾值。JSON缺鍵也算該項未正確交付，原始回應與missing_keys可區分格式／schema失敗與內容誤答。後續請求是在同一user訊息尾端附加驗證句，不是保留assistant答案的真正多輪對話；0%命中時屬嘗試熱快取但失敗，不能稱為熱快取速度。故準確率變化不能單獨歸因給快取。真正對話另見第5.1節。

### 5.1 真正多輪對話與歷史失敗形狀的回歸

此補測保留assistant文字答案，再附加下一則user訊息；推理文字不回填，與橋接保留答案／移除舊思考的政策一致。每個配置一份約120K輸入，另測144K配置約130K的歷史資料形狀。只是一輪三步的回歸，不冒稱三次獨立重複，也不混用歷史成績。

| 配置／資料 | 步驟 | 問題 | 輸入token | 答對 | cache token | TTFT秒 | 總秒 | 結束 | 餘裕MiB |
| --- | --- | --- | --- | --- | --- | --- | --- | --- | --- |
| dflash128graph-120k | 未測試 | 啟動失敗 | — | — | — | — | — | Startup failure; group stopped: ['2026-11-03 17:14:59.426  ERROR startup failed / finalizing target / 22.1 ms', '2026-11-03 17:14:59.470  ERROR engine init / FAILED while constructing the service: requested Engine runtime reservation requires 2625894400 bytes, but only 2583916544 bytes are available for runtime capacity', '2026-11-03 17:14:59.470  FATAL server failed during startup / requested Engine runtime reservation requires 2625894400 bytes, but only 2583916544 bytes are available for runtime capacity'] | — |
| dflash144-120k | 0 | 三項明示事實 | 122856 | True | 0 | 98.33 | 100.73 | stop | 265 |
| dflash144-120k | 1 | 開頭item_000010 | 122946 | True | 122849 | 0.33 | 1.03 | stop | 295 |
| dflash144-120k | 2 | 中段item | 122992 | True | 122939 | 0.30 | 1.11 | stop | 295 |
| base256-120k | 0 | 三項明示事實 | 122856 | True | 0 | 97.34 | 102.55 | stop | 285 |
| base256-120k | 1 | 開頭item_000010 | 122946 | True | 122851 | 0.33 | 2.34 | stop | 287 |
| base256-120k | 2 | 中段item | 122992 | True | 122941 | 0.31 | 2.19 | stop | 287 |
| dflash144-historical130k | 0 | 三項明示事實 | 130427 | True | 0 | 108.02 | 109.92 | stop | 295 |
| dflash144-historical130k | 1 | 開頭item_000010 | 130517 | True | 130420 | 0.34 | 1.16 | stop | 295 |
| dflash144-historical130k | 2 | 中段item | 130563 | False | 130510 | 0.28 | 1.09 | stop | 295 |


## 6. Harness相容性與政策

- 目前橋接health：`{"status": "ok", "service": "bonsai-guard", "max_tool_calls": null}`。
- OpenCode檔位steps：`{"base256.opencode.json": null, "dflash128graph.opencode.json": null, "dflash144.opencode.json": null}`；null表示未設定，不是舊24預設。
- OpenAI工具往返：{'ok': True, 'seconds': [0.5310000000026776, 0.3120000000053551]}。
- Anthropic工具往返：{'ok': True, 'seconds': [0.26600000000325963, 0.3279999999940628]}。
- OpenCode真實任務：{'seconds': 12.687999999994645, 'exit_code': 0, 'external_pass': True, 'protected_tests_unchanged': True}。
- 串流：`{"openai": {"complete": true, "first_sse_line_s": 0.375, "total_s": 0.375, "buffered_by_bridge": true, "utf8_json_parsed": true, "expected_chinese_text_present": true}, "anthropic": {"complete": true, "first_sse_line_s": 0.5779999999940628, "total_s": 0.5939999999973224, "buffered_by_bridge": true, "utf8_json_parsed": true, "expected_chinese_text_present": true}}`。
- 同時兩請求：`{"requests": 2, "statuses": [200, 200], "client_latencies": [5.0939999999973224, 2.687999999994645], "total_s": 5.0939999999973224, "implementation": "bridge LOCK serializes generation, native max-concurrency1; not a fair/cancelable scheduler"}`。
- Responses端點狀態：404；目前不支援Responses。
- Claude Code以本輪18個任務的觀測為準，不把有限測試宣稱成全天候／多日穩定保證。防循環未停用；有些正常重複指令可能被恢復邏輯糾正，事件計數已列出。
- Hermes只做官方文件相容性分析，沒有安裝或改個人設定；候選配置與驗收步驟見[HERMES_PLAN.md](../../2026-11-03/HERMES_PLAN.md)。須使用8081、文字／工具子集、釘選實際窗口。
- 多Agent需客戶端序列佇列；橋接LOCK與引擎concurrency1限制並行，不代表具備公平排程、取消與全任務期限。

### 6.1 參數相容性的實際限制

- OpenAI小輸出上限試驗：`{"status": 200, "requested_max_tokens": 16, "requested_thinking": false, "actual_usage": {"completion_tokens": 2048, "completion_tokens_details": {"reasoning_tokens": 70}, "prompt_tokens": 60, "prompt_tokens_details": {"cached_tokens": 0}, "total_tokens": 2108}, "cap_honored": false}`。
- Anthropic小輸出上限試驗：`{"status": 200, "requested_max_tokens": 16, "actual_usage": {"cache_creation": null, "cache_creation_input_tokens": null, "cache_read_input_tokens": 0, "inference_geo": null, "input_tokens": 20, "output_tokens": 16, "output_tokens_details": {"thinking_tokens": 0}, "server_tool_use": {"web_fetch_requests": 0, "web_search_requests": 0}, "service_tier": null}, "cap_honored": true}`。
目前橋接並非所有參數原樣透傳：OpenAI路徑的思考／最小輸出預算政策可能覆蓋客戶端設定，因此Harness設定關思考或max_tokens很小，不一定真正生效。這會增加整輪等待；本輪只揭露與驗證，沒有在Benchmark途中偷偷改政策。
- OpenCode實際有效Build設定：`{"steps_present": false, "steps": null}`。原檔未設steps之外，再透過CLI agent.list確認；橋接max_tool_calls=null與這個設定屬不同層。
- 總工具額度取消不代表永遠執行：相同工具循環檢查、客戶端取消／逾時、模型輸出長度與Context仍可終止工作。工具錯誤、語意錯誤及橋接恢復應各自處理。

## 7. 三套配置建議

### 極速候選：graph128draft5

依至少三次512-token冷樣本中位數、無已記錄組錯誤篩選；這是吞吐候選，不是Coding品質冠軍。需同看256／1024、長Prompt、溫度與接受率；微小差異不足以宣稱普遍優勢。只提供獨立實驗設定，沒有覆寫穩定檔位。

### 日常Coding候選：dflash144

先比較本輪完成率，再比較包含失敗成本的每成功件耗時。樣本少、任務類型有限，僅是這組基準的候選；若兩者有失敗，不應把它當成「已能無人監督完成任意專案」。保留原dflash144作回退，必要時用搜尋縮小輸入及外部測試。

### 超長Context：base256（容量模式，品質看第5節）

256K的設定容量適合較大輸入；本輪只驗到120K資料，不宣稱整個256K都可靠。若中段／跨段找回失敗，應先檢索原文片段、引用來源與程式精確查值；不能用更大窗口掩蓋誤答。

### 7.1 實際怎麼取捨速度與窗口

| 用途 | 具體選擇 | 本輪依據 | 限制／風險 |
| --- | --- | --- | --- |
| 極速研究 | 獨立graph128draft5：131072、Graph ON、draft5、chunk256 | 短512中位220.72 tok/s；相對144K OFF約20.95% | 12/12原生啟動成功，但最低餘裕203 MiB；未做完整Coding。draft5+chunk512已啟動失敗，不推薦合併。 |
| 日常Coding | 保留dflash144：147456、Graph OFF、draft3、chunk256 | 8/9通過；全部時間/成功件154.45秒 | 含驗收及失敗成本的跨任務平均，不能取代逐任務表。仍有語意失敗；需要外部驗收。 |
| 超長輸入 | 保留base256：262144、Graph OFF、Basic、chunk256 | 短512中位85.22 tok/s | 容量優先；只測約120K與有限多輪，未驗證256K整窗可靠性。 |


**Graph主要幫Decode，長文第一輪通常卡在Prefill。** 128K Graph同題512輸出約2.64秒，128K OFF約2.91秒；32K冷輸入兩者總延遲約18.78／18.62秒，沒有相同幅度的整輪收益。

Draft5的32K Decode為161.91 tok/s，原draft3為162.77；短題較快不能推廣為所有長度較快。Chunk512的8K冷TTFT為3.20秒，chunk256為3.84秒；這是三次探索，仍需長Prompt及Coding驗證。

**配置窗口與實際工作集分開管理。** 可以保留144K容量，但日常先把相關程式碼、測試與工具輸出控制在約32K～64K；這是本輪查找表現支持的起點，不是通用安全界線。需要原文時先搜尋指定檔案／段落，保留精確來源；不要靠把整個repo與冗長測試輸出全塞進去來提升正確率。這些工作集建議尚未自動改寫到Harness。

先用「外部驗收正確完成時間」選日常模式，再用吞吐挑研究候選。虛增客戶端宣告窗口不會增加引擎容量；提高窗口也無法修復工具JSON、Shell quoting或功能語意錯誤。

## 8. 下一階段最值得測的三項

| 排序 | 項目 | 預期收益 | 風險 | 成本 |
| --- | --- | --- | --- | --- |
| 1 | 優先用Write/Edit取代巢狀Bash改檔，保留循環檢查；釐清橋接思考／輸出預算政策 | 本輪有大量工具錯誤與兩次480秒逾時，先減少重試及錯誤修改；收益未量化 | 中：工具路由與預算變更需回歸，不能移除正常工具能力 | 中 |
| 2 | 將本輪較佳Draft／Chunk候選做交替順序、等溫度重測及Coding三任務驗證 | 確認吞吐收益能否轉成任務收益 | 中：OOM、接受率依內容而變 | 中 |
| 3 | 較高精度KV或分段檢索的長文A/B，保持標準答案與位置測試 | 針對96K以上的精確找回失敗（本輪不限中段），收益未量化 | 高精度KV需更多顯存，可能犧牲容量 | 中高 |


## 9. 可重現與原始資料

依序執行（Windows PowerShell，工作目錄為本資料夾）：

```powershell
python scripts/lab.py inventory
python scripts/lab.py prompts
python scripts/fixtures.py
python scripts/calibrate.py
python scripts/lab.py benchmark --profiles dflash128graph dflash144 base256 control128off
python scripts/lab.py benchmark --profiles graph128draft2 graph128draft4 graph128draft5 --cases short:512
python scripts/lab.py benchmark --profiles graph128chunk128 graph128chunk512 --cases 8192:256
python scripts/coding.py --profiles dflash128graph dflash144 --reps 3
python scripts/context.py prep
python scripts/context.py run
python scripts/compat.py
python scripts/lab.py benchmark --profiles graph128draft5 --cases short:256 short:1024 32768:256
python scripts/lab.py benchmark --profiles graph128draft5chunk512 --cases short:512 8192:256 32768:256
python scripts/multiturn.py
python scripts/audit_coding.py
python scripts/report.py
```

inventory第一次執行會記錄當時的原始服務參數；重跑前應建立新的整份實驗資料夾，避免覆寫本輪manifest。腳本按既有key續跑，拒絕重用已改過的Coding工作目錄。不可讓兩個實驗控制器同時操作同一引擎。

- [inventory.json](../../2026-11-03/inventory.json)：實際模型／引擎雜湊與穩定Profile快照。
- [profiles/](../../2026-11-03/profiles/)：獨立設定差異，檔名control128off只變Graph，draft／chunk實驗只變對應參數。
- [prompts/](../../2026-11-03/prompts/)：完整Prompt與Context標準答案／位置。
- [fixtures/](../../2026-11-03/fixtures/)：相同起始檔、任務Prompt、外部驗收。
- [runs/](../../2026-11-03/runs/)：每次Coding實際修改結果，供人工審查。
- [raw/benchmark.jsonl](../../2026-11-03/raw/benchmark.jsonl)、[benchmark.csv](../../2026-11-03/benchmark.csv)：逐樣本數據與cache有效性。
- [raw/coding.jsonl](../../2026-11-03/raw/coding.jsonl)：CLI使用量、工具／重試／驗收。
- [raw/context.jsonl](../../2026-11-03/raw/context.jsonl)：逐位置答案與快取。
- [raw/gpu.jsonl](../../2026-11-03/raw/gpu.jsonl.gz)：250ms整卡抽樣。
- [logs/](../../2026-11-03/logs/)：每次啟動與完整引擎事件；raw內有SSE、CLI逐事件和外部測試輸出。
- [restore-check.json](../../2026-11-03/restore-check.json)：原配置還原及穩定Profile雜湊確認。

限制：LLM的自評成功不作驗收；CLI顯示的美元成本不是本機實際帳單。原始結果如有同key補測，表格採最後一筆且保留舊資料，不刪除失敗記錄。

## 10. 資源效率補表

峰值來自該Profile全部已測case，case覆蓋不同，不宜當成等工作量功耗比較。輸出token/J統一取512-token短題冷樣本，用整卡抽樣平均功率×請求秒數估算；含prefill，不是牆上電表，也不是僅Decode能耗。

| Profile | 最高使用MiB | 最低餘裕MiB | 最高°C | 最高W | 512輸出token/J |
| --- | --- | --- | --- | --- | --- |
| dflash144 | 11700 | 392 | 90 | 450.1 | 0.503 |
| dflash128graph | 11568 | 524 | 89 | 449.6 | 0.558 |
| base256 | 11562 | 530 | 90 | 450.4 | 0.212 |
| control128off | 11333 | 759 | 90 | 450.2 | 0.504 |
| graph128draft2 | 11375 | 717 | 81 | 432.9 | 0.475 |
| graph128draft4 | 11379 | 713 | 80 | 439.8 | 0.560 |
| graph128draft5 | 11889 | 203 | 87 | 447.4 | 0.633 |
| graph128chunk128 | 11351 | 741 | 81 | 439.8 | 未測試 |
| graph128chunk512 | 11461 | 631 | 81 | 448.8 | 未測試 |
| graph128draft5chunk512 | 11829 | 263 | 83 | 433.5 | 0.594 |


極速候選的512冷樣本中位數為220.72 tok/s；相對本輪128K Graph/draft3同題中位數201.79，整體配方差約9.39%。組合Profile若同時變Draft與Chunk，不能把此差歸給單一參數。此候選沒有完整Coding三任務驗證，不作日常自動Coding推薦。

日常候選本輪為8/9正式任務通過；全部任務的CLI時間合計1233.20秒。仍有失敗時，建議僅在外部驗收及人工審查下使用，不是無人監督可靠性認證。

### Draft接受率與生成效率

同一128K與Graph設定、同一512-token短Prompt；組合列另改Chunk，不能視為單獨Draft效果。接受率高不一定tok/s高，還需考慮每輪候選長度及驗證成本。

| Profile | Draft | Chunk | 冷樣本n | Decode tok/s | 接受候選數 | 提出候選數 | 接受率 | TTFT秒 |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| graph128draft2 | 2 | 256 | 3 | 174.34 | 885 | 1290 | 68.60% | 0.12 |
| dflash128graph | 3 | 256 | 3 | 201.79 | 984 | 1647 | 59.74% | 0.09 |
| graph128draft4 | 4 | 256 | 3 | 203.25 | 1002 | 2121 | 47.24% | 0.12 |
| graph128draft5 | 5 | 256 | 3 | 220.72 | 1050 | 2409 | 43.59% | 0.09 |
| graph128draft5chunk512 | 5 | 512 | 1 | 215.37 | 350 | 803 | 43.59% | 0.11 |


### 方法補充與校準

- 初始原生A按固定Profile順序執行，沒有完全等溫或隨機化順序；後續短題補測、Draft／Chunk、Coding與Context加上起跑前≥80°C降至≤72°C的等待。功耗上限450W是機器原有設定，沒有被本實驗更改；驅動預設400W、最高工作93°C、降速95°C見[thermal-environment.txt](../../2026-11-03/thermal-environment.txt)。不同熱階段不可當成嚴格單因果百分比。
- 熱快取Prefill速率只用剩餘未快取token計算；少數尾端token除以固定開銷，不能拿它和冷快取整段吞吐直接比較。
- Coding使用固定英文Prompt和受控工具允許清單；不含GUI、外部服務或大型第三方依賴。Shell命令遭拒與escaping錯誤是本輪Harness／模型組合的實際成本，但不代表所有日常權限政策都相同。
- Coding每次最多480秒是本實驗的監督逾時，不是正式橋接或OpenCode的新上限。原始測試及[校準](../../2026-11-03/grader-calibration.json)保留。
- 重構第一個pilot對parse_money新helper精度描述不夠明確；原9/10結果與原Prompt保留，補明Prompt後補足兩個配置各三次。驗收標準沒有為了通過而放寬。見[protocol-amendment.json](../../2026-11-03/protocol-amendment.json)。
- 設定的增加／刪除／變更差異見[profile-differences.json](../../2026-11-03/profile-differences.json)。


### 完整逐次匯出與最後稽核

- [coding.csv](../../2026-11-03/coding.csv)：正式Coding逐次結果，包括失敗、工具錯誤、token與資源。
- [context.csv](../../2026-11-03/context.csv)：每次查找的逐位置真假、實際cache分類與延遲。
- [raw/coding-audit.jsonl](../../2026-11-03/raw/coding-audit.jsonl)：逾時與完整工具計數的稽核資料。
- [raw/multiturn.jsonl](../../2026-11-03/raw/multiturn.jsonl)：保留真實assistant/user歷史的獨立回歸。
- [FINALIZED.json](../../2026-11-03/FINALIZED.json)：所有測試結束後的服務、模型、設定及原repo一致性稽核。
- [script-manifest.json](../../2026-11-03/script-manifest.json)：本輪實際交付腳本雜湊。
正式環境仍走8081；8080僅供本輪引擎層Benchmark。重跑範例應先確認沒有正式任務，並只啟動一個控制器。報告沒有把未測的144K Graph ON重新宣稱安全，也沒有測滿256K、安裝Hermes或做多日不中斷驗證。

