"""Current-session read-only discovery. Never transfer this evidence directory."""
import json
import sys
import time
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / 'skill'))
from hardware import enumerate_current_devices, capture_fresh
from lerobot.motors.feetech.feetech import FeetechMotorsBus
from lerobot.motors.motors_bus import Motor, MotorNormMode
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig

OUT = ROOT / 'evidence'
def camera(index):
    try:
        config = OpenCVCameraConfig(index_or_path=index, width=640, height=480, fps=30, fourcc='MJPG')
        path = capture_fresh(config, OUT / f'initial-camera-{index}.png', 4000)
        return {'camera':index,'path':str(path),'time':time.time()}
    except Exception as exc:
        return {'camera':index,'error':str(exc)}

def motors(port):
    bus = FeetechMotorsBus(port, {}, calibration=None)
    try:
        bus.connect(handshake=False)
        bus.set_baudrate(bus.default_baudrate)
        found = bus.broadcast_ping()
        table = {v:k for k,v in bus.model_number_table.items()}
        assignments = {str(k):Motor(k,table[v],MotorNormMode.DEGREES) for k,v in found.items()}
        bus.disconnect(disable_torque=False)
        bus = FeetechMotorsBus(port, assignments, calibration=None)
        bus.connect(handshake=False)
        bus.set_baudrate(bus.default_baudrate)
        registers = ['Operating_Mode','Torque_Enable','Present_Position','Goal_Position',
                     'Present_Load','Present_Temperature','Present_Voltage','Present_Current',
                     'Status','Min_Position_Limit','Max_Position_Limit','Max_Temperature_Limit',
                     'Torque_Limit','Max_Torque_Limit','Goal_Velocity','Acceleration']
        values = {name:{r:bus.read(r,name,normalize=False) for r in registers} for name in bus.motors}
        return {'port':port,'models':found,'values':values,'time':time.time()}
    except Exception as exc:
        return {'port':port,'error':repr(exc)}
    finally:
        if bus.is_connected:
            bus.disconnect(disable_torque=False)

if __name__ == '__main__':
    result = {'started':time.time(),'devices':enumerate_current_devices()}
    with ThreadPoolExecutor(max_workers=5) as pool:
        cams = list(pool.map(camera,[4,6,8,10]))
        buses = list(pool.map(motors,['/dev/ttyACM0','/dev/ttyACM1']))
    result.update(cameras=cams,buses=buses,finished=time.time())
    (OUT/'initial-discovery.json').write_text(json.dumps(result,indent=2))
    print(json.dumps({'cameras':cams,'buses':buses},indent=2))
