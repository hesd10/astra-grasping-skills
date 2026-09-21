import sys,json,time,traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from skill.hardware import enumerate_current_devices, discover_motor_models,ReadOnlyFeetech,capture_fresh
from lerobot.motors import Motor, MotorNormMode
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
root=Path(__file__).resolve().parents[1]/'evidence'
out={'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()),'devices':enumerate_current_devices(),'motors':{},'cameras':{}}
registers=['Operating_Mode','Present_Position','Goal_Position','Present_Load','Present_Temperature','Status','Torque_Enable','Max_Temperature_Limit','Min_Position_Limit','Max_Position_Limit','Torque_Limit','Max_Torque_Limit','Present_Voltage','Goal_Velocity','Acceleration','Unloading_Condition']
for port in ('/dev/ttyACM0','/dev/ttyACM1'):
 try:
  found=discover_motor_models(port)
  print(port,found,flush=True)
  models={777:'sts3215',2825:'sts3250',11272:'sm8512bl',1284:'scs0009'}
  motors={str(i):Motor(i,models[m],MotorNormMode.DEGREES) for i,m in found.items()}
  with ReadOnlyFeetech(port,motors) as reader: data=reader.snapshot(registers)
  out['motors'][port]={'models':found,'data':data}
  print(json.dumps(data),flush=True)
 except Exception as e:
  out['motors'][port]={'error':repr(e)};print(traceback.format_exc(),flush=True)
for index in (4,6,8,10):
 try:
  p=capture_fresh(OpenCVCameraConfig(index_or_path=index,width=640,height=480,fps=30,fourcc='MJPG'),root/f'initial_camera_{index}.jpg',5000)
  out['cameras'][str(index)]=str(p)
 except Exception as e: out['cameras'][str(index)]={'error':repr(e)};print(traceback.format_exc(),flush=True)
(root/'initial_hardware.json').write_text(json.dumps(out,indent=2))
print('EVIDENCE',root/'initial_hardware.json',flush=True)
