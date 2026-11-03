"""Render final Markdown/CSV exclusively from measured artifacts."""
import csv,json,pathlib,statistics,hashlib,collections,math,datetime
from lab import LAB,existing,sha
def mdtable(head,rows):return '| '+' | '.join(head)+' |\n| '+' | '.join('---' for _ in head)+' |\n'+''.join('| '+' | '.join(str(x).replace('\n',' ').replace('|','/') for x in row)+' |\n' for row in rows)
def fmt(x,d=2):return '未測試' if x is None else f'{x:.{d}f}'
def median(rows,path):
 vals=[]
 for row in rows:
  value=row
  for key in path.split('.'):
   value=value.get(key) if isinstance(value,dict) else None
  if isinstance(value,(int,float)):vals.append(value)
 return statistics.median(vals) if vals else None
def subset(rows,**query):return [r for r in rows if all(r.get(k)==v for k,v in query.items())]
def load(name):
 p=LAB/name
 return json.loads(p.read_text(encoding='utf-8-sig')) if p.exists() else {}
def main():
 inv=load('inventory.json');system=load('system.json');osinfo=load('system-os.json');restore=load('restore-check.json');compat=load('compatibility.json')
 raw=existing('benchmark');expected=hashlib.sha256((LAB/'prompts/short.txt').read_bytes()).hexdigest();latest={}
 for row in raw:
  if row.get('case')=='short' and row.get('prompt_sha256')!=expected:continue
  latest[row['key']]=row
 bench=list(latest.values());good=[r for r in bench if r.get('ok') and r.get('actual_output_matches')];coding=list({r['key']:r for r in existing('coding')+existing('coding-audit')}.values());coding=[x for x in coding if x.get('task')!='refactor' or x.get('prompt_sha256')==sha(LAB/'fixtures/refactor/prompt.txt')];contexts=list({r['key']:r for r in existing('context')}.values());startups=existing('startups')
 for x in coding:x['task_total_s']=x.get('evaluation_total_s',x.get('agent_latency_s'))
 profiles=['dflash144','dflash128graph','base256','control128off','graph128draft2','graph128draft4','graph128draft5','graph128chunk128','graph128chunk512','graph128draft5chunk512'];profilemeta={}
 for profile in profiles:
  p=LAB/'profiles'/f'{profile}.json'
  if not p.exists():continue
  a=json.loads(p.read_text());get=lambda k,default=None:a[a.index(k)+1] if k in a else default
  profilemeta[profile]={'context':int(get('--max-context')),'graph':'OFF' if '--no-cuda-graph' in a else 'ON','draft':get('--draft-tokens','0'),'chunk':get('--prefill-chunk')}
 flat=[]
 for r in good:
  t=r['timings'];g=r.get('gpu',{});u=r['usage'];flat.append({'profile':r['profile'],'case':r['case'],'output_limit':r['output_limit'],'actual_output':u.get('completion_tokens'),'rep':r['rep'],'cache':r['cache'],'cached_tokens':t.get('cache_n'),'prompt_tokens':u.get('prompt_tokens'),'prefill_tok_s':t.get('prompt_per_second'),'decode_tok_s':t.get('predicted_per_second'),'ttft_s':r.get('ttft_observed_s'),'total_s':r['latency_s'],'draft_accepted':t.get('draft_n_accepted'),'draft_total':t.get('draft_n'),'vram_max_mib':g.get('used_mib_max'),'vram_free_min_mib':g.get('free_mib_min'),'temperature_max_c':g.get('temp_c_max'),'power_max_w':g.get('power_w_max'),'power_mean_w':g.get('power_w_mean'),'cache_valid':r.get('cache_valid'),'prompt_sha256':r.get('prompt_sha256')})
 if flat:
  with (LAB/'benchmark.csv').open('w',encoding='utf-8-sig',newline='') as f:w=csv.DictWriter(f,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
 lines=['# RTX 3080 12GB／Bonsai 2 27B 完整評估報告','', '測試日：2026-11-03，Asia/Taipei。本報告僅引用本輪產生的資料；歷史190／209 tok/s及單次Agent成功紀錄沒有混入本輪統計。','', '## 1. 環境與保護措施','',f'- CPU：{system.get("cpu","未取得")}；RAM可用實體位元組：{system.get("ram_bytes","未取得")}。',f'- OS：{osinfo.get("Caption",system.get("platform"))}，build {osinfo.get("BuildNumber","未知")}。',f'- GPU／驅動初始狀態：`{inv.get("gpu","").strip().splitlines()[-1] if inv.get("gpu") else "未取得"}`。',f'- Python：{inv.get("python","未知")}；Claude Code：{inv.get("claude","未知")}；OpenCode：{inv.get("opencode","未知")}。',f'- 模型：{inv.get("model",{}).get("file")}，{inv.get("model",{}).get("bytes")} bytes；SHA256 `{inv.get("model",{}).get("sha256")}`。',f'- 引擎：現有Fusion KVMem sm86二進位，build字串為unknown；不推測未標示的版本。SHA256 `{inv.get("engine",{}).get("sha256")}`，{inv.get("engine",{}).get("bytes")} bytes。',f'- 專案起始commit：`{inv.get("repo_commit")}`。',f'- 穩定Profile雜湊比對：{restore.get("stable_hashes_match","尚未完成")}；原啟動參數保留／恢復：{restore.get("original_engine_options_match","尚未完成")}。', '- 實驗Profile都在本資料夾profiles；未改模型權重、未安裝Harness或大型依賴。重啟前檢查slots，僅停止engine.pid對應且ExecutablePath符合的自有程序；橋接保持原有保護。','', '## 2. 方法與解讀限制','', '- A：每組獨立重啟，先用不同Prompt暖機，再送相同測試Prompt；各冷／熱至少三次。冷樣本以cache_n=0驗證，熱樣本必須真的有快取命中。舊的45-token短Prompt補測前資料保留但排除統計。', '- A原生8080串流：temperature=0、seed=42、思考關閉；ignore_eos=true用來固定256／512／1024輸出。這是吞吐測試，不是自然結束的日常回答。TTFT計第一個非空文字／思考delta，不是HTTP首位元組。', '- GPU每250ms由nvidia-smi抽樣整張卡，包含Windows與其他GPU程序，可能漏掉瞬時峰值。非嚴格恆溫環境；功耗、溫度及測試次序均應一起看。', '- B：真實Claude Code經8081，原思考1536與橋接temperature=0.3政策不變；CLI未提供可固定的seed，以三次重複顯示隨機性。外部驗收、既有測試、保護檔案與實際執行測試同時通過才算完成。', '- C：每個Profile／長度用一個冷資料集與三次同前綴追問；追問是相依樣本，不冒稱三個獨立冷資料集。六個位置加一項帶干擾值的兩段關聯，各自精確比對。原生API未經Harness壓縮。', '- 原生TTFT與8081緩衝SSE不同：橋接先等完整一輪再檢查工具；引擎先吐字不表示CLI已能顯示。', '- OOM、啟動或API錯誤會停止該組並記錄，不以無限重試挑成功值；沒有數據的項目標「未測試」。','', '## 3. Benchmark總覽','', '下表短題Decode取512輸出的冷樣本中位數；其餘Prefill／TTFT／Latency統一取約32K輸入、256輸出的冷樣本。不同Context／檔位差距是整體配方差距；只有相同128K的Graph控制組才較能分離Graph因素。','']
 rows=[]
 for profile in profiles:
  if profile not in profilemeta:continue
  meta=profilemeta[profile];short=subset(good,profile=profile,case='short',output_limit=512,cache='cold');long=subset(good,profile=profile,case='32768',cache='cold');allrows=subset(good,profile=profile);ss=subset(startups,profile=profile)
  total=sum(x['timings'].get('draft_n',0) for x in long);acc=sum(x['timings'].get('draft_n_accepted',0) for x in long)
  gpuvals=lambda name:[x.get('gpu',{}).get(name) for x in allrows if x.get('gpu',{}).get(name) is not None]
  rows.append([profile,meta['context'],meta['graph'],meta['draft'],meta['chunk'],len(short),fmt(median(short,'timings.predicted_per_second')),fmt(median(long,'timings.prompt_per_second')),fmt(median(long,'ttft_observed_s')),fmt(median(long,'latency_s')),f'{acc/total:.1%}' if total else '—',fmt(min(gpuvals('free_mib_min')) if gpuvals('free_mib_min') else None,0),fmt(max(gpuvals('temp_c_max')) if gpuvals('temp_c_max') else None,0),f'{sum(bool(x["ready"]) for x in ss)}/{len(ss)}'])
 lines.append(mdtable(['Profile','Context','Graph','Draft','Chunk','短題n','Decode tok/s','32K Prefill tok/s','32K TTFT秒','32K總秒','32K接受率','最低餘裕MiB','最高°C','啟動成功'],rows))
 lines+=['### 3.1 每種輸入與輸出長度的冷／熱結果','', '所有數值為中位數；三次樣本的完整值、實際token數、功耗與VRAM見[benchmark.csv](benchmark.csv)。cache_valid=false的第二次請求不是已驗證熱快取，不與真熱快取混算。','']
 rows=[]
 for profile in profiles:
  for case,output in [('short',256),('short',512),('short',1024)]+[(str(n),256) for n in (8192,32768,65536,98304)]:
   for cache in ('cold','hot'):
    a=subset(good,profile=profile,case=case,output_limit=output,cache=cache)
    if not a:continue
    rows.append([profile,case,output,cache,len(a),sum(bool(x.get('cache_valid')) for x in a),fmt(median(a,'timings.predicted_per_second')),fmt(median(a,'timings.prompt_per_second')),fmt(median(a,'ttft_observed_s')),fmt(median(a,'latency_s'))])
 lines.append(mdtable(['Profile','輸入','輸出','快取','n','快取分類有效n','Decode','Prefill','TTFT秒','總秒'],rows))
 errors=[r for r in bench if not r.get('ok')];lines+=['### 3.2 失敗與未測項目','',mdtable(['Profile／組別','狀態'],[[r.get('key'),r.get('error')] for r in errors]) if errors else '本輪A目前沒有已記錄的啟動／API失敗。']
 lines+=['','## 4. 真實Coding Agent結果','', 'Task1：inclusive日期Bug；Task2：多幣別與日期過濾功能、須新增至少三個測試；Task3：八模組金額重構，檢查真實使用共用邏輯且保留公開行為。沒有在正式repo做破壞性測試。','']
 rows=[]
 for profile in ('dflash128graph','dflash144'):
  for task in ('bug','feature','refactor'):
   group=subset(coding,profile=profile,task=task);success=[x for x in group if x.get('passed')];times=[x.get('task_total_s',0) for x in group]
   rows.append([profile,task,len(group),f'{len(success)}/{len(group)}',fmt(median(success,'task_total_s')) if success else '無成功樣本',fmt(sum(times)/len(success)) if success else '無成功樣本',fmt(median(group,'tool_calls'),0),sum(x.get('tool_errors',0) for x in group),sum(x.get('guard_recoveries',0) for x in group)])
 lines.append(mdtable(['Profile','任務','次數','完成','成功耗時中位秒','含失敗攤提秒/成功件','工具中位','工具錯誤合計','橋接重試合計'],rows));lines+=['','含失敗攤提＝該組全部執行時間÷成功件數；零成功時沒有可用成功耗時。工具錯誤可能包含正常診斷期間的失敗，不等同最終任務失敗。非連續重複也可能是必要的重測，不直接稱為循環。','']
 rows=[]
 for x in coding:
  u=x.get('usage',{});a=x.get('acceptance',{});g=x.get('gpu',{});e=x.get('engine_usage',{})
  it=e.get('input_tokens_total') if e.get('completed_requests') else u.get('input_tokens',0)+u.get('cache_read_input_tokens',0)+u.get('cache_creation_input_tokens',0);ct=e.get('cached_input_tokens') if e.get('completed_requests') else u.get('cache_read_input_tokens');ot=e.get('output_tokens') if e.get('completed_requests') else u.get('output_tokens')
  grade=f'{a.get("tests",0)-a.get("failures",0)-a.get("errors",0)}/{a.get("tests",0)}' if a.get('tests') else '未能載入驗收'
  rows.append([x['key'],x.get('passed'),fmt(x.get('agent_latency_s')),x.get('tool_calls','—'),it,ct,ot,x.get('tool_errors','—'),x.get('guard_recoveries','—'),x.get('guard_stops','—'),x.get('consecutive_repeat_count','—'),x.get('nonconsecutive_duplicate_count','—'),grade,x.get('protected_files_changed',[]),fmt(g.get('free_mib_min'),0),fmt(g.get('temp_c_max'),0),x.get('error','')])
 lines.append(mdtable(['Run','完成','秒','工具','總模型輸入token','含cached token','模型輸出token','工具錯誤','橋接重試','橋接停止','連續重複','全部重用','外部測試','保護檔變更','餘裕MiB','°C','錯誤'],rows));lines+=['','Token優先採各任務時間窗內引擎完成RPC日誌，包含橋接重試與客戶端斷線後的收尾；CLI原始usage另保留。輸入含cache，不能再把cached欄加一次。逾時後補做外部驗收不會把逾時改判成功。']
 lines+=['','## 5. Context準確率','', 'S=開頭、E=前段、M=中間、L=後段、Z=結尾、R=固定seed隨機位置、X=跨段關聯。冷欄每項是一題；熱欄是同資料三次追問的答對數／3。不得把窗口容量等同有效記憶能力。','']
 rows=[]
 for x in contexts:
  rounds=x.get('rounds',[])
  if not rounds:rows.append([x['profile'],x['target'],'—',x.get('error','未測試')]);continue
  cold=rounds[0];hot=rounds[1:];keys=['AT_START','EARLY','MIDDLE','LATE','AT_END','RANDOM_SPOT','LINKED']
  rows.append([x['profile'],x['target'],cold['usage'].get('prompt_tokens'),'/'.join('1' if cold['correct_by_key'][k] else '0' for k in keys),'/'.join(str(sum(r['correct_by_key'][k] for r in hot)) for k in keys),fmt(cold['timings'].get('prompt_ms',0)/1000),fmt(cold['ttft_observed_s']),fmt(median(hot,'latency_s')),f'{median(hot,"cache_hit_fraction"):.2%}' if median(hot,'cache_hit_fraction') is not None else '未測試',cold.get('json_format_valid'),x.get('truncation_detected'),x.get('input_truncation_suspected'),x.get('error','')])
 lines.append(mdtable(['Profile','目標token','實際輸入','冷S/E/M/L/Z/R/X','後續各項答對n/3','冷Prefill秒','冷TTFT秒','後續總秒','後續快取命中','冷可解析JSON','輸出截斷','疑似輸入截斷','API錯誤'],rows));lines+=['','Context原文沒有醒目的位置標籤，查找的是提問指定的普通row_ID值；跨段題需經別名指到目標，另有干擾值。JSON缺鍵也算該項未正確交付，原始回應與missing_keys可區分格式／schema失敗與內容誤答。後續請求是在同一user訊息尾端附加驗證句，不是保留assistant答案的真正多輪對話；0%命中時屬嘗試熱快取但失敗，不能稱為熱快取速度。故準確率變化不能單獨歸因給快取。真正對話另見第5.1節。']
 lines+=['','## 6. Harness相容性與政策','',f'- 目前橋接health：`{json.dumps(compat.get("bridge_health",{}),ensure_ascii=False)}`。',f'- OpenCode檔位steps：`{json.dumps(compat.get("opencode_steps",{}),ensure_ascii=False)}`；null表示未設定，不是舊24預設。',f'- OpenAI工具往返：{compat.get("openai_tool_roundtrip","未測試")}。',f'- Anthropic工具往返：{compat.get("anthropic_tool_roundtrip","未測試")}。',f'- OpenCode真實任務：{compat.get("opencode_actual_task","未測試")}。',f'- 串流：`{json.dumps(compat.get("streaming",{}),ensure_ascii=False)}`。',f'- 同時兩請求：`{json.dumps(compat.get("concurrency",{}),ensure_ascii=False)}`。',f'- Responses端點狀態：{compat.get("responses_endpoint_status","未測試")}；目前不支援Responses。', '- Claude Code以本輪18個任務的觀測為準，不把有限測試宣稱成全天候／多日穩定保證。防循環未停用；有些正常重複指令可能被恢復邏輯糾正，事件計數已列出。', '- Hermes只做官方文件相容性分析，沒有安裝或改個人設定；候選配置與驗收步驟見[HERMES_PLAN.md](HERMES_PLAN.md)。須使用8081、文字／工具子集、釘選實際窗口。', '- 多Agent需客戶端序列佇列；橋接LOCK與引擎concurrency1限制並行，不代表具備公平排程、取消與全任務期限。','', '## 7. 三套配置建議','']
 stable_and_draft=[p for p in profiles if p in ('dflash144','dflash128graph','base256','control128off','graph128draft2','graph128draft4','graph128draft5','graph128draft5chunk512')]
 speed_candidates=[]
 for p in stable_and_draft:
  g=subset(good,profile=p,case='short',output_limit=512,cache='cold')
  if len(g)>=3 and not any(x.get('profile')==p for x in errors):speed_candidates.append((median(g,'timings.predicted_per_second'),p))
 speed=max(speed_candidates)[1] if speed_candidates else '未測試'
 daily=[]
 for p in ('dflash128graph','dflash144'):
  group=subset(coding,profile=p);s=[x for x in group if x.get('passed')]
  if group:daily.append((len(s)/len(group),-sum(x.get('task_total_s',480) for x in group)/max(len(s),1),p))
 daily_name=max(daily)[2] if daily and any(x[0]>0 for x in daily) else '尚無足夠成功樣本，不能推薦無人監督Coding配置'
 lines += [f'### 極速候選：{speed}', '', '依至少三次512-token冷樣本中位數、無已記錄組錯誤篩選；這是吞吐候選，不是Coding品質冠軍。需同看256／1024、長Prompt、溫度與接受率；微小差異不足以宣稱普遍優勢。只提供獨立實驗設定，沒有覆寫穩定檔位。', '',f'### 日常Coding候選：{daily_name}', '', '先比較本輪完成率，再比較包含失敗成本的每成功件耗時。樣本少、任務類型有限，僅是這組基準的候選；若兩者有失敗，不應把它當成「已能無人監督完成任意專案」。保留原dflash144作回退，必要時用搜尋縮小輸入及外部測試。', '', '### 超長Context：base256（容量模式，品質看第5節）', '', '256K的設定容量適合較大輸入；本輪只驗到120K資料，不宣稱整個256K都可靠。若中段／跨段找回失敗，應先檢索原文片段、引用來源與程式精確查值；不能用更大窗口掩蓋誤答。','', '## 8. 下一階段最值得測的三項','',mdtable(['排序','項目','預期收益','風險','成本'],[['1','固定代表性專案做更長的Coding驗收；縮小無關讀檔與工具輸出','改善真正完成時間與正確率；非本輪已量化收益','中：檢索漏掉相關檔案','中'],['2','將本輪較佳Draft／Chunk候選做交替順序、等溫度重測及Coding三任務驗證','確認吞吐收益能否轉成任務收益','中：OOM、接受率依內容而變','中'],['3','較高精度KV或分段檢索的長文A/B，保持標準答案與位置測試','針對Lost in the Middle，可能改善正確性','高精度KV需更多顯存，可能犧牲容量','中高']]),'', '## 9. 可重現與原始資料','', '依序執行（Windows PowerShell，工作目錄為本資料夾）：','', '```powershell','python scripts/lab.py inventory','python scripts/lab.py prompts','python scripts/fixtures.py','python scripts/lab.py benchmark --profiles dflash128graph dflash144 base256 control128off','python scripts/lab.py benchmark --profiles graph128draft2 graph128draft4 graph128draft5 --cases short:512','python scripts/lab.py benchmark --profiles graph128chunk128 graph128chunk512 --cases 8192:256','python scripts/coding.py --profiles dflash128graph dflash144 --reps 3','python scripts/context.py prep','python scripts/context.py run','python scripts/compat.py','python scripts/report.py','```','', 'inventory第一次執行會記錄當時的原始服務參數；重跑前應建立新的整份實驗資料夾，避免覆寫本輪manifest。腳本按既有key續跑，拒絕重用已改過的Coding工作目錄。不可讓兩個實驗控制器同時操作同一引擎。', '', '- [inventory.json](inventory.json)：實際模型／引擎雜湊與穩定Profile快照。','- [profiles/](profiles/)：獨立設定差異，檔名control128off只變Graph，draft／chunk實驗只變對應參數。','- [prompts/](prompts/)：完整Prompt與Context標準答案／位置。','- [fixtures/](fixtures/)：相同起始檔、任務Prompt、外部驗收。','- [runs/](runs/)：每次Coding實際修改結果，供人工審查。','- [raw/benchmark.jsonl](raw/benchmark.jsonl)、[benchmark.csv](benchmark.csv)：逐樣本數據與cache有效性。','- [raw/coding.jsonl](raw/coding.jsonl)：CLI使用量、工具／重試／驗收。','- [raw/context.jsonl](raw/context.jsonl)：逐位置答案與快取。','- [raw/gpu.jsonl](raw/gpu.jsonl)：250ms整卡抽樣。','- [logs/](logs/)：每次啟動與完整引擎事件；raw內有SSE、CLI逐事件和外部測試輸出。','- [restore-check.json](restore-check.json)：原配置還原及穩定Profile雜湊確認。','', '限制：LLM的自評成功不作驗收；CLI顯示的美元成本不是本機實際帳單。原始結果如有同key補測，表格採最後一筆且保留舊資料，不刪除失敗記錄。']
 resource_rows=[]
 for profile in profiles:
  measured=subset(good,profile=profile);short=subset(measured,case='short',output_limit=512,cache='cold')
  def extreme(field,which):
   values=[x.get('gpu',{}).get(field) for x in measured if x.get('gpu',{}).get(field) is not None]
   return which(values) if values else None
  energy=sum(x['gpu']['power_w_mean']*x['latency_s'] for x in short if x.get('gpu',{}).get('power_w_mean') is not None)
  output=sum(x['usage'].get('completion_tokens',0) for x in short if x.get('gpu',{}).get('power_w_mean') is not None)
  resource_rows.append([profile,fmt(extreme('used_mib_max',max),0),fmt(extreme('free_mib_min',min),0),fmt(extreme('temp_c_max',max),0),fmt(extreme('power_w_max',max),1),fmt(output/energy if energy else None,3)])
 lines+=['','## 10. 資源效率補表','', '峰值來自該Profile全部已測case，case覆蓋不同，不宜當成等工作量功耗比較。輸出token/J統一取512-token短題冷樣本，用整卡抽樣平均功率×請求秒數估算；含prefill，不是牆上電表，也不是僅Decode能耗。','',mdtable(['Profile','最高使用MiB','最低餘裕MiB','最高°C','最高W','512輸出token/J'],resource_rows)]
 if speed in profilemeta:
  sp=median(subset(good,profile=speed,case='short',output_limit=512,cache='cold'),'timings.predicted_per_second');ref=median(subset(good,profile='dflash128graph',case='short',output_limit=512,cache='cold'),'timings.predicted_per_second')
  lines+=['',f'極速候選的512冷樣本中位數為{fmt(sp)} tok/s；相對本輪128K Graph/draft3同題中位數{fmt(ref)}，整體配方差約{fmt((sp/ref-1)*100) if sp and ref else "未測試"}%。組合Profile若同時變Draft與Chunk，不能把此差歸給單一參數。此候選沒有完整Coding三任務驗證，不作日常自動Coding推薦。']
 cg=subset(coding,profile=daily_name);cp=[x for x in cg if x.get('passed')]
 if cg:lines+=['',f'日常候選本輪為{len(cp)}/{len(cg)}正式任務通過；全部任務的CLI時間合計{fmt(sum(x.get("agent_latency_s",480) for x in cg))}秒。仍有失敗時，建議僅在外部驗收及人工審查下使用，不是無人監督可靠性認證。']
 draft_rows=[]
 for profile in ('graph128draft2','dflash128graph','graph128draft4','graph128draft5','graph128draft5chunk512'):
  g=subset(good,profile=profile,case='short',output_limit=512,cache='cold');dn=sum(x['timings'].get('draft_n',0) for x in g);accepted=sum(x['timings'].get('draft_n_accepted',0) for x in g)
  draft_rows.append([profile,profilemeta[profile]['draft'],profilemeta[profile]['chunk'],len(g),fmt(median(g,'timings.predicted_per_second')),accepted,dn,f'{accepted/dn:.2%}' if dn else '未測試',fmt(median(g,'ttft_observed_s'))])
 lines+=['','### Draft接受率與生成效率','', '同一128K與Graph設定、同一512-token短Prompt；組合列另改Chunk，不能視為單獨Draft效果。接受率高不一定tok/s高，還需考慮每輪候選長度及驗證成本。','',mdtable(['Profile','Draft','Chunk','冷樣本n','Decode tok/s','接受候選數','提出候選數','接受率','TTFT秒'],draft_rows)]
 if not (LAB/'FINALIZED.json').exists():lines.insert(2,'> **實驗進行中，此為自動產生的草稿；未完成欄位不是最終結論。**\n')
 lines+=['','### 方法補充與校準','', '- 初始原生A按固定Profile順序執行，沒有完全等溫或隨機化順序；後續短題補測、Draft／Chunk、Coding與Context加上起跑前≥80°C降至≤72°C的等待。功耗上限450W是機器原有設定，沒有被本實驗更改；驅動預設400W、最高工作93°C、降速95°C見[thermal-environment.txt](thermal-environment.txt)。不同熱階段不可當成嚴格單因果百分比。','- 熱快取Prefill速率只用剩餘未快取token計算；少數尾端token除以固定開銷，不能拿它和冷快取整段吞吐直接比較。','- Coding使用固定英文Prompt和受控工具允許清單；不含GUI、外部服務或大型第三方依賴。Shell命令遭拒與escaping錯誤是本輪Harness／模型組合的實際成本，但不代表所有日常權限政策都相同。','- Coding每次最多480秒是本實驗的監督逾時，不是正式橋接或OpenCode的新上限。原始測試及[校準](grader-calibration.json)保留。','- 重構第一個pilot對parse_money新helper精度描述不夠明確；原9/10結果與原Prompt保留，補明Prompt後補足兩個配置各三次。驗收標準沒有為了通過而放寬。見[protocol-amendment.json](protocol-amendment.json)。','- 設定的增加／刪除／變更差異見[profile-differences.json](profile-differences.json)。','']
 from enhance_report import enhance
 lines=enhance(lines,bench,good,coding,contexts,profilemeta,speed,daily_name)
 (LAB/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
 dump_summary={'benchmark_valid_rows':len(good),'benchmark_errors':errors,'coding_runs':len(coding),'coding_passes':sum(bool(x.get('passed')) for x in coding),'context_cells':len(contexts),'speed_candidate':speed,'daily_candidate':daily_name,'stable_profiles_unchanged':restore.get('stable_hashes_match')}
 (LAB/'summary.json').write_text(json.dumps(dump_summary,ensure_ascii=False,indent=2)+'\n',encoding='utf-8');print(json.dumps(dump_summary,ensure_ascii=False))
if __name__=='__main__':main()
