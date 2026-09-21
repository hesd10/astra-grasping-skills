"""Current-run audit and synthetic checks; not part of the transfer skill."""
import ast, hashlib, importlib.util, json, sys
from pathlib import Path
sys.dont_write_bytecode=True
root=Path(__file__).resolve().parents[1]
skill=root/'skill'
expected={'SKILL.md','hardware.py','safety.py'}
files=list(skill.iterdir())
assert {p.name for p in files}==expected
report={'files':{},'synthetic_checks':[],'manual_review':'Every transfer source reviewed. General procedures and parameterized helpers only; no images, observation data, device assignments, recorded motor states, targets, coordinates, trajectories, replays, binary payloads, or encoded equivalents.'}
for p in files:
 assert p.is_file() and not p.is_symlink()
 content=p.read_text()
 if p.suffix=='.py': ast.parse(content)
 report['files'][p.name]={'bytes':p.stat().st_size,'sha256':hashlib.sha256(p.read_bytes()).hexdigest()}
spec=importlib.util.spec_from_file_location('safety',skill/'safety.py'); safety=importlib.util.module_from_spec(spec); spec.loader.exec_module(safety)
safety.require_goal_continuity({'synthetic_motor':1.0},{'synthetic_motor':1.0})
report['synthetic_checks'].append('Equal synthetic goals accepted')
try: safety.require_goal_continuity({'synthetic_motor':1.0},{'synthetic_motor':2.0})
except RuntimeError: report['synthetic_checks'].append('Discontinuous synthetic goals rejected')
else: raise AssertionError('Discontinuity was accepted')
try: safety.require_metric_clearance(verified_reference=False,lower_bound=2,required_clearance=1)
except RuntimeError: report['synthetic_checks'].append('Unverified metric reference rejected')
else: raise AssertionError('Unverified metric reference was accepted')
safety.require_metric_clearance(verified_reference=True,lower_bound=2,required_clearance=1)
report['synthetic_checks'].append('Valid synthetic metric bound accepted')
(root/'evidence'/'skill_audit.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
