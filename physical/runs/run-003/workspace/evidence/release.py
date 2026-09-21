"""Operator-requested shutdown for this session, after motion-owner exit."""
import json, sys, time
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
sys.dont_write_bytecode=True
sys.path.insert(0,str(ROOT/'skill'))
from hardware import ReadOnlyFeetech, release_requested_torque
from lerobot.motors.motors_bus import Motor, MotorNormMode

result={'time':time.time(),'controller_processes_found':[],'arms':{}}
for role,port in [('left','/dev/ttyACM1'),('right','/dev/ttyACM0')]:
    try:
        motors={str(i):Motor(i,'sts3215',MotorNormMode.DEGREES) for i in range(1,7)}
        with ReadOnlyFeetech(port,motors) as device:
            release=release_requested_torque(device.bus,list(motors))
            result['arms'][role]={'release':release,'verified':device.snapshot(
                ['Torque_Enable','Max_Temperature_Limit','Present_Temperature','Status'])}
    except Exception as exc:
        result['arms'][role]={'error':repr(exc)}
result['finished']=time.time()
(ROOT/'evidence'/'torque-release.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
if not all(all(v['disabled'] for v in arm.get('release',{}).values())
           and len(arm.get('release',{}))==6 for arm in result['arms'].values()):
    raise SystemExit('Torque release verification incomplete')
