import sys, json, time
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from skill.hardware import ReadOnlyFeetech
from lerobot.motors import Motor, MotorNormMode
registers=['Model_Number','Operating_Mode','Torque_Enable','Goal_Position','Present_Position','Present_Velocity','Present_Load','Present_Current','Present_Temperature','Present_Voltage','Status','Min_Position_Limit','Max_Position_Limit','Max_Temperature_Limit','Max_Torque_Limit','Torque_Limit','Goal_Velocity','Acceleration','Unloading_Condition']
result={'timestamp':time.time(),'buses':{}}
for port in ('/dev/ttyACM0','/dev/ttyACM1'):
    with ReadOnlyFeetech(port,{str(i):Motor(i,'sts3215',MotorNormMode.DEGREES) for i in range(1,7)}) as device:
        result['buses'][port]=device.snapshot(registers)
Path(__file__).with_name('initial_state.json').write_text(json.dumps(result,indent=2))
print(json.dumps(result,indent=2))
