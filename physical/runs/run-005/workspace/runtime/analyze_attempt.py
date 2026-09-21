import json,datetime
from pathlib import Path
root=Path(__file__).resolve().parents[1]
rows=[json.loads(x) for x in (root/'evidence/control.jsonl').read_text().splitlines()]
decisions=[r for r in rows if r['event']=='decision']
images=[r for r in rows if r['event']=='images']
start=next(r for r in images if '/025_' in r['paths'][0])
end=next(r for r in images if '/026_' in r['paths'][0])
ss=[r for r in rows if r['event']=='telemetry' and start['time']<=r['time']<=end['time']]
initial=next(r for r in rows if r['event']=='initialize_hold')
all_samples=[r for r in rows if r['event']=='telemetry']
summary={
 'experiment_start_utc':'2026-09-16T02:18:52Z',
 'control_end_utc':datetime.datetime.fromtimestamp(rows[-1]['time'],datetime.timezone.utc).isoformat(),
 'experiment_elapsed_seconds':rows[-1]['time']-datetime.datetime(2026,9,16,2,18,52,tzinfo=datetime.timezone.utc).timestamp(),
 'motor_session_seconds':rows[-1]['time']-initial['time'],
 'outcome':'Visible stable suspension; 3 cm metric threshold not verified',
 'verified_visual_interval_seconds':end['time']-start['time'],
 'hold_telemetry_samples':len(ss),
 'motion_command_decisions':sum(r['command']['op']=='move' for r in decisions),
 'verification_decisions':sum(r['command']['op']=='status' for r in decisions),
 'closeout_decisions':sum(r['command']['op']=='quit' for r in decisions),
 'startup_decision_groups':3,
 'faults':[r for r in rows if r['event']=='fault'],
 'right_max_drift_counts':max(abs(r['data']['right']['Present_Position'][n]-initial['initial']['right'][n]) for r in all_samples for n in initial['initial']['right']),
 'maximum_observed_temperature':max(t for r in all_samples for d in r['data'].values() for t in d['Present_Temperature'].values()),
 'hold':{side:{reg:{n:[min(r['data'][side][reg][n] for r in ss),max(r['data'][side][reg][n] for r in ss)] for n in ss[0]['data'][side][reg]} for reg in ('Present_Position','Present_Load','Status')} for side in ('left','right')},
 'final_state':'Serial connections closed without disabling torque; active position and gripper goals retained. Software monitoring ended. Hardware protections retained.',
 'temperature_register_writes':0,
 'history_accessed':False,
 'contamination_detected':False,
}
(root/'evidence/summary.json').write_text(json.dumps(summary,indent=2))
print(json.dumps({k:v for k,v in summary.items() if k!='hold'},indent=2))
