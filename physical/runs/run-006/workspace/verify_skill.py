"""Offline synthetic helper checks and transfer audit for this attempt."""
import ast
import hashlib
import json
import math
from pathlib import Path
import sys
import tempfile

sys.dont_write_bytecode = True
from skill.safety import require_healthy, require_preload_window, require_fresh_evidence, require_fixed_joint_hold
from skill.hardware import exclusive_command_owner

def rejects(fn):
    try:
        fn()
    except (RuntimeError, ValueError):
        return
    raise AssertionError('Invalid synthetic input was accepted')

sample={'Status':0,'Present_Temperature':20,'Present_Load':2}
require_healthy(sample,50,5,10)
for name in sample:
    rejects(lambda name=name: require_healthy({k:v for k,v in sample.items() if k!=name},50,5,10))
    for value in [math.nan,math.inf,-math.inf]:
        rejects(lambda name=name,value=value: require_healthy({**sample,name:value},50,5,10))
rejects(lambda: require_healthy(sample,50,5,0))
rejects(lambda: require_fixed_joint_hold([{}],{'synthetic':0},1))
rejects(lambda: require_fresh_evidence(observed_at=0,now=2,maximum_age=1))
rejects(lambda: require_preload_window([(0,10),(.1,0),(.2,10)],now=.2,maximum_age=1,
    minimum_duration=.1,maximum_gap=.2,baseline_preload=10,minimum_preload=1,maximum_fractional_loss=.5))
with tempfile.TemporaryDirectory() as directory:
    lock=Path(directory)/'owner.lock'
    with exclusive_command_owner(lock):
        def competing_owner():
            with exclusive_command_owner(lock):
                pass
        rejects(competing_owner)
    with exclusive_command_owner(lock):
        pass

root=Path('skill')
expected={'SKILL.md','hardware.py','safety.py'}
assert {p.name for p in root.iterdir()}==expected
audit=[]
for path in sorted(root.iterdir()):
    assert path.is_file() and not path.is_symlink()
    source=path.read_text()
    assert '\x00' not in source
    row={'file':str(path),'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
         'lines':len(source.splitlines())}
    if path.suffix=='.py':
        tree=ast.parse(source)
        row['numeric_constants']=sorted({repr(n.value) for n in ast.walk(tree)
            if isinstance(n,ast.Constant) and isinstance(n.value,(int,float))})
        assert not any(isinstance(n,ast.Call) and isinstance(n.func,ast.Name) and n.func.id in {'eval','exec'}
                       for n in ast.walk(tree))
    audit.append(row)
result={'synthetic_checks':'passed','transfer_files':audit,
        'manual_review':'Reviewed all three source files. Generic procedures and parameterized helpers only; no recorded joint state, scene geometry, images, task assignments, trajectories, calibration, or encoded data found.',
        'binary_symlink_generated_file_check':'passed',
        'limitations':'An automated scan supplements manual review and does not prove absence of encoded knowledge.'}
Path('evidence/skill_audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
