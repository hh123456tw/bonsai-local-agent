# Hermes／其他Harness接入方案（分析，未安裝）

2026-11-03查閱[Hermes官方Provider文件](https://hermes-agent.nousresearch.com/docs/integrations/providers)。文件支援具名自訂Provider，明確指定Chat Completions或Anthropic Messages傳輸，以及context_length。這表示協定上可行，但不是本機Hermes已實測通過。

建議優先走既有8081的OpenAI Chat Completions。候選設定如下，僅作文件，未寫入個人Hermes設定：

```yaml
providers:
  bonsai-local:
    api: http://127.0.0.1:8081/v1
    transport: chat_completions
    api_key: local
    default_model: bonsai2-27b
    context_length: 131072
model:
  provider: bonsai-local
  default: bonsai2-27b
  context_length: 131072
```

窗口必須隨實際引擎檔位調整，不可宣告比引擎更大。Hermes文件指出可明確釘選窗口；metadata辨識不符時應先校正，而不是提高虛擬宣告來繞過容量檢查。Messages傳輸也可另建Provider，以根URL `http://127.0.0.1:8081` 接入，仍需安裝後驗證，不能把Chat URL直接當Messages根URL。

本橋接提供文字、客戶端工具、工具結果與緩衝SSE；不提供Responses、圖片、文件或雲端內建工具。未來接入應避免啟動Hermes自管模型引擎，避免另下載模型；輔助模型、壓縮、fallback也要確認沒有跑到未授權的雲端服務。

批准安裝後的驗收順序：先models與基本聊天，再檢查工具JSON與tool_result，多輪文件修改、外部測試、SSE結尾、取消／超時與長任務。用相同三個Coding fixture比較Harness成本與成功率，不能只測一句問候就認定相容。

Windows原生／WSL的支援路徑、Shell命令、磁碟路徑轉換與工具權限仍需在批准安裝後驗證；目前不宣稱Windows版Hermes已能直接操作這台電腦的專案。

多Agent先由Harness或外部工作佇列序列派發。本橋接的LOCK可阻止生成並行，但不是公平、具取消／期限管理的排程器；大量客戶端同時排隊可能超時，也會造成前綴互相逐出。引擎仍維持max-concurrency1；不增加GPU並發來假裝多Agent加速。

其他開源Harness亦以「是否可指定Chat Completions／Messages、完整工具回傳、是否強制Responses」逐項驗收；不在未安裝的情況下宣稱特定客戶端全面相容。
