# 執行紀錄與待辦

**2026-11-03 17:26 完成。** 最終交付為REPORT.md、benchmark.csv、coding.csv、context.csv；FINALIZED.json與artifact-validation.json已通過。以下保留的是執行期間紀錄，其中「待辦」已完成或明確記錄為未測試，不應重新啟動控制器。

補測已完成：128重構正式三次均通過；Draft5完成256／512／1024及32K確認；Draft5+Chunk512第二次啟動顯存預留不足而停止。真正多輪回歸中，128Graph因當時顯存不足而未測，144K及Basic在120K均通過三步，144K約130K的中段追問誤答。正式Coding為144K 8/9、128Graph 6/9，未把原pilot混入。原模型、六份穩定Profile、防循環及正式repo完整保留，服務已恢復147456／Graph OFF／draft3，max_tool_calls維持null，OpenCode steps未設定。沒有發布、推送或安裝新Harness。

- 輸出位置：`outputs/bonsai-evaluation-20261103`；正式repo另在`outputs/bonsai-local-agent`，沒有在正式原始碼上執行修改測試。
- 三套穩定Profile只讀快照，六份engine／OpenCode檔案SHA列於inventory.json。模型SHA為cdc4810b0ff17c40d0f62cf214b6e0bcd08346e9eb05ca53371507037793c14a；引擎為cd6be5e8ca872a1044aaab4c219be38d2787ee852429e2dd9b073e635dcf5d3f。
- 原配置為147456、Graph OFF、draft3、prefill256、host4096；每個控制器finally會還原此argv、驗證穩定檔案及engine-options未改。
- 本輪功耗上限原本450W（驅動預設400W），沒有改硬體設定。最高工作93°C、降速95°C；初始A最高觀測約89°C，spot checks沒有硬體thermal slowdown。後續流程起跑前≥80°C則等≤72°C。
- 原生A四組已完成：128Graph、144OFF、256Basic、同128GraphOFF控制。輸出256／512／1024及8K／32K／64K／96K，每組三次cold與hot；冷快取以重啟驗證。短Prompt第一版45token未命中快取，原資料留raw/superseded-short，128短題已用共同新Prompt補測，報告按Prompt SHA排除舊版。
- Draft2／4／5的512-token探索及Chunk128／512的8K探索已完成。其餘完整資料在raw/benchmark.jsonl；同key最後一筆為補測版本，舊JSONL紀錄不刪除。
- 自動控制器scripts/run_remaining.py等待初始native程序36760結束後，依序跑short-recheck、draft-scan、chunk-scan、coding、context-prep、context、compatibility。它已在背景執行；不要同時啟動另一個會切引擎的控制器。進度見raw/phases.jsonl及logs/*.stdout。
- Coding兩配置×三任務×三輪，CLI經8081。每次全新runs目錄，480秒監督逾時，這不是正式服務的新工具上限。已取消的總工具限制維持null，防重複工具原樣。
- Task1起始公開測試有3個失敗；Task2及3起始既有測試通過。校準器確認三個起始專案均無法通過外部驗收，參考實作通過4／9／10項；grader-calibration.json留檔。
- **Task3方法修訂**：第一個128-refactor-0對parse_money回傳精度的Prompt不夠明確，列pilot，原9/10結果不變。補明新helper精度後，其他refactor使用新Prompt。舊Prompt存prompts/refactor-pilot-v1.txt，SHA與原run一致；驗收沒有放寬。正式報告按新Prompt SHA篩選。
- **最後必須補跑**：所有自動階段結束後，執行`python scripts/coding.py --profiles dflash128graph --reps 1 --tasks refactor --rep-offset 3`，補足128組三次正式重構。不要重用舊工作目錄。
- 可再確認極速候選：目前Draft5的512-token約221 tok/s，但仍需256／1024及32K補測。用`lab.py benchmark --profiles graph128draft5 --cases short:256 short:1024 32768:256`，每個case自動三次冷熱。這不會將候選部署成日常檔位。
- Context：32K／64K／96K／120K，一個冷資料集加三次相同前綴追問。查找的是普通row_ID的隨機hash（沒有額外特殊needle標籤），另有兩跳關聯與干擾值；記錄可解析JSON與精確找回，不能把相依追問算作獨立冷資料集。
- Harness：compat.py只走8081，測兩種協定工具往返／SSE／序列排程／實際OpenCode Bug任務，並讀有效agent.list確認steps缺省。Hermes僅分析官方文件，不安裝；HERMES_PLAN.md有候選設定。
- 逾時CLI缺結案用量時，scripts/audit_coding.py以CLI逐事件重建工具數，並以工作時間窗內engine done日誌統計完成RPC的token與guard events；不虛構terminal usage。也會在逾時後補做外部驗收，但不把逾時改判成功。
- 收尾：補跑重構、極速候選確認→audit_coding.py→檢查每任務各三次正式資料與所有錯誤→驗證model／stable profiles／repo未改、服務回原配置→寫FINALIZED.json→report.py。原始日誌保留，不發布網站。
