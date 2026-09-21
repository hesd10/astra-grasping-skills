"""Read the authorized five-run evidence and write derived metrics here only.

This retrospective is not transferable. It does not import drivers or operate
hardware. Original reports and logs remain unchanged, including obsolete paths
embedded in the renamed first project's evidence.
"""
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROJECTS = ROOT.parent
SOURCES = {
    'Run 001': ('run/REPORT.md', 'run/evidence/session.jsonl', 'run/summary.json'),
    'Run 002': ('RUN_REPORT.md', 'evidence/control.jsonl', 'evidence/summary.json'),
    'Run 003': ('evidence/REPORT.md', 'evidence/session.jsonl'),
    'Run 004': ('REPORT.md', 'evidence/session.jsonl', 'evidence/summary.json'),
    'Run 005': ('REPORT.md', 'evidence/control.jsonl', 'evidence/summary.json'),
}


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


def is_motion(run, row):
    if run == 'Run 001':
        return kind(row) in ('motion_start', 'grip_start')
    if run == 'Run 002':
        return kind(row) == 'command' and bool(row['data'].get('delta'))
    if run == 'Run 003':
        return kind(row) == 'online_command' and bool(row['command'].get('delta'))
    if run == 'Run 004':
        return kind(row) == 'command' and row['data'].get('op') == 'move'
    return kind(row) == 'decision' and row['command'].get('op') == 'move'


def timestamp(row, line, description):
    return dict(utc=datetime.fromtimestamp(row['time'], timezone.utc).isoformat(),
                unix_seconds=row['time'], log_line=line, description=description)


def derive():
    output = {'scope': 'Authorized retrospective only; never transfer analysis/',
              'timing_definition': 'First logged left-position change after the first '
              'movement command, relative to the latest preceding position sample, '
              'through final hold-verification evidence or explicitly labeled proxy. '
              'This is not an exact physical onset or assistant-declaration timestamp.',
              'full_metric_success_count': 0, 'runs': [], 'source_sha256': []}
    for run, paths in SOURCES.items():
        for relative in paths:
            source = PROJECTS / run / relative
            output['source_sha256'].append(dict(path=str(source),
                sha256=hashlib.sha256(source.read_bytes()).hexdigest()))
        rows = [json.loads(line) for line in (PROJECTS / run / paths[1]).read_text().splitlines()]
        indexed = list(enumerate(rows, 1))
        commands = [(i, row) for i, row in indexed if is_motion(run, row)]
        first_line, first_command = commands[0]
        baseline = [left_positions(row) for i, row in indexed if i < first_line and left_positions(row)]
        if not baseline:
            raise RuntimeError(f'No pre-command feedback in {run}')
        motion_line, motion = next((i, row) for i, row in indexed
            if i > first_line and left_positions(row) is not None
            and left_positions(row) != baseline[-1])
        result = dict(run=run, full_metric_success=False,
            movement_commands_submitted=len(commands),
            first_movement_command=timestamp(first_command, first_line, 'First movement command'),
            first_observed_movement=timestamp(motion, motion_line, 'First changed left-position sample'),
            result='Slip; no stable suspension', stable_hold_seconds=0,
            final_hold_evidence=None, seconds_to_final_hold_evidence=None,
            seconds_to_full_metric_success=None)
        if run == 'Run 001':
            summary = json.loads((PROJECTS / run / paths[2]).read_text())
            end_line, end = [(i, r) for i, r in indexed if kind(r) == 'snapshot' and r['tag'] == 'final'][-1]
            result['stable_hold_seconds'] = summary['confirmed_hold_seconds']
            endpoint_description = 'Final corrected hold snapshot; withdrawn earlier claim excluded'
            result['reported_actuation_batches'] = summary['submitted_actuation_batches']
        elif run == 'Run 004':
            summary = json.loads((PROJECTS / run / paths[2]).read_text())
            end_line, end = next((i, r) for i, r in indexed if kind(r) == 'command'
                and r['data'].get('label') == 'clearance_hold_end')
            result['stable_hold_seconds'] = summary['hold_interval_seconds']
            result['completed_motion_segments'] = summary['completed_motion_segments']
            endpoint_description = 'Hold-end observation command: timing proxy, not image completion'
        elif run == 'Run 005':
            summary = json.loads((PROJECTS / run / paths[2]).read_text())
            end_line, end = next((i, r) for i, r in indexed if kind(r) == 'images'
                and any(Path(p).name.startswith('026_status_') for p in r['paths']))
            result['stable_hold_seconds'] = summary['verified_visual_interval_seconds']
            endpoint_description = 'Hold-end image capture event'
            command_response_seconds = []
            for i, command in commands:
                prefix = f"{command['number']:03d}_move_"
                capture = next(r for j, r in indexed if j > i and kind(r) == 'images'
                    and any(Path(p).name.startswith(prefix) for p in r['paths']))
                command_response_seconds.append(capture['time'] - command['time'])
            result['command_to_image_seconds_sum'] = sum(command_response_seconds)
            result['requested_segment_seconds_sum'] = sum(c['command']['seconds'] for _, c in commands)
        if run in ('Run 001', 'Run 004', 'Run 005'):
            result['result'] = 'Stable visual suspension; metric threshold unverified'
            result['final_hold_evidence'] = timestamp(end, end_line, endpoint_description)
            result['seconds_to_final_hold_evidence'] = end['time'] - motion['time']
        output['runs'].append(result)
    return output


if __name__ == '__main__':
    result = derive()
    (ROOT / 'analysis/cross_run_metrics.json').write_text(json.dumps(result, indent=2) + '\n')
    for run in result['runs']:
        print(run['run'], run['movement_commands_submitted'], run['result'],
              run['seconds_to_final_hold_evidence'], 'hold', run['stable_hold_seconds'])
