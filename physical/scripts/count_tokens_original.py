import json,pathlib,collections,hashlib
ROOT=pathlib.Path('/home/robot-operator/.codex/sessions/2026/09/16')
OUT=pathlib.Path(__file__).resolve().parent
IDS=['01a0a5db-7f62-7532-badc-2f63e10b1d9a','01a0a7a5-cbbe-7192-bb8a-b2078a098792','01a0a7c1-9d84-78d1-8c82-ef23b8d91342','01a0a7d9-be53-7643-9aa7-3634598d2658','01a0a802-5a02-7662-b98e-69fcbfbffd8f','01a0a84e-4a3e-7e51-9c3f-a0e7d325483f']
KEYS=['input_tokens','cached_input_tokens','cache_write_input_tokens','output_tokens','reasoning_output_tokens','total_tokens']
def sums(records):
 d={k:sum(r['usage'].get(k,0) for r in records) for k in KEYS}
 d['uncached_input_tokens']=d['input_tokens']-d['cached_input_tokens'];d['requests']=len(records)
 return d
runs=[]
for num,tid in enumerate(IDS,1):
 records={};sources=[];turns={};last=None
 for path in sorted(ROOT.glob('*'+tid+'*.jsonl')):
  sources.append({'filename':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest()})
  for line,text in enumerate(path.open(),1):
   r=json.loads(text);p=r.get('payload',{})
   if r['type']=='turn_context':turns.setdefault(p['turn_id'],{'turn_id':p['turn_id'],'model':p.get('model'),'effort':p.get('effort')})
   if r['type']=='token_usage_record':
    rid=p['response_id']
    if rid in records:assert records[rid]['usage']==p['usage'];continue
    assert p['usage']['total_tokens']==p['usage']['input_tokens']+p['usage']['output_tokens']
    records[rid]={'response_id':rid,'turn_id':p['turn_id'],'timestamp':r['timestamp'],'usage':p['usage'],'source':path.name,'line':line}
    if last is None or r['timestamp']>last[0]:last=(r['timestamp'],p['thread_token_usage'])
 allr=sorted(records.values(),key=lambda r:r['timestamp'])
 ordered=list(dict.fromkeys(r['turn_id'] for r in allr))
 for idx,t in enumerate(ordered):
  rr=[r for r in allr if r['turn_id']==t]
  turns[t].update({'first_usage_utc':rr[0]['timestamp'],'last_usage_utc':rr[-1]['timestamp'],'usage':sums(rr)})
  if num==5:phase='experiment' if idx==0 else ('post_release' if idx==1 else ('cross_run_retrospective' if idx==7 else 'followup'))
  elif num in [1,4]:phase='experiment' if idx<2 else 'post_release'
  elif num==6:phase='experiment' if idx==0 else 'post_release'
  else:phase='experiment'
  turns[t]['phase']=phase
 total=sums(allr)
 assert all(total[k]==last[1].get(k,0) for k in KEYS),(num,total,last)
 exp=sums([r for r in allr if turns[r['turn_id']]['phase']=='experiment'])
 runs.append({'run':f'Run {num:03}','thread_id':tid,'sources':sources,'experiment':exp,'whole_session':total,'turns':[turns[t] for t in ordered],'records':allr})
result={'definition':'Experiment includes setup, physical execution, corrections/continuation, failure termination where applicable, report, skill audit and commit. Separate post-attempt release and later questions/retrospective are excluded. Sum unique token_usage_record payload.usage by response_id; checked against final thread_token_usage. Cached input is included in input; reasoning output is included in output. Logged usage only, not billing or unique text length.','runs':runs}
(OUT/'token_usage.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))
for r in runs:
 print(r['run'],'EXPERIMENT',r['experiment'],'SESSION',r['whole_session'])
 for t in r['turns']:print(' ',t['phase'],t['usage']['total_tokens'],t['first_usage_utc'])
print('TOTAL', {k:sum(r['experiment'][k] for r in runs) for k in runs[0]['experiment']})
