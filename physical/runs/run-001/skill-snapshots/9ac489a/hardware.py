"""Generic read-only hardware helpers; all device assignments are runtime inputs."""
from pathlib import Path
import os
import stat


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


class ReadOnlyFeetech:
    """Use explicit, freshly assigned motors; never load calibration files."""
    def __init__(self, port, motors):
        from lerobot.motors.feetech.feetech import FeetechMotorsBus
        self.bus = FeetechMotorsBus(port, motors, calibration=None)

    def __enter__(self):
        try:
            self.bus.connect()
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
