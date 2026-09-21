"""Read-only, timed multi-view evidence of the current lift."""
import json
import time
from pathlib import Path
import cv2
from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.motors.feetech.feetech import FeetechMotorsBus
from lerobot.motors.motors_bus import Motor, MotorNormMode

out = Path(__file__).resolve().parent / 'evidence'
buses = {}
cameras = {}
try:
    for side, port in (('left', '/dev/ttyACM1'), ('right', '/dev/ttyACM0')):
        bus = FeetechMotorsBus(port, {str(i): Motor(i, 'sts3215', MotorNormMode.RANGE_M100_100) for i in range(1, 7)})
        bus.connect()
        buses[side] = bus
    for index in (6, 8, 10):
        camera = OpenCVCamera(OpenCVCameraConfig(index_or_path=index, width=640, height=480, fourcc='MJPG'))
        camera.connect()
        cameras[index] = camera
    start = time.monotonic()
    capture_at = 0
    with (out / 'hold_verification.jsonl').open('a', buffering=1) as f:
        while True:
            elapsed = time.monotonic() - start
            row = {'time': time.time(), 'elapsed': elapsed, 'state': {}}
            for side, bus in buses.items():
                row['state'][side] = {name: {key: bus.read(key, name, normalize=False) for key in ('Present_Position', 'Present_Load', 'Present_Temperature', 'Present_Current', 'Status', 'Goal_Position', 'Torque_Enable')} for name in bus.motors}
            if elapsed >= capture_at:
                paths = {}
                for index, camera in cameras.items():
                    p = out / f'hold_{capture_at:02d}_video{index}.jpg'
                    frame = camera.async_read(timeout_ms=1000)
                    cv2.imwrite(str(p), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
                    paths[index] = str(p)
                row['images'] = paths
                print(json.dumps(row), flush=True)
                capture_at += 5
            f.write(json.dumps(row) + '\n')
            if elapsed >= 15:
                break
            time.sleep(0.15)
finally:
    for camera in cameras.values():
        if camera.is_connected:
            camera.disconnect()
    for bus in buses.values():
        if bus.is_connected:
            bus.disconnect(disable_torque=False)
