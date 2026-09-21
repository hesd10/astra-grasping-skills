"""Offline checks for safety-relevant generic helpers; no real hardware writes."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skill.hardware import release_requested_torque, require_evidence_destination
from skill.safety import require_side_enclosure, require_lift_evidence

class FakeBus:
    def __init__(self): self.attempts=[]
    def write(self, register, motor, value, normalize):
        self.attempts.append(motor)
        assert register == 'Torque_Enable' and value == 0 and normalize is False
        if motor == 'failed': raise OSError('Synthetic write failure')
    def read(self, register, motor, normalize): return 0

bus=FakeBus()
result=release_requested_torque(bus,['failed','healthy'])
assert bus.attempts==['failed','healthy']
assert not result['failed']['disabled'] and result['healthy']['disabled']

for kwargs in [dict(opposing_side_walls_engaged=False,upper_edges_clear=True,sufficient_insertion=True,independent_view_confirms=True,object_moved=False),dict(opposing_side_walls_engaged=True,upper_edges_clear=True,sufficient_insertion=True,independent_view_confirms=True,object_moved=True)]:
    try: require_side_enclosure(**kwargs)
    except RuntimeError: pass
    else: raise AssertionError('Unsafe enclosure accepted')
require_side_enclosure(opposing_side_walls_engaged=True,upper_edges_clear=True,sufficient_insertion=True,independent_view_confirms=True,object_moved=False)
try:
    require_lift_evidence(all_bottom_corners_clear=False,independent_view_confirms=True,visible_support_gap=True,slipping=False,hold_duration=10,required_duration=5)
except RuntimeError: pass
else: raise AssertionError('Partial clearance accepted')
try: require_evidence_destination(Path(__file__).resolve().parents[1]/'skill'/'observation.jpg')
except ValueError: pass
else: raise AssertionError('Transfer evidence destination accepted')
print('PASS: release continues after failure and verifies readback; ambiguous enclosure, partial clearance, and transfer evidence writes are rejected.')
