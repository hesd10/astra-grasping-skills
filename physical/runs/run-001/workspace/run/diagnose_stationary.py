"""Stationary read-only follow-up to an anomalous temperature sample."""
import json
import time
from pathlib import Path
from lerobot.motors.feetech.feetech import FeetechMotorsBus
from lerobot.motors.motors_bus import Motor, MotorNormMode

out = Path(__file__).resolve().parent / 'evidence' / 'stationary_diagnostic.jsonl'
bus = FeetechMotorsBus('/dev/ttyACM1', {str(i): Motor(i, 'sts3215', MotorNormMode.RANGE_M100_100) for i in range(1, 7)})
rows = []
try:
    bus.connect()
    with out.open('a') as f:
        for _ in range(100):
            row = {'time': time.time(), 'motors': {}}
            for name in bus.motors:
                row['motors'][name] = {key: bus.read(key, name, normalize=False) for key in ('Present_Position', 'Present_Load', 'Present_Temperature', 'Present_Current', 'Present_Voltage', 'Status', 'Torque_Enable')}
            f.write(json.dumps(row) + '\n')
            f.flush()
            rows.append(row)
            time.sleep(0.1)
finally:
    if bus.is_connected:
        bus.disconnect(disable_torque=False)
for name in bus.motors:
    print(name, {key: [min(r['motors'][name][key] for r in rows), max(r['motors'][name][key] for r in rows)] for key in rows[0]['motors'][name]})
