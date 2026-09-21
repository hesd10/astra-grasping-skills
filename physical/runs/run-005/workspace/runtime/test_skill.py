import sys,math
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from skill.safety import require_fixed_joint_hold,require_protection_unchanged
require_fixed_joint_hold([{'synthetic_joint':0.2},{'synthetic_joint':0.3}],{'synthetic_joint':0.1},0.25)
require_protection_unchanged({'synthetic_limit':7},{'synthetic_limit':7})
cases=[
 (lambda: require_fixed_joint_hold([],{'synthetic_joint':0},1),ValueError),
 (lambda: require_fixed_joint_hold([{}],{'synthetic_joint':0},1),ValueError),
 (lambda: require_fixed_joint_hold([{'synthetic_joint':math.nan}],{'synthetic_joint':0},1),ValueError),
 (lambda: require_fixed_joint_hold([{'synthetic_joint':3}],{'synthetic_joint':0},1),RuntimeError),
 (lambda: require_fixed_joint_hold([{'synthetic_joint':0}],{'synthetic_joint':0},-1),ValueError),
 (lambda: require_protection_unchanged({'synthetic_limit':7},{'synthetic_limit':8}),RuntimeError),
 (lambda: require_protection_unchanged({},{}),ValueError),
]
for f,expected in cases:
 try:f()
 except expected:pass
 else:raise AssertionError('Expected rejection')
print('Nine synthetic safety checks passed.')
