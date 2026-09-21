"""Generic low-level helpers; all device assignments are runtime inputs."""
from pathlib import Path
from contextlib import contextmanager
import fcntl
import os
import stat
import time


def enumerate_current_devices():
    """Call in each approved namespace; this function does not escalate access."""
    nodes = []
    for pattern in ('ttyACM*', 'ttyUSB*', 'video*', 'serial/by-id/*', 'v4l/by-id/*'):
        for path in sorted(Path('/dev').glob(pattern)):
            info = path.stat()
            nodes.append(dict(path=str(path), target=str(path.resolve()),
                              mode=stat.filemode(info.st_mode),
                              readable=os.access(path, os.R_OK),
                              writable=os.access(path, os.W_OK)))
    metadata = []
    for kind in ('tty', 'video4linux'):
        for path in sorted((Path('/sys/class') / kind).glob('*')):
            if kind == 'tty' and not path.name.startswith(('ttyACM', 'ttyUSB')):
                continue
            row = dict(device=path.name, target=str(path.resolve()))
            for key in ('dev', 'name', 'device/uevent'):
                try:
                    row[key] = (path / key).read_text().strip()
                except OSError:
                    pass
            metadata.append(row)
    return dict(device_nodes=nodes, live_sysfs=metadata)


def require_evidence_destination(destination):
    path = Path(destination).resolve()
    transfer_root = Path(__file__).resolve().parent
    if path == transfer_root or transfer_root in path.parents:
        raise ValueError('Current-run evidence must remain outside the transfer skill')
    return path


@contextmanager
def exclusive_command_owner(lock_path):
    """Advisory process lock for cooperating current-session motor utilities.

    Acquire before opening motor buses and hold until all buses are closed.
    This does not detect noncooperating programs. Verify current ownership
    separately when an earlier tool session's process status is uncertain.
    Keep the lock outside this transfer directory; do not unlink an active lock.
    """
    path = require_evidence_destination(lock_path)
    with path.open('a') as handle:
        try:
            fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as exc:
            raise RuntimeError('A cooperating motor command owner is active') from exc
        try:
            yield
        finally:
            fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def discover_motor_models(port):
    """Read live IDs/models without changing actuator registers.

    Construct a new bus with explicit runtime assignments after discovery.
    Do not replace a connected bus's motor dictionary: driver lookup caches
    can retain the original assignment and decode feedback incorrectly.
    """
    from lerobot.motors.feetech.feetech import FeetechMotorsBus
    bus = FeetechMotorsBus(port, {}, calibration=None)
    try:
        bus.connect(handshake=False)
        bus.set_baudrate(bus.default_baudrate)
        return bus.broadcast_ping(raise_on_error=True)
    finally:
        if bus.is_connected:
            bus.disconnect(disable_torque=False)


class ReadOnlyFeetech:
    """Use explicit, freshly assigned motors; never load calibration files."""
    def __init__(self, port, motors):
        from lerobot.motors.feetech.feetech import FeetechMotorsBus
        self.bus = FeetechMotorsBus(port, motors, calibration=None)

    def __enter__(self):
        try:
            self.bus.connect(handshake=False)
            self.bus.set_baudrate(self.bus.default_baudrate)
            for name, motor in self.bus.motors.items():
                actual = self.bus.ping(name, raise_on_error=True)
                if actual != self.bus.model_number_table[motor.model]:
                    raise RuntimeError('Live motor model differs from runtime assignment')
        except BaseException:
            if self.bus.is_connected:
                self.bus.disconnect(disable_torque=False)
            raise
        return self

    def snapshot(self, registers):
        return {name: {register: self.bus.read(register, name, normalize=False)
                       for register in registers} for name in self.bus.motors}

    def __exit__(self, exc_type, exc, traceback):
        if self.bus.is_connected:
            self.bus.disconnect(disable_torque=False)


def capture_fresh(camera_config, destination, timeout_ms):
    """Capture through LeRobot; no persistent images or intrinsics are loaded."""
    import cv2
    from lerobot.cameras.opencv.camera_opencv import OpenCVCamera
    destination = require_evidence_destination(destination)
    camera = OpenCVCamera(camera_config)
    try:
        camera.connect()
        frame = camera.async_read(timeout_ms=timeout_ms)
        if not cv2.imwrite(str(destination), cv2.cvtColor(frame, cv2.COLOR_RGB2BGR)):
            raise OSError('Image could not be saved')
    finally:
        if camera.is_connected:
            camera.disconnect()
    return destination


def release_requested_torque(bus, motors):
    """Use after an explicit release request and exclusive bus ownership.

    Try every requested motor even if one fails. The caller must inspect all
    results and record them outside this directory. No arm roles are assumed.
    """
    results = {}
    for motor in motors:
        try:
            bus.write('Torque_Enable', motor, 0, normalize=False)
            observed = bus.read('Torque_Enable', motor, normalize=False)
            results[motor] = {'disabled': observed == 0, 'readback': observed}
        except Exception as exc:
            results[motor] = {'disabled': False, 'error': str(exc)}
    return results


def read_active_goals(bus, motors):
    """Read the current command before constructing a loaded segment.

    Keep the returned runtime values outside the transfer directory. Measured
    positions are separate feedback and must not silently replace these goals.
    """
    return bus.sync_read('Goal_Position', motors=list(motors), normalize=False)


def confirm_temperature_readings(bus, motor, sample_count, interval_seconds):
    """Corroborate a reading while the caller has paused motion.

    This reads no saved state, writes no registers, and does not clear a fault.
    The caller must evaluate these samples against current hardware protection
    and other evidence before deciding whether operation may continue.
    """
    if not isinstance(sample_count, int) or sample_count < 2:
        raise ValueError('Repeated confirmation requires multiple samples')
    if interval_seconds < 0:
        raise ValueError('The sampling interval must not be negative')
    readings = []
    for index in range(sample_count):
        if index:
            time.sleep(interval_seconds)
        readings.append(bus.read('Present_Temperature', motor, normalize=False))
    return readings
