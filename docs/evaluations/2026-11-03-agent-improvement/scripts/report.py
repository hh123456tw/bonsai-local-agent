"""Render improvement results; historical controls remain separate."""
import collections,csv,json,pathlib,re,statistics
from lab import LAB,existing,dump

def load(name):
 p=LAB/name;return json.loads(p.read_text(encoding='utf-8-sig')) if p.exists() else {}
def rows(path):return [json.loads(x) for x in path.read_text(encoding='utf-8').splitlines()] if path.exists() else []
def table(head,data):return '| '+' | '.join(head)+' |\n| '+' | '.join('---' for _ in head)+' |\n'+''.join('| '+' | '.join(str(v).replace('|','/').replace('\n',' ') for v in r)+' |\n' for r in data)
def med(data,key):
 v=[x.get(key) for x in data if isinstance(x.get(key),(float,int))];return statistics.median(v) if v else None
def f(x):return '—' if x is None else f'{x:.2f}'
def total(x):return x.get('evaluation_total_s',x.get('agent_latency_s',0))
def summary(group):
 measured=[x for x in group if not x.get('not_tested')];success=[x for x in measured if x.get('passed')]
 return {'measured':len(measured),'not_tested':len(group)-len(measured),'passes':len(success),'total_seconds':sum(total(x) for x in measured),'seconds_per_success':sum(total(x) for x in measured)/len(success) if success else None,'tool_calls':sum(x.get('tool_calls',0) for x in measured),'tool_errors':sum(x.get('tool_errors',0) for x in measured)}

def tool_mix(path):
 calls={}
 for e in rows(path):
  if e.get('type')=='assistant':
   for b in e.get('message',{}).get('content',[]):
    if b.get('type')=='tool_use':calls[b['id']]=b
 bash=[c.get('input',{}).get('command','') for c in calls.values() if c['name']=='Bash']
 return {'tools':dict(collections.Counter(c['name'] for c in calls.values())),'bash_python_c_or_heredoc':sum(bool(re.search(r'\bpython(?:\.exe)?\s+(?:-c\b|-\s*<<)',s)) for s in bash),'bash_source_write_pattern':sum(bool(re.search(r'write_text|write_bytes|\.write\(|Set-Content|Out-File',s,re.I)) for s in bash)}

def main():
 baseline=list({x['key']:x for x in rows(LAB/'baseline/coding.jsonl')+rows(LAB/'baseline/coding-audit.jsonl')}.values());baseline=[x for x in baseline if x['profile']=='dflash144']
 current=list({x['key']:x for x in existing('coding')+existing('coding-audit')}.values());api=load('api-validation.json');gate=load('draft5-gate.json');decision=load('guidance-decision.json')
 arms=[('舊版144K','dflash144',baseline),('通用指引144K','dflash144',[x for x in current if x['profile']=='dflash144']),('Windows指引144K','dflash144windows',[x for x in current if x['profile']=='dflash144windows']),('通用指引Draft5','graph128draft5',[x for x in current if x['profile']=='graph128draft5'])]
 totals={label:summary(group) for label,profile,group in arms};before=load('raw/budget-before.json');after=load('raw/budget-after.json')
 for name,variable in [('before',before),('after',after)]:
  p=LAB/'raw'/f'budget-{name}.stdout'
  if p.exists():variable.update(json.loads(p.read_text(encoding='utf-8').splitlines()[0]))
 lines=['# Bonsai Agent改善報告：API預算與改檔指引','', '2026-11-03，RTX3080 12GB。這份報告只比較本輪修正；[上一輪完整Benchmark](../bonsai-evaluation-20261103/REPORT.md)另存，歷史與新樣本沒有混算。','',
 '## 已確定的修正','',
 f'- 相同OpenAI請求要求16 token並關思考：修正前實際{before.get("actual_usage",{}).get("completion_tokens","未測試")} token、{before.get("seconds","未測試")}秒；修正後{after.get("actual_usage",{}).get("completion_tokens","未測試")} token、{after.get("seconds","未測試")}秒。這是預算被尊重，不是Decode吞吐變快。',
 f'- 實機API檢查：{"通過" if api.get("passed") else "未完成"}，{len(api.get("cases",[]))}個案例。支援max_completion_tokens別名、顯式關思考、合法思考預算；不合法或衝突額度回400。',
 '- 輸出預設16384、上限32768；一般大額度的1536思考預算保留。原生引擎啟用思考至少1024，校驗額外預留256答案token；不足就清楚拒絕，不偷加額度。',
 '- 一般截斷保留length；截斷工具批次／無效JSON不放行並回502。空白且用完額度不再當循環重試。既有重複工具糾正、權限及max_tool_calls=null保留。',
 '- 新增Claude Code追加指引：Edit／Write優先、避免巢狀Bash改檔、錯誤後改變做法、逐項核對需求及測試。只改指引，沒有放寬工具權限；不保證模型遵守。','',
 '## Coding：先看完成率與總時間','',
 'Bug／功能／八模組重構各三次；同起始檔、同使用者任務Prompt、同外部驗收。新版多了固定system指引與橋接安全修正，因此只比較整體配方，不把差異歸因於單一改動。Claude走Anthropic路徑，原本就能尊重小輸出額度；OpenAI小預算修正不能直接解釋Claude任務耗時。','']
 lines.append(table(['組別','實測次數','未測試','完成','含驗收總秒','含失敗秒/成功件','工具呼叫合計','工具錯誤合計'],[[label,s['measured'],s['not_tested'],f'{s["passes"]}/{s["measured"]}',f(s['total_seconds']),f(s['seconds_per_success']),s['tool_calls'],s['tool_errors']] for label,s in totals.items()]))
 taskrows=[]
 for label,profile,group in arms:
  for task in ('bug','feature','refactor'):
   g=[x for x in group if x['task']==task];s=summary(g);successful=[{**x,'total':total(x)} for x in g if x.get('passed')]
   taskrows.append([label,task,f'{s["passes"]}/{s["measured"]}',s['not_tested'],f(med(successful,'total')),f(s['seconds_per_success']),f(med(g,'tool_calls')),s['tool_errors']])
 lines+=['',table(['組別','任務','完成','未測試','成功總秒中位','含失敗秒/成功件','工具中位','工具錯誤合計'],taskrows),'',
 '主要時間為CLI啟動到外部驗收／公開測試結束，包含工具與逾時收尾；不含引擎起跑及降溫。外部驗收、既有測試、保護檔案、CLI正常結束且真的執行測試，全部成立才算成功。480秒仍只是本實驗監督逾時，沒有改成正式工具總上限。','']
 detail=[];flat=[]
 for x in current:
  a=x.get('acceptance',{});gpu=x.get('gpu',{});e=x.get('engine_usage',{});tests=a.get('tests',0);grade=f'{tests-a.get("failures",0)-a.get("errors",0)}/{tests}' if tests else '未載入／未測試'
  detail.append([x['key'],'未測試' if x.get('not_tested') else x.get('passed'),f(total(x)) if not x.get('not_tested') else '—',x.get('tool_calls','—'),x.get('tool_errors','—'),x.get('guard_recoveries','—'),x.get('consecutive_repeat_count','—'),grade,x.get('protected_files_changed','—'),gpu.get('free_mib_min','—'),gpu.get('temp_c_max','—'),x.get('error','')])
  flat.append({'run':x['key'],'profile':x['profile'],'task':x['task'],'passed':x.get('passed',False),'not_tested':x.get('not_tested',False),'cli_seconds':x.get('agent_latency_s'),'total_seconds':total(x) if not x.get('not_tested') else None,'tool_calls':x.get('tool_calls'),'tool_errors':x.get('tool_errors'),'guard_recoveries':x.get('guard_recoveries'),'guard_stops':x.get('guard_stops'),'consecutive_repeats':x.get('consecutive_repeat_count'),'all_duplicate_calls':x.get('nonconsecutive_duplicate_count'),'input_tokens_with_cache':e.get('input_tokens_total'),'cached_input_tokens':e.get('cached_input_tokens'),'output_tokens':e.get('output_tokens'),'external_grade':grade,'protected_changed':json.dumps(x.get('protected_files_changed',[])),'vram_free_min_mib':gpu.get('free_mib_min'),'temperature_max_c':gpu.get('temp_c_max'),'power_max_w':gpu.get('power_w_max'),'error':x.get('error','')})
 for x,row in zip(current,flat):row.update(guard_tool_rejections=x.get('guard_tool_rejections'),guard_output_truncations=x.get('guard_output_truncations'),client_api_retry_events=x.get('client_api_retry_events'),max_request_input_tokens=x.get('engine_usage',{}).get('max_request_prompt_tokens'),max_request_output_tokens=x.get('engine_usage',{}).get('max_request_output_tokens'))
 if flat:
  with (LAB/'coding.csv').open('w',encoding='utf-8-sig',newline='') as out:w=csv.DictWriter(out,fieldnames=list(flat[0]));w.writeheader();w.writerows(flat)
 lines+=['## 每次任務與資源','',table(['Run','完成','總秒','工具','工具錯誤','橋接重試','連續重複','外部驗收','保護檔變更','餘裕MiB','最高°C','錯誤'],detail),'',
 '完整輸入／輸出token（輸入含cache）、重複工具、停止原因及資源見[coding.csv](coding.csv)。250ms抽樣量整張卡，含桌面程式，可能漏掉瞬時峰值；本輪沒有改原450W功耗上限、風扇或顯存設定。','',
 '## 工具使用有沒有改變','']
 mixes=load('baseline/tool-mix.json')
 if not mixes:
  old=LAB.parent/'bonsai-evaluation-20261103'
  mixes={x['key']:tool_mix(old/'raw'/f'{x["key"]}.claude.jsonl') for x in baseline};dump(LAB/'baseline/tool-mix.json',mixes)
 newmixes={x['key']:tool_mix(LAB/'raw'/f'{x["key"]}.claude.jsonl') for x in current if not x.get('not_tested')};dump(LAB/'tool-mix.json',newmixes)
 tm=[]
 for label,profile,group in arms:
  mix=mixes if label=='舊版144K' else newmixes;counter=collections.Counter();nested=0;writepatterns=0
  for x in group:
   v=mix.get(x['key'],{});counter.update(v.get('tools',{}));nested+=v.get('bash_python_c_or_heredoc',0);writepatterns+=v.get('bash_source_write_pattern',0)
  tm.append([label,counter.get('Read',0),counter.get('Write',0),counter.get('Edit',0),counter.get('Bash',0),nested,writepatterns])
 lines += [table(['組別','Read','Write','Edit','Bash','Bash含python -c/heredoc','Bash含寫檔字樣'],tm),'',
 '最後兩欄為命令文字的可重現規則分類，可能包含正當的檢查／測試，不直接當錯誤或循環。重複呼叫也可能是必要的重跑測試。指引只在實際採用率和外部驗收有改善時才算有效，不能只看提示文字。','',
 '## 採用與回退','',f'- 指引預設：{ {"generic":"通用改檔指引","windows":"Windows專用指引","baseline":"原本不追加指引的行為"}.get(decision.get("selected"),"尚待完整結果確認") }。完整決策與各組統計見[guidance-decision.json](guidance-decision.json)。',f'- Draft5啟動條件：144K至少完成8/9，實際完成{gate.get("daily_passes","待確認")}/9；本輪{ "已進入實測" if gate.get("allowed") else "未進入實測" }，它維持獨立實驗配置。',
 '- 每個配置仍只有三次／任務，不是大規模統計證明。舊版與新版分時執行，未完全等溫或隨機化；不可把小差異宣稱為普遍勝率或GPU參數的因果效果。',
 '- Draft5維持獨立131072／Graph ON／draft5／chunk256；第一個啟動／OOM失敗即停止該Profile，不降低Context刷分、不停用防循環、不覆寫原Profile。',
 '- 舊版原始部署程式在baseline/runtime，本輪中間部署快照在rollback；回退須先確認8081與引擎沒有正式工作，只重啟自有橋接。舊版會恢復已知小輸出額度問題，不建議因指引無效而把API修正一起撤掉。','',
 '## 可重現','',
 '先在新的獨立資料夾放scripts；確認ROOT指向本機部署、REPO位置正確，而且沒有正式任務。保留原始資料，不在這份已修改的runs上重跑。','',
 '```powershell','python scripts/lab.py inventory','python scripts/fixtures.py','python scripts/api_smoke.py','python scripts/run_study.py','python scripts/run_windows.py','python scripts/report.py','```','',
 'run_study先跑144K九次並稽核；完成至少8/9且沒有未測任務時，才進Draft5九次（仍會在首次啟動失敗停止）。要重跑歷史控制，需明確使用舊runtime／無新增指引，不能把新版當成舊版。','',
 '- [protocol.json](protocol.json)、[tested-source.json](tested-source.json)、[fixture-comparison.json](fixture-comparison.json)：實測來源、設定及任務一致性。',
 '- [api-validation.json](api-validation.json)：實際HTTP上限、思考、工具與串流驗證。',
 '- [raw/coding.jsonl](raw/coding.jsonl)、[raw/coding-audit.jsonl](raw/coding-audit.jsonl)、[coding.csv](coding.csv)：原始任務與稽核。',
 '- [logs/](logs/)、[runs/](runs/)、[fixtures/](fixtures/)：引擎、實際修改與外部驗收。',
 '- [FINALIZED.json](FINALIZED.json)：全部測試結束後的模型、設定、部署及服務還原稽核。','']
 from error_analysis import analyze
 baseline_errors=load('baseline/error-analysis.json')
 if not baseline_errors or not all('event_kinds' in v for v in baseline_errors.values()):
  old=LAB.parent/'bonsai-evaluation-20261103'
  baseline_errors={x['key']:analyze(old/'raw'/f'{x["key"]}.claude.jsonl') for x in baseline};dump(LAB/'baseline/error-analysis.json',baseline_errors)
 current_errors={x['key']:analyze(LAB/'raw'/f'{x["key"]}.claude.jsonl') for x in current if not x.get('not_tested')};dump(LAB/'error-analysis.json',current_errors)
 classified=[]
 for label,profile,group in arms:
  data=baseline_errors if label=='舊版144K' else current_errors;counter=collections.Counter()
  for x in group:counter.update(data.get(x['key'],{}).get('counts',{}))
  classified.append([label,*[counter[k] for k in ('permission','python_syntax','missing_tool','import','missing_file','test_or_other_command')]])
 idx=lines.index('## 採用與回退')
 lines[idx:idx]=['### 工具錯誤分類','',table(['組別','需授權／遭拒','Python語法','不存在工具','匯入','找不到檔案','測試／其他命令'],classified),'',
 '例如通用指引的一回重構反覆使用python3、/tmp、/usr/bin，出現13次需要授權的工具錯誤；Windows指引因此另列一個實驗組，明示python、既有工作目錄及獨立測試命令，沒有放寬Bash權限。它是在觀察這批任務後定向調整的指引，仍需未見過的真實專案驗證，不能宣稱已證明通用Coding能力。分類依原始工具結果文字，可在error-analysis.json稽核；測試失敗也可能是正常診斷。','']
 resources=[]
 for label,profile,group in arms:
  measured=[x for x in group if not x.get('not_tested')]
  def extreme(container,key,fn):
   values=[x.get(container,{}).get(key) for x in measured if x.get(container,{}).get(key) is not None];return fn(values) if values else '未統計'
  resources.append([label,extreme('engine_usage','max_request_prompt_tokens',max),extreme('gpu','free_mib_min',min),extreme('gpu','temp_c_max',max),extreme('gpu','power_w_max',max),sum(x.get('guard_tool_rejections',0) for x in measured),sum(x.get('client_api_retry_events',0) for x in measured)])
 idx=lines.index('## 採用與回退');lines[idx:idx]=['### 本輪實際覆蓋的輸入與資源','',table(['組別','單次最大完整輸入token','最低餘裕MiB','最高°C','峰值W','工具JSON拒絕事件','CLI API重試事件'],resources),'',
 '單次輸入取引擎完成RPC日誌，含已快取前綴；它與累計輸入token或設定窗口不同。舊控制缺少此最大值時標未統計，不補猜。這輪沒有重測96K以上的長文精確找回，也沒有證明新的指引修復了上輪長文誤答。任務仍是固定的小型英文Python專案，未做長期真實專案驗證。','']
 compact=load('compaction-analysis.json') or []
 idx=lines.index('## 採用與回退');lines[idx:idx]=['### 客戶端壓縮成本','',table(['Run','觸發','壓縮前客戶端token','壓縮後token','耗時秒'],[[x['run'],c['trigger'],c['pre_tokens'],c['post_tokens'],f(c['duration_ms']/1000) if c.get('duration_ms') is not None else '—'] for x in compact for c in x.get('compactions',[])]),'',
 '這是Claude Code原始compact_boundary事件，不是引擎配置容量。觀測到的壓縮成本已包含於任務時間；本輪沒有調整壓縮門檻，也不把壓縮或不同工具路徑的成本當成Draft5的單一因果效果。','']
 if decision.get('applied'):
  lines[4:4]=['**目前採用：144K／Graph OFF／draft3＋通用改檔指引。** 本輪9/9通過；含失敗成本約160秒／成功件，歷史控制為8/9、154秒。完成件數較好，尚未證明整體任務速度提升。Windows指引7/9與Draft5的8/9均不作日常預設。','']
 final=load('FINALIZED.json');ci=load('ci-validation.json')
 if final:
  lines+=['## 最後驗收與保留的限制','',
  '- 35項自動unit／HTTP測試及安裝器dry-run通過；真實Claude啟動器與OpenCode各完成一次新Bug專案，外部測試通過、保護檔案未改。這兩次是整合冒煙檢查，未混入27次Coding比較。',
  '- 已還原144K／Graph OFF／draft3，六份穩定Profile、原引擎參數、模型及引擎雜湊一致；工具總上限仍null，防循環保留。新開原桌面Claude Code捷徑即可使用通用指引。',
  '- 權限審計發現Windows實驗一回提出pip升級的複合命令；工具在執行前預檢拒絕，未執行。沒有為跑分放寬授權，未下載其他模型或安裝新Harness。完整紀錄見[dependency-review.json](dependency-review.json)。',
  '- 仍會有工具試錯、語法與語意錯誤；這組已知小專案不是無人監督、長期真實專案的可靠性認證。CLI原始美元成本是SDK估算，不是本機實際帳單。',
  '- 下一步先用未見過的真實專案驗證通用指引，再單獨核對Claude的壓縮預留與成本，以及未宣告工具／反覆授權錯誤的有界糾正。這些仍未實作或量化收益，不繼續調提示挑本批測試分數。','']
  if ci:lines.append(f'核心修正[3ab5cc6的GitHub Actions]({ci.get("url")})已{ci.get("conclusion")}；[CI紀錄](ci-validation.json)。')
 if not (LAB/'FINALIZED.json').exists():lines.insert(2,'> 實驗進行中；這是草稿，未完成欄位不可作最終結論。\n')
 (LAB/'REPORT.md').write_text('\n'.join(lines)+'\n',encoding='utf-8');dump(LAB/'summary.json',{'arms':totals,'api_passed':api.get('passed'),'guidance_decision':decision,'draft5_gate':gate});print(json.dumps(totals,ensure_ascii=False))
if __name__=='__main__':main()
