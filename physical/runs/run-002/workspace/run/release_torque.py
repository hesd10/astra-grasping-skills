"""Current attempt: operator-requested torque release after controller exit."""
import json, time
from pathlib import Path
from lerobot.motors.feetech.feetech import FeetechMotorsBus
from lerobot.motors.motors_bus import Motor, MotorNormMode

result={'timestamp':time.time(),'authorization':'Operator ended attempt and requested torque removal','arms':{}}
for side,port in [('left','/dev/ttyACM1'),('right','/dev/ttyACM0')]:
    bus=FeetechMotorsBus(port,{str(i):Motor(i,'sts3215',MotorNormMode.DEGREES) for i in range(1,7)},calibration=None)
    row={}
    try:
        bus.connect(handshake=False)
        bus.set_baudrate(bus.default_baudrate)
        for motor in bus.motors:
            try:
                bus.write('Torque_Enable',motor,0,normalize=False)
                row[motor]=bus.read('Torque_Enable',motor,normalize=False)
            except Exception as exc:
                row[motor]={'error':str(exc)}
    finally:
        if bus.is_connected:bus.disconnect(disable_torque=False)
    result['arms'][side]=row
result['all_arm_torque_off']=all(value==0 for rows in result['arms'].values() for value in rows.values())
Path('evidence/torque_release.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result),flush=True)
if not result['all_arm_torque_off']:raise SystemExit(1)
