from lab import LAB,sha,dump
import hashlib,json
new=(LAB/'fixtures/refactor/prompt.txt').read_text(encoding='utf-8')
sentence="Explicit new-helper contract: parse_money('1.005') must return Decimal('1.01'), rounded to cents; apply_discount and line_total must compute discounts from the unrounded input before rounding the unit price, so do not introduce double rounding. "
old=new.replace(sentence,'');row=json.loads((LAB/'raw/dflash128graph-refactor-0.summary.json').read_text(encoding='utf-8'))
assert hashlib.sha256(old.encode()).hexdigest()==row['prompt_sha256']
(LAB/'prompts/refactor-pilot-v1.txt').write_text(old,encoding='utf-8');(LAB/'prompts/refactor-v2.txt').write_text(new,encoding='utf-8')
print('Pilot prompt preserved; SHA matches original run.')
