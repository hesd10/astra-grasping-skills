"""Current-session read-only discovery; no saved calibration or robot controller."""
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.dont_write_bytecode = True
from skill.hardware import enumerate_current_devices, discover_motor_models, capture_fresh
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig

OUT = Path(__file__).resolve().parent / 'evidence'

def camera(index):
    try:
        destination = OUT / f'initial_camera_{index}.jpg'
        capture_fresh(OpenCVCameraConfig(index_or_path=index, width=640, height=480,
                                       fps=30, fourcc='MJPG'), destination, 3000)
        return {'camera': index, 'path': str(destination), 'monotonic': time.monotonic()}
    except Exception as exc:
        return {'camera': index, 'error': str(exc)}

def serial(port):
    try:
        return {'port': port, 'models': discover_motor_models(port)}
    except Exception as exc:
        return {'port': port, 'error': str(exc)}

if __name__ == '__main__':
    report = {'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
              'devices': enumerate_current_devices()}
    with ThreadPoolExecutor(max_workers=6) as pool:
        jobs = [pool.submit(camera, i) for i in [4, 6, 8, 10]]
        jobs += [pool.submit(serial, port) for port in ['/dev/ttyACM0', '/dev/ttyACM1']]
        report['observations'] = [job.result() for job in jobs]
    (OUT / 'discovery.json').write_text(json.dumps(report, indent=2))
    print(json.dumps(report['observations'], indent=2))
