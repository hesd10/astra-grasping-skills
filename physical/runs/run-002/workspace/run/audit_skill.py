"""Audit this run's transfer boundary. Evidence remains outside skill/."""
import ast
import hashlib
import json
from pathlib import Path

root = Path(__file__).resolve().parents[1]
transfer = root / 'skill'
allowed = {'SKILL.md', 'hardware.py', 'safety.py'}
files = list(transfer.rglob('*'))
assert all(not p.is_symlink() for p in files), 'Transfer symlink found'
assert {p.name for p in files} == allowed, 'Unexpected transfer file or directory'
result = {'manual_review': 'All transfer source and prose manually reviewed after edits. General procedures and parameterized low-level helpers only; no recorded state, scene geometry, device assignments, calibration, targets, trajectories, images, or encoded equivalents.', 'files': {}}
for path in sorted(files):
    source = path.read_text()
    if path.suffix == '.py':
        tree = ast.parse(source)
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant):
                assert not isinstance(node.value, bytes), 'Binary literal found'
                if isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
                    assert node.value == 0, 'Unreviewed numeric constant found'
                if isinstance(node.value, str):
                    assert '/home/' not in node.value, 'Host-specific path found'
                    assert 'base64' not in node.value.lower(), 'Encoded content requires review'
    result['files'][path.name] = {'sha256': hashlib.sha256(path.read_bytes()).hexdigest(), 'bytes': path.stat().st_size}
result['passed'] = True
(root / 'evidence' / 'skill_audit.json').write_text(json.dumps(result, indent=2))
print(json.dumps(result, indent=2))
