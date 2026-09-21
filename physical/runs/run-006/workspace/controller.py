"""This run's command owner. Targets and observations never belong in skill/."""
import sys
sys.dont_write_bytecode = True
import json, time, math, os, traceback
from pathlib import Path
import cv2
from lerobot.motors import Motor, MotorNormMode
from lerobot.motors.feetech.feetech import FeetechMotorsBus
from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from skill.safety import (require_healthy, require_fixed_joint_hold,
                          require_goal_continuity, require_fresh_evidence,
                          require_preload_window, require_side_enclosure,
                          require_contact_evidence)

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'evidence'
QUEUE=ROOT/'commands'
QUEUE.mkdir(exist_ok=True)
NAMES=[str(i) for i in range(1,7)]
FIELDS=['Present_Position','Present_Load','Present_Temperature','Status','Torque_Enable']
PROTECT=['Max_Temperature_Limit','Max_Torque_Limit','Torque_Limit','Protection_Current',
         'Unloading_Condition','Overload_Torque','Protective_Torque','Protection_Time']

class Owner:
    def __init__(self):
        self.buses={}
        self.cameras={}
        self.fault=None
        self.preload=[]
        self.retention=None
        self.latest_visual=None
        self.loaded=False
        self.log=(OUT/'monitor.jsonl').open('a',buffering=1)
        for role,port in [('left','/dev/ttyACM1'),('right','/dev/ttyACM0')]:
            bus=FeetechMotorsBus(port,{n:Motor(int(n),'sts3215',MotorNormMode.DEGREES) for n in NAMES},calibration=None)
            bus.connect(handshake=False)
            bus.set_baudrate(bus.default_baudrate)
            self.buses[role]=bus
        self.protections=self.read_protections()
        self.right_reference=self.buses['right'].sync_read('Present_Position',normalize=False)
        self.right_goals=self.buses['right'].sync_read('Goal_Position',normalize=False)
        self.goals=self.buses['left'].sync_read('Goal_Position',normalize=False)
        for index in [6,8,10]:
            cam=OpenCVCamera(OpenCVCameraConfig(index_or_path=index,width=640,height=480,fps=30,fourcc='MJPG'))
            cam.connect()
            self.cameras[index]=cam
        self.event('ready',{'pid':os.getpid(),'protections':self.protections,'right_reference':self.right_reference,'right_goals':self.right_goals,'left_goals':self.goals})

    def event(self,kind,data):
        row={'kind':kind,'time':time.time(),'mono':time.monotonic(),'data':data}
        self.log.write(json.dumps(row)+'\n')
        if kind!='sample': print(json.dumps(row),flush=True)

    def read_protections(self):
        return {role:{n:{r:bus.read(r,n,normalize=False) for r in PROTECT} for n in NAMES} for role,bus in self.buses.items()}

    def sample(self):
        data={role:{r:bus.sync_read(r,normalize=False) for r in FIELDS} for role,bus in self.buses.items()}
        now=time.monotonic()
        self.event('sample',data)
        for role,fields in data.items():
            for n in NAMES:
                s={r:fields[r][n] for r in FIELDS}
        require_fixed_joint_hold([data['right']['Present_Position']],self.right_reference,12)
        if self.buses['right'].sync_read('Goal_Position',normalize=False)!=self.right_goals:
            raise RuntimeError('Observation arm goal changed')
        if self.loaded and self.retention:
            self.preload.append((now,data['left']['Present_Load']['6']))
            self.preload=self.preload[-100:]
            if len(self.preload)>1:
                require_preload_window(self.preload,now=now,maximum_age=1,minimum_duration=.01,
                                      maximum_gap=1,**self.retention)
        self.latest=data
        return data

    def snapshot(self,label):
        times={}
        for index,cam in self.cameras.items():
            frame=cam.read()
            times[str(index)]=time.monotonic()
            cv2.imwrite(str(OUT/f'{label}_camera_{index}.jpg'),cv2.cvtColor(frame,cv2.COLOR_RGB2BGR))
        self.latest_visual=min(times.values())
        data=self.sample()
        result={'label':label,'acquired':times,'telemetry':data,'goals':self.goals,'fault':self.fault}
        (OUT/f'{label}.json').write_text(json.dumps(result,indent=2))
        self.event('snapshot',result)

    def enable(self):
        self.sample()
        b=self.buses['left']
        for n in NAMES:
            if not b.read('Torque_Enable',n,normalize=False):
                pos=b.read('Present_Position',n,normalize=False)
                b.write('Goal_Position',n,pos,normalize=False)
                self.goals[n]=pos
                b.write('Torque_Enable',n,1,normalize=False)
        self.event('enabled',self.goals)

    def move(self,cmd):
        if self.fault: raise RuntimeError('Latched fault: '+self.fault)
        self.sample()
        require_fresh_evidence(observed_at=self.latest_visual,now=time.monotonic(),maximum_age=180)
        if cmd.get('loaded') and not self.loaded: raise RuntimeError('Loaded movement needs independent enclosure and retention assessment')
        b=self.buses['left']
        start=b.sync_read('Goal_Position',normalize=False)
        require_goal_continuity(self.goals,start)
        delta=cmd['delta']
        if self.loaded and '6' in delta: raise RuntimeError('Do not alter a verified grip during a loaded move')
        if not delta or set(delta)-set(NAMES): raise ValueError('Invalid joints')
        if any(not math.isfinite(v) or abs(v)>160 for v in delta.values()): raise ValueError('Segment too large')
        if any(self.latest['left']['Torque_Enable'][n]!=1 for n in NAMES): raise RuntimeError('Left torque is not enabled')
        target={n:int(start[n]+delta.get(n,0)) for n in NAMES}
        for n in delta:
            low=b.read('Min_Position_Limit',n,normalize=False)
            high=b.read('Max_Position_Limit',n,normalize=False)
            if not low<=target[n]<=high: raise ValueError('Goal outside live motor limits')
        duration=max(float(cmd.get('duration',2)),max(abs(v) for v in delta.values())/45)
        steps=math.ceil(duration/.1)
        self.event('motion_start',{'command':cmd,'start':start,'target':target})
        begin=time.monotonic()
        for step in range(1,steps+1):
            self.sample()
            f=step/steps
            values={n:round(start[n]+(target[n]-start[n])*f) for n in delta}
            b.sync_write('Goal_Position',values,normalize=False)
            self.goals.update(values)
            time.sleep(max(0,begin+step*duration/steps-time.monotonic()))
        for _ in range(5): self.sample(); time.sleep(.1)
        self.event('motion_done',{'label':cmd['label'],'actual':self.latest['left']['Present_Position']})

    def authorize_contact(self,cmd):
        if self.fault: raise RuntimeError('Latched fault: '+self.fault)
        require_fresh_evidence(observed_at=self.latest_visual,now=time.monotonic(),maximum_age=120)
        require_side_enclosure(**cmd['enclosure'])
        self.sample()
        observed=self.latest['left']
        minimum=self.buses['left'].read('Min_Position_Limit','6',normalize=False)
        require_contact_evidence(sustained_load=observed['Present_Load']['6'],
            tracking_shortfall=observed['Present_Position']['6']-self.goals['6'],
            distance_from_closed_limit=observed['Present_Position']['6']-minimum,
            minimum_load=40,minimum_shortfall=8,closed_limit_margin=80,visible_enclosure=True)
        self.retention=cmd['retention']
        self.preload=[]
        self.loaded=True
        for _ in range(12): self.sample(); time.sleep(.1)
        self.event('contact_authorized',cmd)

    def run(self):
        self.snapshot('ready_'+str(os.getpid()))
        try:
            while True:
                pending=sorted(QUEUE.glob('*.json'))
                for path in pending:
                    cmd=json.loads(path.read_text())
                    path.rename(path.with_suffix('.taken'))
                    self.event('command',cmd)
                    try:
                        if cmd['op']=='exit':
                            self.event('final_protections',self.read_protections())
                            self.snapshot(cmd['label'])
                            return
                        if cmd['op']=='enable': self.enable()
                        elif cmd['op']=='move': self.move(cmd)
                        elif cmd['op']=='authorize_contact': self.authorize_contact(cmd)
                        elif cmd['op']=='snapshot': pass
                        else: raise ValueError('Unsupported operation')
                        self.snapshot(cmd['label'])
                    except Exception as exc:
                        self.fault=str(exc)
                        self.event('fault',{'error':str(exc),'trace':traceback.format_exc()})
                        try: self.snapshot(cmd['label']+'_fault')
                        except Exception: pass
                try: self.sample()
                except Exception as exc:
                    if not self.fault: self.event('fault',{'error':str(exc)})
                    self.fault=str(exc)
                time.sleep(.12)
        finally:
            for cam in self.cameras.values():
                if cam.is_connected: cam.disconnect()
            for bus in self.buses.values():
                if bus.is_connected: bus.disconnect(disable_torque=False)
            self.event('closed',{'torque_changed_on_exit':False})

if __name__=='__main__': Owner().run()
