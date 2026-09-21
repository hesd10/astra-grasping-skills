"""Recompute matched execution durations and model-request counts; offline only."""
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def timestamp(value):
    return value if isinstance(value, (int, float)) else datetime.fromisoformat(value.replace('Z', '+00:00')).timestamp()

def utc(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat()

# End of live execution as recorded in each controller's closeout evidence.
# Run 001 ends with the final corrected snapshot; Run 004 uses its full-precision
# final log event. Failed runs end at the torque-off verification marker.
SOURCES = [
    ('run/summary.json', 'execution_end_utc'),
    ('evidence/summary.json', 'torque_release_utc'),
    ('evidence/torque-release.json', 'time'),
    ('evidence/summary.json', 'end_utc'),
    ('evidence/summary.json', 'control_end_utc'),
    ('evidence/summary.json', 'monitoring_end_utc'),
]
results = []
for n, (relative, key) in enumerate(SOURCES, 1):
    run = ROOT / 'runs' / f'run-{n:03}'
    events_path = run / 'conversation/events.jsonl'
    events = [json.loads(line) for line in events_path.read_text().splitlines()]
    start_event = next(e for e in events if e['type'] == 'task_started')
    start = timestamp(start_event['timestamp'])
    endpoint_path = run / 'workspace' / relative
    end_source = {'file': str(endpoint_path.relative_to(ROOT)), 'key': key}
    if n == 4:
        endpoint_path = run / 'workspace/evidence/session.jsonl'
        indexed = [(i, json.loads(line)) for i, line in enumerate(endpoint_path.read_text().splitlines(), 1)]
        line, event = [(i, e) for i, e in indexed if e.get('kind') == 'final'][-1]
        end = event['time']
        end_source = {'file': str(endpoint_path.relative_to(ROOT)), 'log_line': line, 'event': 'final', 'key': 'time'}
    else:
        end = timestamp(json.loads(endpoint_path.read_text())[key])
    requests = {}
    for line, event in enumerate(events, 1):
        if event['type'] == 'token_usage_record' and start <= timestamp(event['timestamp']) <= end:
            requests.setdefault(event['response_id'], {
                'response_id': event['response_id'], 'timestamp': event['timestamp'],
                'export_line': line, 'source_file': event['source_file'],
                'source_line': event['source_line'],
            })
    elapsed = end - start
    seconds = round(elapsed)
    result = {
        'run': f'Run {n:03}', 'start_utc': utc(start), 'end_utc': utc(end),
        'elapsed_seconds': elapsed, 'display_duration': f'{seconds//60}m {seconds%60:02}s',
        'execution_model_requests': len(requests),
        'start_source': {'file': str(events_path.relative_to(ROOT)),
                         'event': 'first task_started', 'source_line': start_event['source_line']},
        'end_source': end_source,
        'counted_requests': list(requests.values()),
    }
    results.append(result)
    print(result['run'], result['display_duration'], len(requests))
(ROOT / 'analysis/execution_metrics.json').write_text(json.dumps({
    'methodology': 'analysis/METHODOLOGY.md',
    'interval': 'first task_started through recorded live-execution closeout; inclusive',
    'count': 'unique response_id with token_usage_record timestamp inside interval',
    'runs': results,
}, indent=2) + '\n')
