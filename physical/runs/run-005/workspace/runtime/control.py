"""Current-run low-level motor owner. All measured state remains in evidence/."""
import sys,json,time,select,traceback,os
from pathlib import Path
import cv2
from lerobot.motors import Motor,MotorNormMode
from lerobot.motors.feetech.feetech import FeetechMotorsBus
from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
root=Path(__file__).resolve().parents[1]/'evidence'
log=(root/'control.jsonl').open('a',buffering=1)
buses={};cameras={};goals={};initial={};limits={};count=0;fault=None;last={}
def record(event,**data):
 row=dict(time=time.time(),event=event,**data);log.write(json.dumps(row)+'\n');return row
def observe():
 result={}
 for side,b in buses.items():
  result[side]={r:b.sync_read(r,normalize=False) for r in ('Present_Position','Present_Load','Present_Temperature','Status','Torque_Enable')}
 record('telemetry',data=result)
 return result
def check(data):
 for side,d in data.items():
  for n in buses[side].motors:
   if d['Status'][n]: raise RuntimeError(f'{side}:{n} status {d["Status"][n]}')
   if abs(d['Present_Load'][n])>(150 if side=='left' and n=='6' else 450): raise RuntimeError(f'{side}:{n} excess effort')
   if d['Torque_Enable'][n]!=1: raise RuntimeError(f'{side}:{n} lost torque')
   if side=='right' and abs(d['Present_Position'][n]-initial[side][n])>16: raise RuntimeError('Observation arm drift')
def capture(label):
 paths=[]
 for i,c in cameras.items():
  frame=c.read_latest(max_age_ms=1000)
  p=root/f'{count:03d}_{label}_cam{i}.jpg'
  cv2.imwrite(str(p),cv2.cvtColor(frame,cv2.COLOR_RGB2BGR));paths.append(str(p))
 record('images',paths=paths);return paths
try:
 for side,port in [('left','/dev/ttyACM1'),('right','/dev/ttyACM0')]:
  b=FeetechMotorsBus(port,{str(i):Motor(i,'sts3215',MotorNormMode.DEGREES) for i in range(1,7)},calibration=None)
  b.connect(handshake=False);b.set_baudrate(b.default_baudrate);buses[side]=b
  assert all(b.ping(n)==777 for n in b.motors)
  limits[side]={n:{r:b.read(r,n,normalize=False) for r in ('Min_Position_Limit','Max_Position_Limit','Operating_Mode')} for n in b.motors}
  assert all(v['Operating_Mode']==0 for v in limits[side].values())
  initial[side]=b.sync_read('Present_Position',normalize=False)
  goals[side]=b.sync_read('Goal_Position',normalize=False)
  enabled=b.sync_read('Torque_Enable',normalize=False)
  for n in b.motors:
   if not enabled[n]:
    goals[side][n]=initial[side][n]
    b.write('Goal_Position',n,goals[side][n],normalize=False)
    b.write('Torque_Enable',n,1,normalize=False)
 record('initialize_hold',initial=initial,goals=goals,limits=limits,pid=os.getpid())
 for i in (6,8,10):
  c=OpenCVCamera(OpenCVCameraConfig(index_or_path=i,width=640,height=480,fps=30,fourcc='MJPG'))
  c.connect();c.async_read(timeout_ms=5000);cameras[i]=c
 last=observe();check(last)
 print(json.dumps(dict(ready=True,pid=os.getpid(),data=last,images=capture('hold'))),flush=True)
 while True:
  if not select.select([sys.stdin],[],[],0.2)[0]:
   if fault is None:
    try:last=observe();check(last)
    except Exception as e:
     fault=repr(e);record('fault',error=fault);print('FAULT '+fault,flush=True)
   continue
  line=sys.stdin.readline()
  if not line: record('input_closed');break
  try:
   cmd=json.loads(line);count+=1;record('decision',number=count,command=cmd)
   if cmd['op']=='quit':
    print(json.dumps(dict(stopped=True,goals=goals,data=observe(),images=capture('final'))),flush=True);break
   if cmd['op']=='status':
    last=observe();print(json.dumps(dict(number=count,fault=fault,data=last,goals=goals,images=capture('status'))),flush=True);continue
   if fault:raise RuntimeError('Motion inhibited after fault: '+fault)
   if cmd['op']!='move':raise ValueError('Unknown operation')
   delta={str(k):int(v) for k,v in cmd['delta'].items()};duration=float(cmd.get('seconds',2))
   if not 1<=duration<=10:raise ValueError('Duration out of bound')
   if not delta or not set(delta)<=set(buses['left'].motors) or max(abs(v) for v in delta.values())>120:raise ValueError('Segment out of bound')
   start=goals['left'].copy();dest=start.copy()
   for n,d in delta.items():
    dest[n]+=d
    lim=limits['left'][n]
    if not lim['Min_Position_Limit']<=dest[n]<=lim['Max_Position_Limit']: raise ValueError('Target outside live motor limit')
    if abs(d)/duration>50:raise ValueError('Command rate exceeds bound')
   b=buses['left'];t=time.monotonic()
   while True:
    u=min(1,(time.monotonic()-t)/duration)
    vals={n:round(start[n]+(dest[n]-start[n])*u) for n in delta}
    b.sync_write('Goal_Position',vals,normalize=False);goals['left'].update(vals)
    last=observe();check(last)
    if u>=1:break
    time.sleep(0.08)
   time.sleep(0.5);last=observe();check(last)
   print(json.dumps(dict(number=count,data=last,goals=goals,images=capture('move'))),flush=True)
  except Exception as e:
   fault=repr(e);record('fault',error=fault);print('FAULT '+fault,flush=True)
finally:
 for c in cameras.values():
  if c.is_connected:c.disconnect()
 for b in buses.values():
  if b.is_connected:b.disconnect(disable_torque=False)
 record('closed_preserving_hold');log.close()
