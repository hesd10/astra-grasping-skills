"""This attempt only: read live hardware and capture fresh views. No motor writes."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import json
import time
from concurrent.futures import ThreadPoolExecutor
from skill.hardware import enumerate_current_devices, capture_fresh
from lerobot.motors.feetech.feetech import FeetechMotorsBus
from lerobot.motors.motors_bus import Motor, MotorNormMode
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig

ROOT = Path(__file__).resolve().parents[1] / 'evidence'
REGISTERS = ['Model_Number', 'Operating_Mode', 'Torque_Enable', 'Goal_Position',
             'Present_Position', 'Present_Load', 'Present_Temperature', 'Status',
             'Present_Voltage', 'Present_Current', 'Min_Position_Limit',
             'Max_Position_Limit', 'Max_Temperature_Limit', 'Torque_Limit',
             'Goal_Velocity', 'Acceleration', 'Unloading_Condition']

def inspect_bus(port):
    bus = FeetechMotorsBus(port, {}, calibration=None)
    out = {'port':port,'timestamp':time.time()}
    try:
        bus.connect(handshake=False)
        bus.set_baudrate(bus.default_baudrate)
        found = bus.broadcast_ping()
        out['ping'] = found
    finally:
        if bus.is_connected:
            bus.disconnect(disable_torque=False)
    motors = {str(i): Motor(i, bus._model_nb_to_model_dict[m], MotorNormMode.DEGREES)
              for i,m in (found or {}).items()}
    bus = FeetechMotorsBus(port, motors, calibration=None)
    out['registers'] = {}
    try:
        bus.connect(handshake=False)
        bus.set_baudrate(bus.default_baudrate)
        for name in motors:
            out['registers'][name] = {}
            for reg in REGISTERS:
                try:
                    out['registers'][name][reg] = bus.read(reg,name,normalize=False)
                except Exception as exc:
                    out['registers'][name][reg] = {'error':str(exc)}
    finally:
        if bus.is_connected:
            bus.disconnect(disable_torque=False)
    (ROOT / (Path(port).name + '_initial.json')).write_text(json.dumps(out,indent=2))
    return out

def camera(index):
    try:
        p = capture_fresh(OpenCVCameraConfig(index_or_path=index,width=640,height=480,
                           fps=30,fourcc='MJPG'),ROOT/f'initial_video{index}.jpg',3000)
        return {'camera':index,'path':str(p)}
    except Exception as exc:
        return {'camera':index,'error':str(exc)}

if __name__ == '__main__':
    (ROOT/'host_devices.json').write_text(json.dumps(enumerate_current_devices(),indent=2))
    with ThreadPoolExecutor(max_workers=6) as pool:
        jobs = [pool.submit(inspect_bus,p) for p in ['/dev/ttyACM0','/dev/ttyACM1']]
        jobs += [pool.submit(camera,i) for i in [4,6,8,10]]
        for job in jobs:
            try:
                print(json.dumps(job.result()),flush=True)
            except Exception as exc:
                print(json.dumps({'error':str(exc)}),flush=True)
