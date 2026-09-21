"""Bounded, observed joint-space increments using only LeRobot hardware drivers."""
import json
import queue
import sys
import threading
import time
from pathlib import Path

import cv2
from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
from lerobot.cameras.opencv.configuration_opencv import OpenCVCameraConfig
from lerobot.motors.feetech.feetech import FeetechMotorsBus
from lerobot.motors.motors_bus import Motor, MotorNormMode

OUT = Path(__file__).resolve().parent / 'evidence'
LOG = (OUT / 'session.jsonl').open('a', buffering=1)
buses = {}
cameras = {}
commands = queue.Queue()
limits = {}
baseline = {}
active = False
faulted = False

def emit(event, **data):
    row = dict(time=time.time(), event=event, **data)
    line = json.dumps(row)
    LOG.write(line + '\n')
    print(line, flush=True)

def read(bus, key, name):
    return int(bus.read(key, name, normalize=False))

def state():
    return {side: {name: {key: read(bus, key, name) for key in
        ('Present_Position', 'Present_Load', 'Present_Temperature', 'Present_Current', 'Status', 'Torque_Enable')}
        for name in bus.motors} for side, bus in buses.items()}

def check(s):
    for side, motors in s.items():
        for name, row in motors.items():
            if row['Status']:
                raise RuntimeError(f'{side}/{name} status fault: {row}')
            if row['Present_Temperature'] >= limits[side][name]['temperature'] - 5:
                raise RuntimeError(f'{side}/{name} temperature near configured limit: {row}')
            if abs(row['Present_Load']) > 650:
                raise RuntimeError(f'{side}/{name} excessive load: {row}')
            if side == 'right' and active and abs(row['Present_Position'] - baseline[side][name]) > 12:
                raise RuntimeError(f'Right arm moved outside hold tolerance: {row}')

def snapshot(tag, s=None):
    if not tag.replace('_', '').isalnum():
        raise ValueError('Invalid snapshot tag')
    s = state() if s is None else s
    paths = {}
    for index, camera in cameras.items():
        frame = camera.async_read(timeout_ms=1000)
        p = OUT / f'{tag}_video{index}.jpg'
        if p.exists():
            p = OUT / f'{tag}_{time.time_ns()}_video{index}.jpg'
        cv2.imwrite(str(p), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR))
        paths[index] = str(p)
    emit('snapshot', tag=tag, state=s, images=paths)

def input_loop():
    for line in sys.stdin:
        try:
            commands.put(json.loads(line))
        except Exception as exc:
            emit('input_error', error=str(exc))
    commands.put({'op': 'quit'})

try:
    # Bus roles inferred this run from live responding head/wheel IDs and the
    # generic XLeRobot motor-name wiring declarations; these are not transferable.
    for side, port in (('left', '/dev/ttyACM1'), ('right', '/dev/ttyACM0')):
        bus = FeetechMotorsBus(port, {str(i): Motor(i, 'sts3215', MotorNormMode.RANGE_M100_100) for i in range(1, 7)})
        bus.connect()
        buses[side] = bus
        limits[side] = {name: {'min': read(bus, 'Min_Position_Limit', name),
                               'max': read(bus, 'Max_Position_Limit', name),
                               'temperature': read(bus, 'Max_Temperature_Limit', name)} for name in bus.motors}
        for name in bus.motors:
            if read(bus, 'Operating_Mode', name) != 0:
                raise RuntimeError('Expected position mode')
    for index in (6, 8, 10):
        camera = OpenCVCamera(OpenCVCameraConfig(index_or_path=index, width=640, height=480, fourcc='MJPG'))
        camera.connect()
        cameras[index] = camera
    s = state()
    check(s)
    baseline = {side: {name: row['Present_Position'] for name, row in motors.items()} for side, motors in s.items()}
    snapshot('before_enable', s)
    # Load current encoder positions before enabling torque; no stale goal is used.
    for side, bus in buses.items():
        for name in bus.motors:
            bus.write('Goal_Velocity', name, 90, normalize=False)
            bus.write('Acceleration', name, 5, normalize=False)
            if not s[side][name]['Torque_Enable']:
                bus.write('Goal_Position', name, baseline[side][name], normalize=False)
                bus.enable_torque(name)
    active = True
    emit('ready', baseline=baseline)
    threading.Thread(target=input_loop, daemon=True).start()
    last_record = 0
    while True:
        s = state()
        check(s)
        if time.monotonic() - last_record > 1:
            LOG.write(json.dumps(dict(time=time.time(), event='health', state=s)) + '\n')
            last_record = time.monotonic()
        try:
            command = commands.get(timeout=0.1)
        except queue.Empty:
            continue
        op = command.get('op')
        if op == 'quit':
            snapshot('final')
            emit('closed', torque='preserved to support stationary arms')
            break
        if op == 'snapshot':
            snapshot(command['tag'])
            continue
        if op == 'grip':
            bus = buses['left']
            name = '6'
            start = read(bus, 'Present_Position', name)
            bus.write('Torque_Limit', name, 100, normalize=False)
            bus.write('Goal_Velocity', name, 45, normalize=False)
            goal = start
            contact = False
            emit('grip_start', start=start, torque_limit=100)
            for _ in range(18):
                goal = max(limits['left'][name]['min'], goal - 20)
                bus.write('Goal_Position', name, goal, normalize=False)
                contact_samples = 0
                for _ in range(8):
                    time.sleep(0.1)
                    s = state()
                    check(s)
                    LOG.write(json.dumps(dict(time=time.time(), event='grip_health', goal=goal, state=s)) + '\n')
                    row = s['left'][name]
                    if abs(row['Present_Load']) >= 70 and row['Present_Position'] - goal >= 10:
                        contact_samples += 1
                    else:
                        contact_samples = 0
                    if contact_samples >= 3:
                        contact = True
                        break
                if contact or goal == limits['left'][name]['min']:
                    break
            emit('grip_result', contact_detected=contact, goal=goal, state=s)
            snapshot(command['tag'])
            continue
        if op != 'step':
            emit('rejected', reason='Unknown command')
            continue
        deltas = command.get('delta', {})
        if not deltas or any(name not in buses['left'].motors or not isinstance(delta, int) or abs(delta) > 180 for name, delta in deltas.items()):
            emit('rejected', reason='Only left motor increments of at most 180 counts are accepted')
            continue
        targets = {name: s['left'][name]['Present_Position'] + delta for name, delta in deltas.items()}
        if any(target < limits['left'][name]['min'] or target > limits['left'][name]['max'] for name, target in targets.items()):
            emit('rejected', reason='Outside live hardware position limits')
            continue
        emit('motion_start', command=command, targets=targets)
        starts = {name: s['left'][name]['Present_Position'] for name in targets}
        settled_since = None
        last_positions = starts.copy()
        for name, target in targets.items():
            buses['left'].write('Goal_Position', name, target, normalize=False)
        deadline = time.monotonic() + 5
        while True:
            s = state()
            check(s)
            LOG.write(json.dumps(dict(time=time.time(), event='motion_health', state=s)) + '\n')
            if all(abs(s['left'][name]['Present_Position'] - target) <= 20 for name, target in targets.items()):
                break
            positions = {name: s['left'][name]['Present_Position'] for name in targets}
            if all(abs(positions[name] - last_positions[name]) <= 2 for name in targets):
                settled_since = time.monotonic() if settled_since is None else settled_since
            else:
                settled_since = None
            last_positions = positions
            if settled_since is not None and time.monotonic() - settled_since > 0.6 and all(
                abs(positions[name] - targets[name]) <= 80 and
                abs(positions[name] - starts[name]) >= abs(deltas[name]) / 2 and
                abs(s['left'][name]['Present_Load']) < 250 for name in targets):
                emit('settled_short', positions=positions, targets=targets)
                break
            if time.monotonic() > deadline:
                raise RuntimeError('Motion tracking timeout')
            time.sleep(0.06)
        time.sleep(0.25)
        snapshot(command['tag'])
except BaseException as exc:
    faulted = True
    emit('fault', error=str(exc))
    # Stop further travel at the live positions. Do not drop an unsupported arm.
    if active and 'left' in buses:
        for name in buses['left'].motors:
            if name == '6':
                continue  # Preserve an established grasp while arresting arm travel.
            try:
                pos = read(buses['left'], 'Present_Position', name)
                buses['left'].write('Goal_Position', name, pos, normalize=False)
            except Exception as hold_exc:
                emit('hold_error', motor=name, error=str(hold_exc))
    try:
        snapshot('fault_final')
    except Exception as capture_exc:
        emit('capture_error', error=str(capture_exc))
finally:
    for camera in cameras.values():
        if camera.is_connected:
            camera.disconnect()
    for bus in buses.values():
        if bus.is_connected:
            bus.disconnect(disable_torque=False)
    LOG.close()
