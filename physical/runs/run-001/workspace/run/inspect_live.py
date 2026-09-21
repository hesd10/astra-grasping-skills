"""Current-run read-only motor telemetry and camera capture. No calibration loading."""
import json
import time
from pathlib import Path

import cv2
from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.motors.feetech.feetech import FeetechMotorsBus
from lerobot.motors.motors_bus import Motor, MotorNormMode

OUT = Path(__file__).resolve().parent / 'evidence'
OUT.mkdir(exist_ok=True)
report = {'time': time.time(), 'cameras': {}, 'buses': {}}
for index in (4, 6, 8, 10):
    camera = OpenCVCamera(OpenCVCameraConfig(index_or_path=index, width=640, height=480, fourcc='MJPG'))
    try:
        camera.connect()
        frame = camera.async_read(timeout_ms=2000)
        path = OUT / f'initial_video{index}.jpg'
        cv2.imwrite(str(path), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        report['cameras'][index] = str(path)
    except Exception as exc:
        report['cameras'][index] = {'error': str(exc)}
    finally:
        if camera.is_connected:
            camera.disconnect()

for port in ('/dev/ttyACM0', '/dev/ttyACM1'):
    bus = FeetechMotorsBus(port, {'probe': Motor(1, 'sts3215', MotorNormMode.RANGE_M100_100)})
    found = {}
    try:
        bus.connect(handshake=False)
        for motor_id in range(1, 21):
            model, comm, error = bus.packet_handler.ping(bus.port_handler, motor_id)
            if comm != bus._comm_success:
                continue
            row = {'model': model, 'ping_error': error}
            for key in ('Present_Position', 'Present_Velocity', 'Present_Load', 'Present_Voltage', 'Present_Temperature', 'Present_Current', 'Status', 'Torque_Enable', 'Goal_Position', 'Operating_Mode', 'Max_Temperature_Limit', 'Torque_Limit', 'Max_Torque_Limit', 'Min_Position_Limit', 'Max_Position_Limit'):
                address, length = bus.model_ctrl_table['sts3215'][key]
                value, result, status = bus._read(address, length, motor_id, raise_on_error=False)
                row[key] = {'value': value, 'comm': result, 'error': status}
            found[motor_id] = row
    except Exception as exc:
        found['error'] = str(exc)
    finally:
        if bus.is_connected:
            bus.disconnect(disable_torque=False)
    report['buses'][port] = found

(OUT / 'initial_telemetry.json').write_text(json.dumps(report, indent=2))
print(json.dumps(report, indent=2))
