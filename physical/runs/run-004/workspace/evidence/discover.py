import os, sys, json, time
from pathlib import Path
sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from skill.hardware import enumerate_current_devices, discover_motor_models, capture_fresh
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
out = Path(__file__).parent
report = {'timestamp':time.time(), 'devices':enumerate_current_devices(), 'models':{}, 'cameras':{}}
for port in ('/dev/ttyACM0','/dev/ttyACM1'):
    try: report['models'][port]=discover_motor_models(port)
    except Exception as exc: report['models'][port]={'error':str(exc)}
for idx in (4,6,8,10):
    try:
        p=capture_fresh(OpenCVCameraConfig(index_or_path=idx, width=640, height=480, fps=30, fourcc='MJPG'), out/f'initial_video{idx}.jpg', 3000)
        report['cameras'][str(idx)]=str(p)
    except Exception as exc: report['cameras'][str(idx)]={'error':str(exc)}
(out/'discovery.json').write_text(json.dumps(report,indent=2))
print(json.dumps(report,indent=2))
