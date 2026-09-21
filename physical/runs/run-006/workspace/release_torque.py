"""User-requested shutdown for this session; no movement goals are written."""
import sys
sys.dont_write_bytecode = True
import json
import time
from pathlib import Path
from lerobot.motors import Motor, MotorNormMode
from skill.hardware import ReadOnlyFeetech, release_requested_torque, exclusive_command_owner

root = Path(__file__).resolve().parent
output = {'utc': time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()), 'arms': {}}
with exclusive_command_owner(root / 'evidence' / 'shutdown.lock'):
    for role, port in [('left', '/dev/ttyACM1'), ('right', '/dev/ttyACM0')]:
        try:
            motors = {str(i): Motor(i, 'sts3215', MotorNormMode.DEGREES) for i in range(1, 7)}
            with ReadOnlyFeetech(port, motors) as device:
                output['arms'][role] = release_requested_torque(device.bus, list(motors))
        except Exception as exc:
            output['arms'][role] = {'error': str(exc)}
(root / 'evidence' / 'torque_release.json').write_text(json.dumps(output, indent=2))
print(json.dumps(output, indent=2))
if not all(len(results) == 6 and all(row.get('disabled') is True for row in results.values())
           for results in output['arms'].values()):
    raise SystemExit('Torque release was not fully verified')
