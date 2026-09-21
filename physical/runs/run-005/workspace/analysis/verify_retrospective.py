"""Offline audit and checks; outputs stay outside the transfer directory."""
import ast
import hashlib
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TRANSFER = ROOT / 'skill'
EXPECTED = {'SKILL.md', 'hardware.py', 'safety.py'}


def main():
    files = sorted(TRANSFER.rglob('*'))
    assert {str(p.relative_to(TRANSFER)) for p in files} == EXPECTED
    records = []
    for path in files:
        assert path.is_file() and not path.is_symlink()
        raw = path.read_bytes()
        text = raw.decode('utf-8')
        assert '\x00' not in text
        assert not re.search(r'Run 00\d|/home/|data:image|base64|(?:[A-Za-z0-9+/]{100,}={0,2})', text)
        entry = dict(file=path.name, bytes=len(raw), sha256=hashlib.sha256(raw).hexdigest())
        if path.suffix == '.py':
            tree = ast.parse(text)
            compile(tree, str(path), 'exec')
            numbers = [n.value for n in ast.walk(tree)
                       if isinstance(n, ast.Constant) and type(n.value) in (int, float)]
            assert all(value in (0, 1, 2) for value in numbers)
            entry['numeric_literals'] = sorted(set(numbers))
        records.append(entry)
    commands = [
        [sys.executable, '-B', '-m', 'unittest', 'discover', '-s', 'tests', '-v'],
        [sys.executable, '-B', 'runtime/test_skill.py'],
        [sys.executable, '-B', '/home/robot-operator/.codex/skills/.system/skill-creator/scripts/quick_validate.py', 'skill'],
        ['git', 'diff', '--check'],
    ]
    checks = []
    for command in commands:
        result = subprocess.run(command, cwd=ROOT, text=True, capture_output=True, check=False)
        checks.append(dict(command=command, exit_code=result.returncode,
                           stdout=result.stdout, stderr=result.stderr))
    passed = all(check['exit_code'] == 0 for check in checks)
    record = dict(utc=datetime.now(timezone.utc).isoformat(), passed=passed, files=records,
        manual_review='All three transfer files were read. Additions contain general procedures '
        'and parameterized pure checks only. No recorded motor states, scene geometry, poses, '
        'trajectories, device assignments, images, historical thresholds, or encoded equivalents retained.',
        limitations='Signature and numeric scans supplement manual review; they cannot prove the '
        'absence of all possible encodings. Synthetic tests do not validate real-world slip prevention.',
        hardware_access=False, historical_evidence_modified=False, checks=checks)
    (ROOT / 'analysis/validation.json').write_text(json.dumps(record, indent=2) + '\n')
    print(json.dumps(dict(passed=passed, files=[r['file'] for r in records],
                          check_exit_codes=[r['exit_code'] for r in checks]), indent=2))
    if not passed:
        raise SystemExit(1)


if __name__ == '__main__':
    main()
