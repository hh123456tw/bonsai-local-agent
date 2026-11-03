# 輸出與思考預算：本機橋接的實際行為

OpenAI Chat Completions使用`http://127.0.0.1:8081/v1`；正式Agent仍經8081防護。這次修正適用OpenAI路徑，沒有更動三套引擎／OpenCode穩定Profile，也沒有取消重複工具檢查。

## 輸出上限

- `max_tokens`或`max_completion_tokens`接受1～32768的整數；未指定時仍是16384。
- 明確的小額度原樣轉送，不再提高成2048。兩個欄位同時提供時必須相等。
- 0、負數、布林值、字串、null、超過32768或互相矛盾的額度，回HTTP 400；不默默增加或縮減。
- 此額度包含模型的思考與答案／工具輸出，不是額外再加一份思考額度。

例如需要極短文字回覆：

```json
{
  "model": "bonsai2-27b",
  "messages": [{"role": "user", "content": "Explain Python unit testing in detail."}],
  "max_tokens": 16,
  "enable_thinking": false
}
```

這個案例修正前實際輸出2048 token、約11秒；修正後輸出16 token、無思考，單次約0.42秒。短測的後續請求約0.14～0.36秒；這是減少未要求的生成量，不能當成引擎吞吐提升或一般任務加速倍數。

## 思考

- `enable_thinking:false`會維持關閉，轉送`thinking_budget:0`；糾正重試不會重新開啟。
- 明確啟用時，本機引擎要求思考預算至少1024；現行防護上限維持1536。明確的合法`thinking_budget`會保留，不再一律改成1536。
- 預算校驗另外保留至少256個輸出token，因此顯式啟用思考至少需要1280總額度。這個保留量不保證任何長工具JSON都能容納。
- 沒指定開關／思考額度時，總輸出小於1280則自動關思考；較大輸出預設開思考，預算為`min(1536, max_tokens - 256)`。一般16384輸出請求的原預設維持不變。
- 未指定開關時，`thinking_budget:0`表示關閉；正值表示明確要求思考。矛盾或不足的組合回HTTP 400，請由客戶端明確調整。

Anthropic Messages原本的小輸出上限仍有效；它的思考準備政策沿用既有設定。本輪沒有宣稱兩種協定的所有思考欄位都完全透明或互相等價。

## 工具輸出太小時

工具JSON也會消耗輸出額度；不要把16 token當成Coding工具回應的通用上限。

- 一般文字用完額度，保留HTTP 200與`finish_reason:"length"`，串流照常有結尾及usage。這不表示回答已完成。
- 空白且已達長度上限的回應不再觸發三次空答案恢復；加長預算應由客戶端決定。
- 工具批次達到長度上限，或工具參數不是完整JSON物件，回HTTP 502並阻止整批工具放行。OpenAI錯誤碼為`tool_output_truncated`或`invalid_tool_arguments`。
- 不會為了讓工具過關而自動突破客戶端額度。正常重複工具的糾正最多兩次，總工具次數仍由`guard-config.json`控制，目前為null。

這裡檢查的是JSON完整性及物件型態，並非任意JSON Schema或程式語意的正確性；實際權限、參數驗證與執行仍由Harness負責。

## Claude Code改檔指引

新開的本機Claude Code預設追加簡短工作指引：先確認需求及相容性，優先Read／Edit／Write，避免巢狀Bash/python -c改檔，遇錯誤先讀輸出並改變做法，最後逐項核對需求並跑測試。它不改工具允許清單，不新增權限，也不保證模型一定遵守。

若使用者自行提供`--append-system-prompt`或其檔案版本，啟動器保留使用者覆寫。已開著的CLI不會自動收到新指引；請完成目前工作後，從原本桌面捷徑重新開啟。OpenCode與Hermes可使用新的API預算行為，但沒有被自動注入這份Claude專用指引。

## 驗證

```powershell
python -m unittest discover -s tests
```

測試包含請求實際轉送值、矛盾預算的HTTP 400、截斷／無效工具的HTTP 502、SSE結尾與usage，以及原防循環和工具額度回歸。GPU實測與Coding比較另存於這次改善報告，與舊Benchmark分開保存。
