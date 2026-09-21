import sys,json,time
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from skill.hardware import ReadOnlyFeetech
from lerobot.motors import Motor, MotorNormMode
result={'time':time.time(),'buses':{}}
for role,port in [('left','/dev/ttyACM1'),('right','/dev/ttyACM0')]:
 with ReadOnlyFeetech(port,{str(i):Motor(i,'sts3215',MotorNormMode.DEGREES) for i in range(1,7)}) as d:
  result['buses'][role]=d.snapshot(['Goal_Position','Present_Position','Torque_Enable','Present_Load','Present_Temperature','Status','Max_Temperature_Limit'])
Path(__file__).with_name('final_readback.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
