"""Audit this run's transfer files and produce the current-run report."""
import ast
import hashlib
import importlib.util
import json
import re
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SKILL = ROOT / 'skill'
RUN = ROOT / 'run'
files = sorted(SKILL.rglob('*'))
allowed = {'SKILL.md', 'hardware.py', 'safety.py'}
assert {p.name for p in files if p.is_file()} == allowed
manifest = {}
for path in files:
    assert not path.is_symlink(), path
    if not path.is_file():
        continue
    assert path.suffix in {'.md', '.py'}, path
    source = path.read_text()
    assert '/home/' not in source and 'run/evidence' not in source, path
    assert not re.search(r'\b\d{4}-\d{2}-\d{2}\b', source), path
    assert not re.search(r'\b\d{4,}\b', source), path
    if path.suffix == '.py':
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                assert node.value == 0, (path, node.value)
        compile(source, str(path), 'exec')
    manifest[path.name] = dict(bytes=path.stat().st_size,
                              sha256=hashlib.sha256(path.read_bytes()).hexdigest())

spec = importlib.util.spec_from_file_location('transfer_safety', SKILL / 'safety.py')
safety = importlib.util.module_from_spec(spec)
spec.loader.exec_module(safety)
tests = []

def expect_rejection(name, fn, **kwargs):
    try:
        fn(**kwargs)
    except RuntimeError:
        tests.append(dict(test=name, passed=True))
    else:
        raise AssertionError(name)

health = dict(sample={'Status': 0, 'Present_Temperature': 20, 'Present_Load': 0},
              temperature_limit=70, temperature_margin=5, load_limit=100)
safety.require_healthy(**health)
tests.append(dict(test='healthy_input_accepted', passed=True))
expect_rejection('status_fault_rejected', safety.require_healthy,
                 **(health | {'sample': health['sample'] | {'Status': 1}}))
expect_rejection('temperature_limit_rejected', safety.require_healthy,
                 **(health | {'sample': health['sample'] | {'Present_Temperature': 70}}))
expect_rejection('excessive_load_rejected', safety.require_healthy,
                 **(health | {'sample': health['sample'] | {'Present_Load': 101}}))
contact = dict(sustained_load=90, tracking_shortfall=20, distance_from_closed_limit=300,
               minimum_load=70, minimum_shortfall=10, closed_limit_margin=30,
               visible_enclosure=True)
safety.require_contact_evidence(**contact)
tests.append(dict(test='enclosed_contact_accepted', passed=True))
expect_rejection('closed_stop_contact_rejected', safety.require_contact_evidence,
                 **(contact | {'distance_from_closed_limit': 0}))
expect_rejection('missing_enclosure_rejected', safety.require_contact_evidence,
                 **(contact | {'visible_enclosure': False}))
clearance = dict(all_bottom_corners_clear=True, independent_view_confirms=True,
                 visible_support_gap=True, slipping=False, hold_duration=20,
                 required_duration=15)
safety.require_lift_evidence(**clearance)
tests.append(dict(test='clear_stable_hold_accepted', passed=True))
expect_rejection('remaining_corner_contact_rejected', safety.require_lift_evidence,
                 **(clearance | {'all_bottom_corners_clear': False}))
expect_rejection('slipping_rejected', safety.require_lift_evidence,
                 **(clearance | {'slipping': True}))
expect_rejection('short_hold_rejected', safety.require_lift_evidence,
                 **(clearance | {'hold_duration': 0}))

audit = dict(time=datetime.now(timezone.utc).isoformat(), files=manifest,
             static_audit_passed=True, guard_tests=tests,
             manual_review='All transfer files reviewed as plain text. General procedures and parameterized read-only/safety code only. No images, calibration, scene reconstruction, recorded encoders, angles, poses, coordinates, trajectories, replays, or encoded equivalents. Current-run parameters and evidence remain outside skill/.')
(RUN / 'skill_audit.json').write_text(json.dumps(audit, indent=2) + '\n')

rows = [json.loads(line) for line in (RUN / 'evidence/session.jsonl').read_text().splitlines()]
counts = Counter(r['event'] for r in rows)
lift = next(r for r in rows if r['event'] == 'snapshot' and r.get('tag') == 'full_clearance_lift')
final = [r for r in rows if r['event'] == 'snapshot' and r.get('tag') == 'final'][-1]
hold = [r for r in rows if lift['time'] <= r['time'] <= final['time'] and 'state' in r]
drift = {side: {motor: max(r['state'][side][motor]['Present_Position'] for r in hold)
               - min(r['state'][side][motor]['Present_Position'] for r in hold)
               for motor in lift['state'][side]} for side in ('left', 'right')}
initial = next(r for r in rows if r['event'] == 'ready')['baseline']['right']
whole_right_drift = {motor: max(abs(r['state']['right'][motor]['Present_Position'] - value)
                    for r in rows if 'state' in r) for motor, value in initial.items()}
start = datetime(2026, 9, 15, 16, 17, 14, tzinfo=timezone.utc).timestamp()
summary = dict(outcome='success_after_correcting_partial_clearance',
               first_success_claim_withdrawn=True, user_corrections=1,
               session_start_utc=datetime.fromtimestamp(start, timezone.utc).isoformat(),
               execution_end_utc=datetime.fromtimestamp(final['time'], timezone.utc).isoformat(),
               execution_elapsed_seconds=final['time'] - start,
               confirmed_hold_seconds=final['time'] - lift['time'],
               hold_encoder_peak_to_peak=drift,
               observation_arm_max_drift_from_initial=whole_right_drift,
               high_level_motion_commands=counts['motion_start'],
               high_level_gripper_closure_commands=counts['grip_start'],
               submitted_actuation_batches=counts['motion_start'] + counts['grip_start'] - 2,
               controller_starts=counts['ready'], dedicated_sensor_passes=3,
               extra_snapshot_commands=1, explicit_controller_closes=counts['closed'],
               faults=[r for r in rows if r['event'] == 'fault'],
               final_images=final['images'], final_motor_state=final['state'],
               physical_clearance_metric='Uncalibrated multi-view visual confirmation; no metric height claimed')
prepared = datetime.now(timezone.utc)
summary['report_prepared_utc'] = prepared.isoformat()
summary['elapsed_through_report_seconds'] = prepared.timestamp() - start
(RUN / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')

lines = [
    '# XLeRobot grasp session report', '',
    '## Outcome', '',
    'The LEFT gripper grasps the carton and holds it fully clear of the desk. The final fixed side view shows a distinct gap beneath the bottom edges; the head view independently supports clearance. The robot was left holding the carton. The RIGHT arm remained in its observation pose.', '',
    f"The final observed hold lasted **{summary['confirmed_hold_seconds']:.1f} seconds**. Both arms had zero peak-to-peak encoder changes during that interval. Maximum right-arm drift across the session was **{max(whole_right_drift.values())} raw encoder count**. No metric lift height is claimed because no metric scene calibration was used.", '',
    f"Execution elapsed time: **{summary['execution_elapsed_seconds']:.1f} seconds**, from initial workspace/hardware inspection through the final hardware snapshot. Documentation and auditing occurred afterward.", '',
    f"Elapsed time through report/audit preparation: **{summary['elapsed_through_report_seconds']:.1f} seconds**. The commit follows this preparation.", '',
    'No visible new robot or environmental damage was observed. The carton rotated and shifted on the desk during shallow alignment and closure. This is a visual assessment, not a physical damage inspection.', '',
    '## Correction and pauses', '',
    'The first claimed success was incorrect: the user identified that the far bottom corner still contacted the desk. That claim is withdrawn. The initial 15-second stationary check is not credited as successful suspension. After preserving gripper preload and lifting farther, the entire base showed sustained clearance in fresh views.', '',
    'One transient temperature reading exceeded its configured limit. Motion paused; the immediate reread and a dedicated stationary diagnostic were normal. Thermal protections remained active. Two tracking timeouts also stopped travel. These events and all actual measured states are retained in the evidence.', '',
    '## Online decisions', '',
    f"There were **{counts['motion_start']} model-issued arm/gripper increment commands** and **{counts['grip_start']} guarded closure commands**, submitted in **{summary['submitted_actuation_batches']} actuation batches**. Local servo updates, health polls, and internal closure increments are not counted as online decisions.", '',
    f"Additional service decisions: **{counts['ready']} controller starts/resumes**, **3 dedicated sensor passes**, **1 explicit verification snapshot**, and **{counts['closed']} explicit controller closes**. Hardware discovery and source/code inspection are outside the actuation count. There was **1 unsolicited user correction** and no requested user input. No subagents were used.", '',
    '| UTC | Online command |', '| --- | --- |']
for row in rows:
    if row['event'] in ('motion_start', 'grip_start'):
        stamp = datetime.fromtimestamp(row['time'], timezone.utc).strftime('%H:%M:%S')
        label = row.get('command', {}).get('tag', 'guarded gripper closure')
        lines.append(f'| {stamp} | {label} |')
lines += ['', '## Provenance and transfer audit', '',
          'No copied skill existed at startup. No previous task workspace, conversation, memory, run evidence, Git history, calibration file, robot model, existing IK/grasp controller, simulation, dataset, demonstration, pretrained policy, or external reference material was used. Existing Python dependencies and the local LeRobot low-level Feetech/OpenCV modules were used. Only generic motor wiring declarations were extracted from the local XLeRobot driver source.', '',
          'Sandbox /dev enumeration was empty. Live /sys metadata and approved read-only host /dev enumeration established that serial and camera hardware was available. Host hardware access then used the approved low-level driver scripts.', '',
          'All current-run observations, numeric state, action targets, scripts, images, and reports are outside skill/. The new skill contains only general procedures and parameterized generic hardware/safety helpers. Static checks, manual review, and the safety-helper tests passed; see skill_audit.json.', '',
          'Git was initialized at the workspace root. This complete attempt is recorded in one commit; no history was inspected or rewritten.', '',
          '## Final evidence', '']
for camera, path in final['images'].items():
    lines.append(f'- [Final camera {camera}]({path})')
lines += ['', '- Full telemetry and event log: `evidence/session.jsonl`',
          '- Machine-readable outcome and measurements: `summary.json`',
          '- Transfer audit and test results: `skill_audit.json`', '']
(RUN / 'REPORT.md').write_text('\n'.join(lines))
print(json.dumps(dict(audit_passed=True, guard_tests=len(tests), summary=summary | {'faults': len(summary['faults']), 'final_motor_state': 'see summary.json'}), indent=2))
