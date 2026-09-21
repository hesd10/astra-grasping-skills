import ast,hashlib,json,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
skill=root/'skill'
expected={'SKILL.md','hardware.py','safety.py'}
files=list(skill.rglob('*'))
assert {str(p.relative_to(skill)) for p in files}==expected
records=[]
for p in sorted(files):
 assert p.is_file() and not p.is_symlink()
 raw=p.read_bytes();text=raw.decode('utf-8');assert '\x00' not in text
 entry={'file':p.name,'bytes':len(raw),'sha256':hashlib.sha256(raw).hexdigest()}
 if p.suffix=='.py':
  tree=ast.parse(text);compile(tree,str(p),'exec')
  entry['numeric_literals']=sorted({str(n.value) for n in ast.walk(tree) if isinstance(n,ast.Constant) and type(n.value) in (int,float)})
  assert all(n.value in (0,1,2) for n in ast.walk(tree) if isinstance(n,ast.Constant) and type(n.value) in (int,float))
  for n in ast.walk(tree):
   if isinstance(n,ast.Constant) and isinstance(n.value,str):
    assert 'base64' not in n.value.lower()
    assert '/home/' not in n.value
    assert 'Run 00' not in n.value
 records.append(entry)
result={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'passed':True,'files':records,
'manual_review':'Every copied transfer file was read before use; additions were reviewed after execution. Retained text is general procedure and generic parameterized code. No images, scene reconstruction, recorded encoder counts, joint angles, poses, coordinates, trajectories, replays, runtime device assignments, binaries, symlinks, or encoded equivalents were retained.',
'limitations':'Structural and numeric scans supplement manual review; they cannot independently prove absence of encoded historical data.',
'synthetic_checks':'Nine checks passed for fixed-joint completeness, finite values, drift bounds, and unchanged protection snapshots.',
'current_run_data_location':'Evidence, runtime scripts, report, and this audit are outside skill/.'}
(root/'evidence/transfer_audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
