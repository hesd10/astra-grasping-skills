"""Current-attempt low-level motor owner. No calibration, models, or IK."""
import sys, json, time, select, traceback
from pathlib import Path
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import cv2
from lerobot.motors.feetech.feetech import FeetechMotorsBus
from lerobot.motors.motors_bus import Motor, MotorNormMode
from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig

ROOT=Path(__file__).resolve().parents[1]/'evidence'
log=(ROOT/'control.jsonl').open('a',buffering=1)
def record(kind, data):
    log.write(json.dumps({'time':time.time(),'kind':kind,'data':data})+'\n')

class Session:
    def __init__(self):
        self.buses={}
        self.cameras={}
        self.fault=None
        self.moving=False
        motors={str(i):Motor(i,'sts3215',MotorNormMode.DEGREES) for i in range(1,7)}
        for side,port in [('left','/dev/ttyACM1'),('right','/dev/ttyACM0')]:
            bus=FeetechMotorsBus(port,motors,calibration=None)
            bus.connect(handshake=False)
            bus.set_baudrate(bus.default_baudrate)
            self.buses[side]=bus
        self.initial={side:{m:{r:b.read(r,m,normalize=False) for r in
            ['Present_Position','Goal_Position','Torque_Enable','Operating_Mode',
             'Min_Position_Limit','Max_Position_Limit','Max_Temperature_Limit']}
            for m in motors} for side,b in self.buses.items()}
        record('initial',self.initial)
        for side in self.initial.values():
            for sample in side.values():
                if sample['Torque_Enable']!=1 or sample['Operating_Mode']!=0:
                    raise RuntimeError('Unexpected initial torque or operating mode')
        self.goals={m:v['Goal_Position'] for m,v in self.initial['left'].items()}
        self.sample()
        for i in [6,8,10]:
            c=OpenCVCamera(OpenCVCameraConfig(index_or_path=i,width=640,height=480,fps=30,fourcc='MJPG'))
            c.connect()
            self.cameras[i]=c

    def sample(self):
        s={side:{m:{r:b.read(r,m,normalize=False) for r in
           ['Present_Position','Present_Load','Present_Temperature','Status','Torque_Enable']}
           for m in b.motors} for side,b in self.buses.items()}
        record('telemetry',s)
        self.last=s
        for side,rows in s.items():
            for m,v in rows.items():
                initial=self.initial[side][m]
                if v['Status'] or not v['Torque_Enable']:
                    raise RuntimeError(f'{side} {m} fault/torque state: {v}')
                if v['Present_Temperature'] >= initial['Max_Temperature_Limit']:
                    raise RuntimeError(f'{side} {m} reached existing hardware thermal limit')
                if abs(v['Present_Load']) > (240 if m=='6' else 450):
                    raise RuntimeError(f'{side} {m} excess load: {v}')
                if side=='right' and abs(v['Present_Position']-initial['Present_Position'])>15:
                    raise RuntimeError(f'Observation arm drift: {m} {v}')
        return s

    def snapshot(self,label):
        for i,c in self.cameras.items():
            frame=c.async_read(timeout_ms=2000)
            cv2.imwrite(str(ROOT/f'{label}_video{i}.jpg'),cv2.cvtColor(frame,cv2.COLOR_RGB2BGR))
        s=self.sample()
        (ROOT/f'{label}.json').write_text(json.dumps(s,indent=2))
        return s

    def freeze_arm(self):
        # Preserve gripper preload and observation-arm goals.
        b=self.buses.get('left')
        if b and b.is_connected:
            for m in ['1','2','3','4','5']:
                try:
                    p=b.read('Present_Position',m,normalize=False)
                    b.write('Goal_Position',m,p,normalize=False)
                    self.goals[m]=p
                except Exception as exc:
                    record('stop_error',str(exc))

    def command(self,cmd):
        record('command',cmd)
        label=cmd['label']
        if not label.replace('_','').isalnum():
            raise ValueError('Invalid evidence label')
        if cmd.get('delta'):
            if self.fault:
                raise RuntimeError('Fault latched; motion inhibited')
            s=self.sample()['left']
            targets={}
            for m,d in cmd['delta'].items():
                if m not in self.goals or abs(d)>240:
                    raise ValueError('Unpermitted motor or movement magnitude')
                p=s[m]['Present_Position']
                target=round(p+d)
                limits=self.initial['left'][m]
                if not limits['Min_Position_Limit']+5 <= target <= limits['Max_Position_Limit']-5:
                    raise ValueError('Target approaches current hardware travel limit')
                targets[m]=target
            b=self.buses['left']
            for m in targets:
                b.write('Goal_Velocity',m,60,normalize=False)
                b.write('Acceleration',m,5,normalize=False)
                if m=='6':
                    b.write('Torque_Limit',m,180,normalize=False)
            self.moving=True
            starts={m:s[m]['Present_Position'] for m in targets}
            n=max(1,int(max(abs(targets[m]-starts[m]) for m in targets)/4)+1)
            for step in range(1,n+1):
                for m,target in targets.items():
                    value=round(starts[m]+(target-starts[m])*step/n)
                    b.write('Goal_Position',m,value,normalize=False)
                    self.goals[m]=value
                self.sample()
                time.sleep(.1)
            self.moving=False
        end=time.monotonic()+cmd.get('hold',1)
        while time.monotonic()<end:
            self.sample()
            time.sleep(.2)
        return self.snapshot(label)

    def close(self):
        for c in self.cameras.values():
            if c.is_connected:c.disconnect()
        for b in self.buses.values():
            if b.is_connected:b.disconnect(disable_torque=False)

s=None
try:
    s=Session()
    print(json.dumps({'ready':True,'state':s.snapshot('owner_start')}),flush=True)
    last=time.monotonic()
    while True:
        ready,_,_=select.select([sys.stdin],[],[],.2)
        if ready:
            line=sys.stdin.readline()
            if not line:break
            cmd=json.loads(line)
            if cmd.get('quit'):
                print(json.dumps({'closed':True,'state':s.snapshot(cmd['label'])}),flush=True)
                break
            try:
                result=s.command(cmd)
                print(json.dumps({'label':cmd['label'],'state':result}),flush=True)
            except Exception as exc:
                s.fault=str(exc)
                s.freeze_arm()
                record('fault',traceback.format_exc())
                print(json.dumps({'fault':s.fault}),flush=True)
        elif time.monotonic()-last>.5:
            try:s.sample()
            except Exception as exc:
                if not s.fault:
                    s.fault=str(exc)
                    s.freeze_arm()
                    record('fault',traceback.format_exc())
                    print(json.dumps({'fault':s.fault}),flush=True)
            last=time.monotonic()
finally:
    if s:s.close()
    log.close()
