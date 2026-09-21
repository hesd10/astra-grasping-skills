"""Current-run live register snapshot. Does not write servo registers."""
import sys
sys.dont_write_bytecode = True
import json
import time
from pathlib import Path
from skill.hardware import ReadOnlyFeetech
from lerobot.motors import Motor, MotorNormMode

REGISTERS = ['Present_Position', 'Goal_Position', 'Present_Load', 'Present_Temperature',
             'Present_Voltage', 'Status', 'Torque_Enable', 'Operating_Mode',
             'Min_Position_Limit', 'Max_Position_Limit', 'Max_Temperature_Limit',
             'Max_Torque_Limit', 'Torque_Limit', 'Protection_Current', 'Unloading_Condition',
             'Overload_Torque', 'Protective_Torque', 'Protection_Time', 'Acceleration',
             'Goal_Velocity', 'P_Coefficient', 'D_Coefficient', 'I_Coefficient']

def main():
    root = Path(__file__).resolve().parent / 'evidence'
    discovery = json.loads((root / 'discovery.json').read_text())
    output = {'utc':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime()), 'ports':{}}
    for row in discovery['observations']:
        if 'models' not in row:
            continue
        motors = {str(i):Motor(int(i), {777:'sts3215',2825:'sts3250'}[m], MotorNormMode.DEGREES)
                  for i,m in row['models'].items()}
        with ReadOnlyFeetech(row['port'],motors) as device:
            output['ports'][row['port']] = device.snapshot(REGISTERS)
    (root / 'startup_telemetry.json').write_text(json.dumps(output,indent=2))
    print(json.dumps(output,indent=2))

if __name__ == '__main__':
    main()
