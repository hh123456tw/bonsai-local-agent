# 已完成：API預算與Coding工具改善

**最終完成說明：** 三組各九次均已完成並稽核：通用144K9/9、Windows指引7/9、Draft5為8/9。依事前規則選通用指引，未套用Windows提示，日常仍147456／GraphOFF／draft3。真實Root Claude啟動器20.719秒及OpenCode13.047秒，兩者新Bug專案外部驗收通過且保護檔未改。FINALIZED.json已通過模型／引擎SHA、六份穩定Profile、實際argv與原引擎參數、防循環與部署一致性；35項unit／HTTP及dry-run再驗證通過。下列「進行中／待辦」保留為歷史工作紀錄，不能據此重啟測試或套用失敗變體。完整結論以REPORT.md為準。

權限審計另發現Windows實驗曾提出pip升級複合命令，被工具預檢以「can't be checked before it runs」拒絕，未執行，沒有放寬權限。這不是已完成下載。CI核心修正3ab5cc6已success；剩餘步驟僅整理、驗證並推送資料文件，網站不發布。

**最新進度（接續時先看這段）：** 核心修正已commit/push為3ab5cc687e6ba82feef4be694e80f710d12009a3，GitHub Actions41625773526已success。Main controller session8402已結束；Draft5完整8/9，1806.564秒、225.8205秒／成功件、411工具／120工具錯誤，feature-2逾時480秒，發生一次客戶端自動壓縮（pre77314、post6863、74.145秒）。通用144K9/9已確定是日常候選。Windows controller session10689目前剩最後一個refactor-2，前八次7pass／1timeout，因此不可能勝過通用組9/9；不得再加新變體挑分。Root launcher仍是通用GUIDANCE，沒有套用Windows版。

補完的工具：select_guidance.py --apply（Generic勝出時會保留原字串格式不重寫）、clients_smoke.py（實際Root啟動器＋OpenCode）、finalize.py（必須等兩client驗收後才跑）。Finalizer及測試腳本已寫，但尚未執行最終驗收。audit_version目前3，含max_request_prompt_tokens、JSON拒絕與API重試。usage_probe.py產生compaction-analysis.json；context_coverage.py記錄實際輸入／壓縮。通用144K最大單次41754、Draft5最大73812；兩組cache約94.1%／93.4%，沒有API retry。Anthropic input/cache正確分列，未發現重複計數，不可虛構為bug。

新的packaging工具已準備：work/package_agent_improvement.py、work/verify_agent_improvement_commit.py，仍未執行。Repo目前HEAD3ab5cc6、核心已推；後續只需新資料夾與README/HTML最終摘要、gitignore/attributes資料例外，再第二個commit/push。Package目的docs/evaluations/2026-11-03-agent-improvement。注意packaged baseline/REPORT相對連結也會改寫至../../2026-11-03/，不是刪掉歷史。Source scripts/default JSON reads已批次改成UTF8。Core runtime沒有再改。

這是工作紀錄，REPORT.md在FINALIZED.json存在之前仍為草稿。不要同時啟動兩個會操作模型的控制器。

## 已完成

- 原repo為outputs/bonsai-local-agent，HEAD4f5259e；本輪runtime／tests／docs改動尚未commit/push。
- 實機重現OpenAI max_tokens16、enable_thinking false卻輸出2048／thinking63，約10.969秒；證據raw/budget-before.stdout及stderr。
- 已修runtime/bonsai_proxy.py並部署C:/AI/bonsai。現在16token／thinking0，單次0.422秒；14項實機API案例通過。引擎思考最小1024，衝突預算先400；顯式小輸出不膨脹；截斷／無效工具JSON整批不放行、502；空白length不重試；恢復不重新開啟思考。max_tool_calls仍null。
- 35項unit/HTTP回歸通過；install.py --dry-run通過。源碼未再變更，尚需最終選指引後實際launcher／OpenCode冒煙驗證。
- 本輪僅重啟自有proxy，沒動模型／引擎／穩定Profile。baseline/runtime保留原部署；rollback是中間版本。
- runtime/claude_launch.py預設追加通用改檔指引。已部署的GUIDANCE是GENERIC版本，原權限未放寬。自帶append-system-prompt的使用者覆寫保留。
- 通用指引144K九次全部通過：1441.407秒，含失敗攤提160.156秒／成功件，312工具、75工具錯誤。歷史144K控制8/9：1235.626秒，154.453秒／成功件，321工具、88錯誤。不能說整體已加速。
- 因重構一回反覆使用python3、/tmp、/usr/bin且13次需授權，另設Windows具體環境指引組。不是中途更改原組，也沒有放寬Bash權限。

## 活動控制器（只能循序）

1. run_study.py，PID32208，exec session8402：通用指引144K已結束及稽核；目前跑graph128draft5九次Coding。達8/9的品質門檻後才測Draft5。第一個啟動失敗即停止該Profile；不降低Context。
2. run_windows.py 32208，exec session10689：等上項整個controller結束後，自動以dflash144windows（三套原Profile之外的獨立byte-identical144K快照）跑三任務各三次，再audit。開始前已寫windows-protocol.json。

GUIDANCE已在scripts/guidance_versions.py凍結：GENERIC_GUIDANCE對應第一組與Draft5；WINDOWS_GUIDANCE是新組。每個run保存實際guidance及SHA，使用者任務Prompt／fixture／外部驗收保持原樣。原第一組runner另存baseline/coding-guidance-v1-runner.py。兩個控制器完成前不要改C:/AI/bonsai/claude_launch.py的常數。

## 待辦

1. 等兩個controller全部結束，檢查logs/*.stdout/stderr、raw/coding.jsonl及coding-audit.jsonl。用scripts/live_status.py看目前呼叫數，不修改測試專案。
2. scripts/select_guidance.py --apply：只在兩組144K各九次已完成後執行。先比完成件數，同數時要求至少10%較低的含失敗秒／成功件才替換；對照歷史baseline。會保存tested-runtime並原子更新自有launcher，三套引擎／OpenCodeProfile不變。
3. 選完後跑scripts/clients_smoke.py：原本真實Claude啟動器及OpenCode，在新bug專案外部驗收。不可與上方GPU控制器並行。
4. scripts/report.py產生草稿／coding.csv／tool-mix／error-analysis；來源與新舊樣本分開。若Root常數變成Windows，原GENERIC實驗仍靠凍結的guidance_versions可重跑。
5. 寫finalize.py並驗證：模型與engine SHA、六份穩定Profile、engine-options及實際運行argv都回原144K／GraphOFF／draft3；guard-config未改；proxy部署同repo原碼；fixture／外部grader／userprompt一致；每組三次；guard停止不能被報成功。記錄35項unit與dry-run、客戶端驗收。
6. 寫FINALIZED.json後再report.py，移除草稿。補report加入Windows組、實際指引決策、Draft5穩定性與溫度、API/CLI重試欄位（audit_version2已記錄新guard_tool_rejections／output_truncations／client_api_retry_events）。
7. 更新docs/api-budget.zh-TW.md、README及本機HTML的最終數字與指引預設。若baseline勝出，啟動器應回舊預設；select_guidance會把新指引改成--edit-first opt-in。若generic/windows勝出則預設追加勝出者。
8. 將本輪資料新增到repo docs/evaluations/2026-11-03-agent-improvement（舊資料不可改）。壓縮*.sse及raw/gpu.jsonl，排除claude-home、__pycache__、.pytest_cache、calibration；原始模型及引擎不入Git。參考work/publish_evaluation.py與verify_evaluation_commit.py，但不能覆寫舊資料夾。新目錄需自己的.gitignore JSONL/log例外及.gitattributes -text -whitespace，以保留歷史雜湊。
9. 套件報告的上一輪連結改成../2026-11-03/REPORT.md。完整manifest、gzip無損、staged bytes、穩定設定未更動及秘密樣式掃描驗證；commit/push到原私人repo main（此前已授權push，本輪使用者說做）。確認remote HEAD與clean tree。不發布網站。

如果跨對話接續，以上進度屬同一任務；不要重跑已完成的組別或刪掉失敗結果。
