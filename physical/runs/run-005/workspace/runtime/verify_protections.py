import sys,json,time
from pathlib import Path
root=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(root))
from skill.hardware import ReadOnlyFeetech
from skill.safety import require_protection_unchanged
from lerobot.motors import Motor,MotorNormMode
initial=json.loads((root/'evidence/initial_hardware.json').read_text())
regs=['Max_Temperature_Limit','Min_Position_Limit','Max_Position_Limit','Torque_Limit','Max_Torque_Limit','Unloading_Condition']
out={'time':time.time(),'arms':{}}
for port in ('/dev/ttyACM0','/dev/ttyACM1'):
 motors={str(i):Motor(i,'sts3215',MotorNormMode.DEGREES) for i in range(1,7)}
 with ReadOnlyFeetech(port,motors) as reader: after=reader.snapshot(regs)
 before={n:{k:initial['motors'][port]['data'][n][k] for k in regs} for n in motors}
 require_protection_unchanged(before,after)
 out['arms'][port]={'unchanged':True,'registers':after}
(root/'evidence/protection_closeout.json').write_text(json.dumps(out,indent=2))
print('Protection registers unchanged on both arms; no actuator writes.')
