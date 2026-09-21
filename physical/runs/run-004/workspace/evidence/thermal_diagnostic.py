import sys,time,json
from pathlib import Path
sys.dont_write_bytecode=True
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
from skill.hardware import ReadOnlyFeetech
from lerobot.motors import Motor, MotorNormMode
rows=[]
with ReadOnlyFeetech('/dev/ttyACM1',{str(i):Motor(i,'sts3215',MotorNormMode.DEGREES) for i in range(1,7)}) as d:
    for _ in range(20):
        rows.append({'time':time.time(),'individual':d.snapshot(['Present_Temperature','Status','Present_Load','Present_Current','Torque_Enable','Max_Temperature_Limit'])})
        time.sleep(.15)
Path(__file__).with_name('thermal_diagnostic.json').write_text(json.dumps(rows,indent=2))
print(json.dumps({'samples':len(rows),'first':rows[0],'last':rows[-1], 'temperature_ranges':{str(i):[min(r['individual'][str(i)]['Present_Temperature'] for r in rows),max(r['individual'][str(i)]['Present_Temperature'] for r in rows)] for i in range(1,7)}},indent=2))
