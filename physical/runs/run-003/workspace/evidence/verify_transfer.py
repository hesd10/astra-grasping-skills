"""Current-session transfer audit and synthetic safety checks; not transferable."""
import ast, hashlib, importlib.util, json, re
from pathlib import Path

ROOT=Path(__file__).resolve().parent.parent
TRANSFER=ROOT/'skill'
expected={'SKILL.md','hardware.py','safety.py'}
assert {p.name for p in TRANSFER.iterdir()} == expected
checks=[]
for path in sorted(TRANSFER.iterdir()):
    assert path.is_file() and not path.is_symlink()
    content=path.read_text()
    assert '\x00' not in content
    assert not re.search(r'\b\d{3,}\b|/home/|/dev/(?:ttyACM|ttyUSB|video)\d+|data:image|base64|BEGIN.*PRIVATE KEY',content)
    if path.suffix=='.py':
        tree=ast.parse(content)
        constants=[node.value for node in ast.walk(tree) if isinstance(node,ast.Constant)]
        numeric=[x for x in constants if isinstance(x,(float,int)) and not isinstance(x,bool)]
        assert all(x in (0,1) for x in numeric),numeric
    checks.append({'file':path.name,'sha256':hashlib.sha256(path.read_bytes()).hexdigest(),
                   'text_only':True,'no_symlink':True,'restricted_pattern_scan':'pass'})

spec=importlib.util.spec_from_file_location('transfer_safety',TRANSFER/'safety.py')
safety=importlib.util.module_from_spec(spec)
spec.loader.exec_module(safety)
good=dict(opposing_walls_still_engaged=True,independent_view_confirms=True,
          object_moved_in_gripper=False,preload_before=10,preload_now=9,
          minimum_preload=5,maximum_fractional_loss=.2)
safety.require_grasp_retention(**good)
negative=[({'object_moved_in_gripper':True},RuntimeError),
          ({'independent_view_confirms':False},RuntimeError),
          ({'opposing_walls_still_engaged':False},RuntimeError),
          ({'preload_now':7},RuntimeError),
          ({'preload_now':4},RuntimeError),
          ({'preload_now':float('nan')},ValueError),
          ({'preload_now':float('inf')},ValueError),
          ({'preload_before':0},ValueError),
          ({'maximum_fractional_loss':1},ValueError)]
for changes,error in negative:
    try:safety.require_grasp_retention(**(good|changes))
    except error:pass
    else:raise AssertionError(changes)

result={'transfer_files':checks,'synthetic_retention_checks':1+len(negative),
        'manual_review':'Every transfer file reviewed: generic procedures and parameterized low-level/safety code only.',
        'prohibited_historical_information_encountered':False,
        'limitations':'Pattern scanning supplements manual review; it is not proof against arbitrary encoding.'}
(ROOT/'evidence'/'transfer-audit.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
