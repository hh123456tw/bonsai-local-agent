"""Additional measured summaries, exports and interpretation for report.py."""
import csv,json,statistics
from lab import LAB,existing

def enhance(lines,bench,good,coding,contexts,meta,speed,daily):
 from report import mdtable,fmt,median,subset,load
 edits={
  '熱欄是同資料三次追問':'後續欄是同資料三次重送',
  '固定代表性專案做更長的Coding驗收；縮小無關讀檔與工具輸出':'優先用Write/Edit取代巢狀Bash改檔，保留循環檢查；釐清橋接思考／輸出預算政策',
  '改善真正完成時間與正確率；非本輪已量化收益':'本輪有大量工具錯誤與兩次480秒逾時，先減少重試及錯誤修改；收益未量化',
  '中：檢索漏掉相關檔案':'中：工具路由與預算變更需回歸，不能移除正常工具能力',
  '針對Lost in the Middle，可能改善正確性':'針對96K以上的精確找回失敗（本輪不限中段），收益未量化',
 }
 for i,line in enumerate(lines):
  for old,new in edits.items():line=line.replace(old,new)
  lines[i]=line
 for i,line in enumerate(lines):
  if line.startswith('含失敗攤提＝'):
   lines[i]+=' 主比較時間包含CLI讀寫／工具／測試及外部驗收、公開測試和逾時收尾；不含建置fixture、引擎啟動或降溫。逐次表「秒」另列CLI本身耗時，coding.csv同時保留兩種時間。'
 def export(name,rows):
  if rows:
   with (LAB/name).open('w',encoding='utf-8-sig',newline='') as f:
    w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
 def insert_before(marker,extra):
  i=next(i for i,x in enumerate(lines) if x.startswith(marker));lines[i:i]=extra
 def rate(p):return median(subset(good,profile=p,case='short',output_limit=512,cache='cold'),'timings.predicted_per_second')
 groups={p:subset(coding,profile=p) for p in ('dflash128graph','dflash144')}
 counts={p:(sum(bool(x.get('passed')) for x in g),len(g)) for p,g in groups.items()}
 cg=rate('dflash128graph');off=rate('control128off');sp=rate(speed)
 insert_before('## 1.',[
  '## 先看結論','',
  f'- **日常Coding暫選{daily}**：144K OFF完成{counts["dflash144"][0]}/{counts["dflash144"][1]}，128K Graph完成{counts["dflash128graph"][0]}/{counts["dflash128graph"][1]}。只代表這三個小型Python任務的結果；仍需外部測試與審查。',
  f'- **極速只列實驗候選{speed}**：512-token短題冷樣本中位數{fmt(sp)} tok/s；原128K Graph/draft3為{fmt(cg)}，144K OFF為{fmt(rate("dflash144"))}。尚未把這個新候選部署為日常配置。',
  f'- **同128K控制組**：Graph ON {fmt(cg)}、OFF {fmt(off)} tok/s，觀測差{fmt((cg/off-1)*100) if cg and off else "未測試"}%；測試順序與熱條件未完全控制，不視為精確因果估計。',
  '- **大窗口不等於可靠長文記憶**：DFlash兩組在32K／64K這組七項查找全對，96K起出現誤答；這次常見於後段及結尾，不能籠統歸為中段遺忘。256K模式仍只驗到約120K輸入。',
  '- 三套原穩定Profile保留；未增加正式工具總次數限制、未停用防循環、未安裝Hermes。所有改動與測試只在獨立實驗資料夾。',''])
 origin=load('engine-origin.json')
 startup_failures=[x for x in existing('startups') if not x.get('ready')]
 insert_before('## 4.',[
  '', '### 3.3 所有階段的啟動失敗','',
  '總覽的啟動成功數包含A／B／C／補測各階段；餘裕及溫度欄只匯總原生A請求抽樣。Coding／多輪的最低餘裕另列。失敗時未反覆重啟同一組來挑成功值。', '',
  mdtable(['Profile','階段標籤','錯誤'],[[x['profile'],x['tag'],'; '.join(x.get('errors',[]))] for x in startup_failures]) if startup_failures else '沒有已記錄的啟動失敗。',''])
 insert_before('## 2.',[
  f'引擎來源：安裝器釘選雜湊與[engine-v0.11.0-kvmem-20261008的sm86資產]({origin.get("url","")})一致。這是可追溯的發行資產標籤；二進位本身沒有提供完整commit/build字串。',
  '模型檔9,520,051,456 bytes＝9.520 GB＝8.866 GiB。這是本機實際v3檔案大小，並非7GB多；不能把其他模型版本、打包大小或載入時顯存占用當成此檔大小。',''])
 # CSV exports preserve per-run measurements, including failed runs.
 cr=[]
 for x in coding:
  g=x.get('gpu',{});a=x.get('acceptance',{});e=x.get('engine_usage',{})
  cr.append({'run':x['key'],'profile':x['profile'],'task':x['task'],'passed':x.get('passed',False),'cli_seconds':x.get('agent_latency_s'),'total_with_validation_seconds':x.get('task_total_s'),'tool_calls':x.get('tool_calls'),'tool_errors':x.get('tool_errors'),'consecutive_repeats':x.get('consecutive_repeat_count'),'all_duplicate_calls':x.get('nonconsecutive_duplicate_count'),'guard_recoveries':x.get('guard_recoveries'),'guard_stops':x.get('guard_stops'),'engine_requests':e.get('completed_requests'),'input_tokens_including_cached':e.get('input_tokens_total'),'cached_input_tokens':e.get('cached_input_tokens'),'output_tokens':e.get('output_tokens'),'external_tests':a.get('tests'),'external_failures':a.get('failures'),'external_errors':a.get('errors'),'protected_changed':json.dumps(x.get('protected_files_changed',[])),'vram_used_max_mib':g.get('used_mib_max'),'vram_free_min_mib':g.get('free_mib_min'),'temperature_max_c':g.get('temp_c_max'),'power_max_w':g.get('power_w_max'),'error':x.get('error','')})
 export('coding.csv',cr)
 cx=[]
 for x in contexts:
  for r in x.get('rounds',[]):
   t=r['timings'];g=r.get('gpu',{})
   cx.append({'profile':x['profile'],'target':x['target'],'rep':r['rep'],'correct':sum(r['correct_by_key'].values()),'total_items':7,'actual_input_tokens':r['usage'].get('prompt_tokens'),'cached_tokens':t.get('cache_n',0),'cache_fraction':r['cache_hit_fraction'],'cache_category':'cold' if r['rep']==0 else ('cache_hit' if t.get('cache_n',0) else 'hot_attempt_cache_miss'),'prefill_s':t.get('prompt_ms',0)/1000,'ttft_s':r.get('ttft_observed_s'),'total_s':r['latency_s'],'json_valid':r.get('json_format_valid'),'output_truncated':r.get('finish_reason')=='length','vram_free_min_mib':g.get('free_mib_min'),'temperature_max_c':g.get('temp_c_max'),**r['correct_by_key']})
 export('context.csv',cx)
 insert_before('## 5.',[
  '### 4.1 失敗是怎麼發生的','',
  '- 128K Graph的feature三次皆未完成：兩次到480秒監督逾時，另一回外部驗收8/9，新增報表把pending款項納入USD總額（5.40而非1.00）。逾時後一回測試檔有SyntaxError，另一回模組匯入缺少normalize_currency；不把逾時的半成品判成功。',
  '- 144K OFF的feature完成2/3，失敗那回同樣把pending款項算進報表。這是語意錯誤，單靠更快Decode或增加Context不能保證修好。',
  '- 重構中可見Bash quoting與受控權限造成多次錯誤／重試。工具輸出中的錯誤次數並非全部是循環；準確連續重複、跨步重用、橋接恢復和最終驗收分開記錄。',
  '- CSV的all_duplicate_calls及Markdown「全部重用」包含連續及非連續相同呼叫，是所有重複簽章額外次數。重用可為正常重跑測試，不能直接等同鬼打牆。',
  '- 每組只有三次，任務和模型路徑差異可能影響結果；本輪不能證明Graph本身導致程式品質下降。完整修改及外部測試輸出均可稽核。',''])
 mt=list({x['key']:x for x in existing('multiturn')}.values());mr=[]
 for x in mt:
  if not x.get('rounds'):
   mr.append([x['key'],'未測試','啟動失敗','—','—','—','—','—',x.get('error','未執行'),'—'])
  for r in x.get('rounds',[]):
   if r['step']==0:
    try:obj=json.loads(r['text'][r['text'].index('{'):r['text'].rindex('}')+1]);correct=all(obj.get(k)==v for k,v in zip(('SECRET_ALPHA','SECRET_BETA','SECRET_GAMMA'),r['expected']))
    except (ValueError,TypeError):correct=False
   else:correct=r['text'].strip().strip('`\"\' ')==r['expected'][0]
   mr.append([x['key'],r['step'],'三項明示事實' if r['step']==0 else ('開頭item_000010' if r['step']==1 else '中段item'),r['usage'].get('prompt_tokens'),correct,r['timings'].get('cache_n',0),fmt(r.get('ttft_observed_s')),fmt(r['latency_s']),r.get('finish_reason'),fmt(r.get('gpu',{}).get('free_mib_min'),0)])
 insert_before('## 6.',[
  '### 5.1 真正多輪對話與歷史失敗形狀的回歸','',
  '此補測保留assistant文字答案，再附加下一則user訊息；推理文字不回填，與橋接保留答案／移除舊思考的政策一致。每個配置一份約120K輸入，另測144K配置約130K的歷史資料形狀。只是一輪三步的回歸，不冒稱三次獨立重複，也不混用歷史成績。', '',
  mdtable(['配置／資料','步驟','問題','輸入token','答對','cache token','TTFT秒','總秒','結束','餘裕MiB'],mr) if mr else '未測試（待前述實驗結束後執行）。',''])
 compat=load('compatibility.json')
 insert_before('## 7.',[
  '### 6.1 參數相容性的實際限制','',
  f'- OpenAI小輸出上限試驗：`{json.dumps(compat.get("openai_small_output_cap","未測試"),ensure_ascii=False)}`。',
  f'- Anthropic小輸出上限試驗：`{json.dumps(compat.get("anthropic_small_output_cap","未測試"),ensure_ascii=False)}`。',
  '目前橋接並非所有參數原樣透傳：OpenAI路徑的思考／最小輸出預算政策可能覆蓋客戶端設定，因此Harness設定關思考或max_tokens很小，不一定真正生效。這會增加整輪等待；本輪只揭露與驗證，沒有在Benchmark途中偷偷改政策。',
  f'- OpenCode實際有效Build設定：`{json.dumps(compat.get("opencode_effective_build","未測試"),ensure_ascii=False)}`。原檔未設steps之外，再透過CLI agent.list確認；橋接max_tool_calls=null與這個設定屬不同層。',
  '- 總工具額度取消不代表永遠執行：相同工具循環檢查、客戶端取消／逾時、模型輸出長度與Context仍可終止工作。工具錯誤、語意錯誤及橋接恢復應各自處理。',''])
 dailyg=groups.get(daily,[]);success=[r for r in dailyg if r.get('passed')]
 default8=subset(good,profile='dflash128graph',case='8192',cache='cold');chunk8=subset(good,profile='graph128chunk512',case='8192',cache='cold')
 draftlong=subset(good,profile='graph128draft5',case='32768',cache='cold');standardlong=subset(good,profile='dflash128graph',case='32768',cache='cold')
 insert_before('## 8.',[
  '### 7.1 實際怎麼取捨速度與窗口','',
  mdtable(['用途','具體選擇','本輪依據','限制／風險'],[
   ['極速研究','獨立graph128draft5：131072、Graph ON、draft5、chunk256',f'短512中位{fmt(sp)} tok/s；相對144K OFF約{fmt((sp/rate("dflash144")-1)*100) if sp else "未測試"}%','12/12原生啟動成功，但最低餘裕203 MiB；未做完整Coding。draft5+chunk512已啟動失敗，不推薦合併。'],
   ['日常Coding','保留dflash144：147456、Graph OFF、draft3、chunk256',f'{len(success)}/{len(dailyg)}通過；全部時間/成功件{fmt(sum(x.get("task_total_s",480) for x in dailyg)/len(success) if success else None)}秒','含驗收及失敗成本的跨任務平均，不能取代逐任務表。仍有語意失敗；需要外部驗收。'],
   ['超長輸入','保留base256：262144、Graph OFF、Basic、chunk256',f'短512中位{fmt(rate("base256"))} tok/s','容量優先；只測約120K與有限多輪，未驗證256K整窗可靠性。']]),'',
  f'**Graph主要幫Decode，長文第一輪通常卡在Prefill。** 128K Graph同題512輸出約{fmt(median(subset(good,profile="dflash128graph",case="short",output_limit=512,cache="cold"),"latency_s"))}秒，128K OFF約{fmt(median(subset(good,profile="control128off",case="short",output_limit=512,cache="cold"),"latency_s"))}秒；32K冷輸入兩者總延遲約{fmt(median(standardlong,"latency_s"))}／{fmt(median(subset(good,profile="control128off",case="32768",cache="cold"),"latency_s"))}秒，沒有相同幅度的整輪收益。', '',
  f'Draft5的32K Decode為{fmt(median(draftlong,"timings.predicted_per_second"))} tok/s，原draft3為{fmt(median(standardlong,"timings.predicted_per_second"))}；短題較快不能推廣為所有長度較快。Chunk512的8K冷TTFT為{fmt(median(chunk8,"ttft_observed_s"))}秒，chunk256為{fmt(median(default8,"ttft_observed_s"))}秒；這是三次探索，仍需長Prompt及Coding驗證。', '',
  '**配置窗口與實際工作集分開管理。** 可以保留144K容量，但日常先把相關程式碼、測試與工具輸出控制在約32K～64K；這是本輪查找表現支持的起點，不是通用安全界線。需要原文時先搜尋指定檔案／段落，保留精確來源；不要靠把整個repo與冗長測試輸出全塞進去來提升正確率。這些工作集建議尚未自動改寫到Harness。', '',
  '先用「外部驗收正確完成時間」選日常模式，再用吞吐挑研究候選。虛增客戶端宣告窗口不會增加引擎容量；提高窗口也無法修復工具JSON、Shell quoting或功能語意錯誤。',''])
 # Reproduction must include all supplemental experiments, not only exploration.
 ix=lines.index('python scripts/compat.py')
 lines[ix+1:ix+1]=[
  'python scripts/lab.py benchmark --profiles graph128draft5 --cases short:256 short:1024 32768:256',
  'python scripts/lab.py benchmark --profiles graph128draft5chunk512 --cases short:512 8192:256 32768:256',
  'python scripts/multiturn.py','python scripts/audit_coding.py']
 ix=lines.index('python scripts/fixtures.py');lines[ix+1:ix+1]=['python scripts/calibrate.py']
 lines += ['','### 完整逐次匯出與最後稽核','',
  '- [coding.csv](coding.csv)：正式Coding逐次結果，包括失敗、工具錯誤、token與資源。',
  '- [context.csv](context.csv)：每次查找的逐位置真假、實際cache分類與延遲。',
  '- [raw/coding-audit.jsonl](raw/coding-audit.jsonl)：逾時與完整工具計數的稽核資料。',
  '- [raw/multiturn.jsonl](raw/multiturn.jsonl)：保留真實assistant/user歷史的獨立回歸。',
  '- [FINALIZED.json](FINALIZED.json)：所有測試結束後的服務、模型、設定及原repo一致性稽核。',
  '- [script-manifest.json](script-manifest.json)：本輪實際交付腳本雜湊。',
  '正式環境仍走8081；8080僅供本輪引擎層Benchmark。重跑範例應先確認沒有正式任務，並只啟動一個控制器。報告沒有把未測的144K Graph ON重新宣稱安全，也沒有測滿256K、安裝Hermes或做多日不中斷驗證。','']
 return lines
