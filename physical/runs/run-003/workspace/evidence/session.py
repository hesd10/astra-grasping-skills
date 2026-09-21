"""Current-run bounded motor control and fresh evidence. Do not transfer."""
import sys, json, time, select, traceback
from pathlib import Path
import cv2
from lerobot.motors.feetech.feetech import FeetechMotorsBus
from lerobot.motors.motors_bus import Motor, MotorNormMode
from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig

OUT=Path(__file__).resolve().parent
LOG=(OUT/'session.jsonl').open('a',buffering=1)
buses={}; cameras={}; goals={}; initial={}; limits={}; step=0
def record(kind, **data):
    LOG.write(json.dumps(dict(time=time.time(),kind=kind,**data))+'\n')

def snap():
    return {role:{n:{r:b.read(r,n,normalize=False) for r in
        ['Present_Position','Present_Load','Present_Temperature','Present_Current','Status','Torque_Enable']}
        for n in b.motors} for role,b in buses.items()}

def health(s):
    for role,rows in s.items():
        for n,v in rows.items():
            if v['Status'] or not v['Torque_Enable']:
                raise RuntimeError(f'Motor status/torque fault: {role}/{n}: {v}')
            if abs(v['Present_Load']) > (200 if n=='6' else 450):
                raise RuntimeError(f'Effort bound: {role}/{n}: {v}')
            if role=='right' and abs(v['Present_Position']-initial[role][n])>30:
                raise RuntimeError(f'Observation arm drift: {n}')

def capture(label):
    paths={}
    for index,c in cameras.items():
        frame=c.async_read(timeout_ms=2000)
        path=OUT/f'{step:02d}-{label}-camera-{index}.png'
        if not cv2.imwrite(str(path),cv2.cvtColor(frame,cv2.COLOR_RGB2BGR)):
            raise RuntimeError('Image write failed')
        paths[index]=str(path)
    record('images',step=step,label=label,paths=paths)
    return paths

def stop_arm():
    b=buses.get('left')
    if b:
        for n in ['1','2','3','4','5']:
            p=b.read('Present_Position',n,normalize=False)
            b.write('Goal_Position',n,p,normalize=False)
            goals['left'][n]=p
    record('motion_stop_gripper_goal_preserved')

try:
    for role,port in [('left','/dev/ttyACM1'),('right','/dev/ttyACM0')]:
        b=FeetechMotorsBus(port,{str(i):Motor(i,'sts3215',MotorNormMode.DEGREES) for i in range(1,7)},calibration=None)
        b.connect(handshake=True); buses[role]=b
        initial[role]={};goals[role]={};limits[role]={}
        for n in b.motors:
            if b.read('Operating_Mode',n,normalize=False)!=0:
                raise RuntimeError('Non-position-mode arm motor')
            p=b.read('Present_Position',n,normalize=False)
            initial[role][n]=p
            limits[role][n]=(b.read('Min_Position_Limit',n,normalize=False),b.read('Max_Position_Limit',n,normalize=False))
            on=b.read('Torque_Enable',n,normalize=False)
            goals[role][n]=b.read('Goal_Position',n,normalize=False) if on else p
            if not on:
                b.write('Goal_Position',n,p,normalize=False)
            # SRAM only; no temperature or other persistent protection writes.
            b.write('Goal_Velocity',n,60,normalize=False)
            b.write('Acceleration',n,5,normalize=False)
            if role=='left':
                old=b.read('Torque_Limit',n,normalize=False)
                b.write('Torque_Limit',n,min(old,180 if n=='6' else 500),normalize=False)
            if not on:
                b.write('Torque_Enable',n,1,normalize=False)
    record('enabled',initial=initial,goals=goals,limits=limits)
    for index in [6,8,10]:
        c=OpenCVCamera(OpenCVCameraConfig(index_or_path=index,width=640,height=480,fps=30,fourcc='MJPG'))
        c.connect(); cameras[index]=c
    s=snap();health(s)
    print(json.dumps(dict(ready=True,state=s,images=capture('enabled'))),flush=True)
    last_log=0
    while True:
        s=snap();health(s)
        if time.monotonic()-last_log>1:
            record('telemetry',state=s);last_log=time.monotonic()
        if not select.select([sys.stdin],[],[],0.1)[0]:
            continue
        line=sys.stdin.readline()
        if not line: break
        command=json.loads(line);step+=1
        record('online_command',step=step,command=command,state=s)
        if command.get('exit'):
            print(json.dumps(dict(exiting=True,state=s)),flush=True);break
        target=dict(goals['left'])
        for n,d in command.get('delta',{}).items():
            if n not in target or abs(d)>120: raise ValueError('Invalid probe size')
            target[n]=s['left'][n]['Present_Position']+int(d)
            lo,hi=limits['left'][n]
            if not lo+5<=target[n]<=hi-5: raise ValueError('Live position limit margin')
        start=dict(goals['left'])
        duration=max([abs(target[n]-start[n])/45 for n in target]+[0.1])
        began=time.monotonic()
        while True:
            fraction=min(1,(time.monotonic()-began)/duration)
            for n in command.get('delta',{}):
                value=round(start[n]+fraction*(target[n]-start[n]))
                buses['left'].write('Goal_Position',n,value,normalize=False)
                goals['left'][n]=value
            s=snap();health(s);record('moving',step=step,state=s)
            if fraction>=1:break
            time.sleep(.05)
        end=time.monotonic()+float(command.get('hold',0.8))
        while time.monotonic()<end:
            s=snap();health(s);record('settling',step=step,state=s);time.sleep(.08)
        print(json.dumps(dict(step=step,goals=goals,state=s,images=capture(command.get('label','observed')))),flush=True)
except BaseException as exc:
    record('fault',error=repr(exc),traceback=traceback.format_exc())
    try:stop_arm()
    except Exception as nested:record('stop_error',error=repr(nested))
    print(json.dumps(dict(stopped=True,error=repr(exc))),flush=True)
finally:
    for c in cameras.values():
        if c.is_connected:c.disconnect()
    for b in buses.values():
        if b.is_connected:b.disconnect(disable_torque=False)
    record('disconnected_torque_preserved')
