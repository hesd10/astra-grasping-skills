"""Explicit operator-requested release after the grasp attempt."""
import sys,json,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from skill.hardware import ReadOnlyFeetech,release_requested_torque
from lerobot.motors import Motor,MotorNormMode
out={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'reason':'Operator explicitly requested torque release to restore arm positions manually','arms':{}}
for side,port in [('left','/dev/ttyACM1'),('right','/dev/ttyACM0')]:
 try:
  motors={str(i):Motor(i,'sts3215',MotorNormMode.DEGREES) for i in range(1,7)}
  with ReadOnlyFeetech(port,motors) as reader:
   out['arms'][side]=release_requested_torque(reader.bus,list(motors))
 except Exception as exc:
  out['arms'][side]={'error':repr(exc)}
(root/'evidence/operator_torque_release.json').write_text(json.dumps(out,indent=2))
print(json.dumps(out,indent=2))
if not all(len(out['arms'][side])==6 and all(v.get('disabled') is True for v in out['arms'][side].values()) for side in ('left','right')):
 raise SystemExit('Torque release not fully verified')
