"""Offline evidence calculation. Reads archive files only; never imports a robot driver."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TOKEN = json.loads((ROOT / 'analysis/token_usage.json').read_text())
LOGS = ['run/evidence/session.jsonl', 'evidence/control.jsonl', 'evidence/session.jsonl',
        'evidence/session.jsonl', 'evidence/control.jsonl', 'evidence/monitor.jsonl']

def kind(row):
    return row.get('event', row.get('kind'))

def left_positions(row):
    state = row.get('state', row.get('data', {}))
    if not isinstance(state, dict) or 'left' not in state:
        return None
    arm = state['left']
    if 'Present_Position' in arm:
        return arm['Present_Position']
    if arm and all(isinstance(v, dict) and 'Present_Position' in v for v in arm.values()):
        return {joint: v['Present_Position'] for joint, v in arm.items()}
    return None

def motion(n, r):
    k = kind(r)
    if n == 1: return k in ('motion_start', 'grip_start')
    if n == 2: return k == 'command' and bool(r['data'].get('delta'))
    if n == 3: return k == 'online_command' and bool(r['command'].get('delta'))
    if n == 4: return k == 'command' and r['data'].get('op') == 'move'
    if n == 5: return k == 'decision' and r['command'].get('op') == 'move'
    return k == 'motion_start'

def stamp(r, line):
    return {'utc': datetime.fromtimestamp(r['time'], timezone.utc).isoformat(),
            'unix_seconds': r['time'], 'log_line': line}

results = []
for n, expected in enumerate(TOKEN['runs'], 1):
    run = ROOT / 'runs' / f'run-{n:03}'
    ws = run / 'workspace'
    rows = [json.loads(s) for s in (ws / LOGS[n-1]).read_text().splitlines()]
    indexed = list(enumerate(rows, 1))
    commands = [(i, r) for i, r in indexed if motion(n, r)]
    first_line, command = commands[0]
    before = [left_positions(r) for i, r in indexed if i < first_line and left_positions(r)]
    baseline = before[-1]
    first = next((i, r) for i, r in indexed if i > first_line and left_positions(r) is not None and left_positions(r) != baseline)
    endpoint = None
    hold = 0
    note = None
    if n == 1:
        endpoint = [(i, r) for i, r in indexed if kind(r) == 'snapshot' and r['tag'] == 'final'][-1]
        hold = json.loads((ws/'run/summary.json').read_text())['confirmed_hold_seconds']
        note = 'Final corrected snapshot; excludes withdrawn success claim'
    elif n == 4:
        endpoint = next((i, r) for i, r in indexed if kind(r) == 'command' and r['data'].get('label') == 'clearance_hold_end')
        hold = json.loads((ws/'evidence/summary.json').read_text())['hold_interval_seconds']
        note = 'Observation request proxy, not image completion'
    elif n == 5:
        endpoint = next((i, r) for i, r in indexed if kind(r) == 'images' and any(Path(p).name.startswith('026_status_') for p in r['paths']))
        hold = json.loads((ws/'evidence/summary.json').read_text())['verified_visual_interval_seconds']
        note = 'Hold-end images event'
    elif n == 6:
        endpoint = next((i, r) for i, r in indexed if kind(r) == 'snapshot' and r['data']['label'] == 'final_hold')
        hold = json.loads((ws/'evidence/summary.json').read_text())['final_hold_interval_s']
        note = 'Final snapshot event proxy, slightly later than camera acquisition returns'
    exported = [json.loads(s) for s in (run/'conversation/events.jsonl').read_text().splitlines()]
    usages = {e['response_id']:e for e in exported if e['type']=='token_usage_record'}
    included = {t['turn_id'] for t in expected['turns'] if t['phase']=='experiment'}
    fields = ['input_tokens','cached_input_tokens','output_tokens','reasoning_output_tokens','total_tokens']
    exp = {k:sum(e['usage'][k] for e in usages.values() if e['turn_id'] in included) for k in fields}
    whole = {k:sum(e['usage'][k] for e in usages.values()) for k in fields}
    for k in fields:
        assert exp[k] == expected['experiment'][k], (n,k,'experiment')
        assert whole[k] == expected['whole_session'][k], (n,k,'whole')
    count = sum(e['turn_id'] in included for e in usages.values())
    assert count == expected['experiment']['requests']
    assert len(commands) == [31,35,25,31,25,31][n-1]
    result = {'run':f'Run {n:03}','outcome':'success' if endpoint else 'failure',
              'outcome_definition':'Grasp and stable visible suspension',
              'motion_submissions':len(commands),'experiment_model_requests':count,
              'first_motion_command':stamp(command,first_line),
              'first_changed_feedback':stamp(first[1],first[0]),
              'final_hold_evidence':stamp(endpoint[1],endpoint[0]) if endpoint else None,
              'endpoint_note':note,'movement_to_final_evidence_seconds':endpoint[1]['time']-first[1]['time'] if endpoint else None,
              'hold_seconds':hold,'experiment_tokens':exp,'whole_session_tokens':whole,
              'motion_log':str((ws/LOGS[n-1]).relative_to(ROOT))}
    results.append(result)
output = {'method':'analysis/METHODOLOGY.md','runs':results,
          'total_experiment_tokens':sum(r['experiment_tokens']['total_tokens'] for r in results),
          'total_model_requests':sum(r['experiment_model_requests'] for r in results)}
(ROOT/'analysis/results.json').write_text(json.dumps(output,indent=2)+'\n')
for r in results:
    print(r['run'],r['outcome'],'motion',r['motion_submissions'],'hold',round(r['hold_seconds'],2),
          'movement_to_evidence',r['movement_to_final_evidence_seconds'],'tokens',r['experiment_tokens']['total_tokens'])
print('Verified total tokens:',output['total_experiment_tokens'])
