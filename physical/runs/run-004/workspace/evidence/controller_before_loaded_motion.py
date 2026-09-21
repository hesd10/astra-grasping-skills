"""Current attempt only. Live low-level control; no saved calibration or IK."""
import sys, json, time, select, traceback, os
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from lerobot.motors import Motor, MotorNormMode
from lerobot.motors.feetech.feetech import FeetechMotorsBus
from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
import cv2
OUT=Path(__file__).parent
log=(OUT/'session.jsonl').open('a',buffering=1)
buses={}; cameras={}; limits={}; goals={}; right_start={}; fault=None
regs=('Present_Position','Present_Load','Present_Temperature','Status','Torque_Enable')
def record(kind, data):
    log.write(json.dumps({'time':time.time(),'kind':kind,'data':data})+'\n')
def snapshot():
    return {side:{reg:b.sync_read(reg,normalize=False) for reg in regs} for side,b in buses.items()}
def capture(label):
    for idx,c in cameras.items():
        f=c.async_read(timeout_ms=1000)
        cv2.imwrite(str(OUT/f'{label}_video{idx}.jpg'),cv2.cvtColor(f,cv2.COLOR_RGB2BGR))
def stop_arm():
    b=buses['left']; q=b.sync_read('Present_Position',normalize=False)
    hold={n:max(limits[n][0],min(limits[n][1],q[n])) for n in q if n!='6'}
    b.sync_write('Goal_Position',hold,normalize=False); goals.update(hold)
def check(s):
    for side, v in s.items():
        for n in v['Present_Position']:
            if v['Status'][n]: raise RuntimeError(f'{side}/{n} status {v["Status"][n]}')
            if abs(v['Present_Load'][n])>650: raise RuntimeError(f'{side}/{n} load {v["Present_Load"][n]}')
    if any(abs(s['right']['Present_Position'][n]-right_start[n])>15 for n in right_start):
        raise RuntimeError('Right arm drift')
def summary(s):
    return {side:{'position':v['Present_Position'],'load':v['Present_Load'],'temperature':v['Present_Temperature']} for side,v in s.items()}
try:
    for side,port in [('right','/dev/ttyACM0'),('left','/dev/ttyACM1')]:
        b=FeetechMotorsBus(port,{str(i):Motor(i,'sts3215',MotorNormMode.DEGREES) for i in range(1,7)},calibration=None)
        b.connect(handshake=False); b.set_baudrate(b.default_baudrate); buses[side]=b
        q=b.sync_read('Present_Position',normalize=False)
        lo=b.sync_read('Min_Position_Limit',normalize=False); hi=b.sync_read('Max_Position_Limit',normalize=False)
        torque=b.sync_read('Torque_Enable',normalize=False)
        oldgoal=b.sync_read('Goal_Position',normalize=False)
        for n in q:
            if b.ping(n,raise_on_error=True)!=777: raise RuntimeError('Wrong model')
            if not torque[n]:
                b.write('Goal_Position',n,max(lo[n],min(hi[n],q[n])),normalize=False)
            if side=='left':
                b.write('Goal_Velocity',n,60,normalize=False)
                b.write('Acceleration',n,5,normalize=False)
                if n=='6': b.write('Torque_Limit',n,180,normalize=False)
        b.enable_torque()
        if side=='right': right_start=q
        else:
            limits={n:(lo[n],hi[n]) for n in q}
            goals=b.sync_read('Goal_Position',normalize=False)
        record('init',{'side':side,'q':q,'oldgoal':oldgoal,'torque_before':torque})
    for idx in (6,8,10):
        c=OpenCVCamera(OpenCVCameraConfig(index_or_path=idx,width=640,height=480,fps=30,fourcc='MJPG'))
        c.connect(); c.async_read(timeout_ms=2000); cameras[idx]=c
    s=snapshot(); record('ready',s); capture('resume_ready')
    print(json.dumps({'ready':True,'pid':os.getpid(),'state':summary(s)}),flush=True)
    lastlog=0
    while True:
        s=snapshot()
        try: check(s)
        except Exception as exc:
            if not fault:
                fault=str(exc); stop_arm(); record('fault',fault); capture('fault')
                print(json.dumps({'fault':fault,'state':summary(s)}),flush=True)
        if time.monotonic()-lastlog>1:
            record('telemetry',s); lastlog=time.monotonic()
        if not select.select([sys.stdin],[],[],0.1)[0]: continue
        line=sys.stdin.readline()
        if not line:
            stop_arm(); record('input_closed',{}); break
        try:
            cmd=json.loads(line); record('command',cmd)
            op=cmd['op']
            if op=='finish':
                stop_arm(); capture('final'); record('final',snapshot()); print('FINISHED',flush=True); break
            if op=='observe':
                capture(cmd['label']); print(json.dumps({'observed':cmd['label'],'state':summary(snapshot()),'fault':fault}),flush=True); continue
            if op=='move':
                if fault: raise RuntimeError('Motion locked following fault')
                delta=cmd['delta']; q=buses['left'].sync_read('Present_Position',normalize=False)
                target={n:int(q[n]+d) for n,d in delta.items()}
                if any(n not in goals or abs(delta[n])>(500 if n=='6' else 160) or not limits[n][0]<=v<=limits[n][1] for n,v in target.items()):
                    raise ValueError('Invalid bounded target')
                maxchange=max(abs(delta[n]) for n in target)
                duration=max(float(cmd.get('duration',2)),maxchange/50)
                start=time.monotonic()
                while True:
                    alpha=min(1,(time.monotonic()-start)/duration)
                    values={n:round(q[n]+alpha*(target[n]-q[n])) for n in target}
                    buses['left'].sync_write('Goal_Position',values,normalize=False); goals.update(values)
                    s=snapshot(); record('motion',s); check(s)
                    if alpha>=1: break
                    time.sleep(0.08)
                time.sleep(0.6); capture(cmd['label']); s=snapshot(); record('segment_end',s)
                print(json.dumps({'completed':cmd['label'],'target':target,'state':summary(s)}),flush=True)
        except Exception as exc:
            stop_arm(); record('command_error',str(exc)); print(json.dumps({'error':str(exc)}),flush=True)
except BaseException as exc:
    record('fatal',{'error':str(exc),'traceback':traceback.format_exc()})
    if 'left' in buses:
        try: stop_arm()
        except Exception: pass
    print(traceback.format_exc(),flush=True)
finally:
    for c in cameras.values():
        try: c.disconnect()
        except Exception: pass
    for b in buses.values():
        try: b.disconnect(disable_torque=False)
        except Exception: pass
    log.close()
