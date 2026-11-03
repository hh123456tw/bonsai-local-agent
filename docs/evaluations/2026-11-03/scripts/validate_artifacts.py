"""Audit completed coverage and report integrity without sending model requests."""
import collections,hashlib,json,re
from lab import LAB,existing,sha,dump
from context import grade

def main():
 expected=sha(LAB/'prompts/short.txt');latest={r['key']:r for r in existing('benchmark') if r.get('case')!='short' or r.get('prompt_sha256')==expected}
 good=[r for r in latest.values() if r.get('ok')];counts=collections.Counter((r['profile'],r['case'],r['output_limit'],r['cache']) for r in good)
 for p in ('dflash128graph','dflash144','base256','control128off'):
  for case,limit in [('short',x) for x in (256,512,1024)]+[(str(x),256) for x in (8192,32768,65536,98304)]:
   for cache in ('cold','hot'):assert counts[p,case,limit,cache]==3
 assert all(r['actual_output_matches'] and r['cache_valid'] for r in good)
 for r in good:
  path=LAB/'prompts'/('short.txt' if r['case']=='short' else f'long-{r["case"]}.txt')
  # Requests hash the UTF-8 message after universal-newline reading; Windows
  # on-disk CRLF hashes are separately retained in prompt_inventory.
  assert r['prompt_sha256']==hashlib.sha256(path.read_text(encoding='utf-8').encode()).hexdigest()
 coding={r['key']:r for r in existing('coding')+existing('coding-audit')};formal=[x for x in coding.values() if x['task']!='refactor' or x['prompt_sha256']==sha(LAB/'fixtures/refactor/prompt.txt')]
 for r in formal:
  assert not r['protected_files_changed']
  if r['passed']:assert r['acceptance']['passed'] and r['public_tests_passed'] and r['agent_ran_tests']
 contexts={x['key']:x for x in existing('context')};assert len(contexts)==12
 for r in contexts.values():
  assert len(r['rounds'])==4
  expected_values=json.loads((LAB/'prompts'/f'context-{r["target"]}.json').read_text())['expected']
  for reply in r['rounds']:assert reply['correct_by_key']==grade(reply['text'],expected_values)
 compat=json.loads((LAB/'compatibility.json').read_text());assert not compat.get('failed');assert compat['openai_tool_roundtrip']['ok'] and compat['anthropic_tool_roundtrip']['ok'];assert compat['opencode_actual_task']['external_pass'];assert compat['opencode_effective_build']['steps_present'] is False
 report=(LAB/'REPORT.md').read_text(encoding='utf-8');assert '實驗進行中' not in report
 for label,path in re.findall(r'\[([^\]]+)\]\(([^)]+)\)',report):
  if not path.startswith(('http:','https:','#')):assert (LAB/path).exists(),(label,path)
 columns=None;tables=0
 for line in report.splitlines():
  if line.startswith('| '):
   n=line.count('|')
   if columns is None:columns=n;tables+=1
   assert n==columns,('Markdown table column mismatch',line)
  else:columns=None
 dump(LAB/'artifact-validation.json',{'native_samples':len(good),'formal_coding_runs':len(formal),'context_queries':sum(len(x['rounds']) for x in contexts.values()),'markdown_tables':tables,'native_fixed_output_and_cache_verified':True,'coverage_verified':True,'protected_files_unchanged':True,'context_grades_recomputed':True,'report_local_links_valid':True,'report_table_columns_valid':True})
 print('Coverage, grading, protected files, report links and tables verified.')
if __name__=='__main__':main()
