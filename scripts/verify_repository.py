"""Offline repository audit; never invokes a robot, model provider or network."""
import argparse
import hashlib
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

ROOT=Path(__file__).resolve().parents[1]

def digest(p):
    h=hashlib.sha256()
    with p.open('rb') as f:
        while block:=f.read(8*1024*1024):h.update(block)
    return h.hexdigest()

def verify_bundle(root):
    manifest=json.loads((root/'SHA256SUMS.json').read_text())
    for name,expected in manifest.items():assert digest(root/name)==expected,name
    print(f'PASS: {len(manifest)} bundle file hashes.')

def main():
    parser=argparse.ArgumentParser();parser.add_argument('--bundle',type=Path)
    args=parser.parse_args()
    if args.bundle:return verify_bundle(args.bundle)
    subprocess.run([sys.executable,str(ROOT/'physical/scripts/verify_archive.py')],check=True)
    data=json.loads((ROOT/'results.json').read_text())
    assert set(data)=={'physical_grasp'} and len(data['physical_grasp'])==6
    measurements=json.loads((ROOT/'physical/analysis/execution_metrics.json').read_text())['runs']
    for actual, expected in zip(data['physical_grasp'], measurements):
        assert abs(actual['seconds']-expected['elapsed_seconds'])<1e-6
        assert actual['requests']==expected['execution_model_requests']
    assert [r['success'] for r in data['physical_grasp']]==[True,False,False,True,True,True]
    broken=[];pages=0
    for p in ROOT.rglob('*.md'):
        rel=p.relative_to(ROOT)
        if any(part in rel.parts for part in ('.git','workspace','skill-snapshots','subject','input-skill','experiments','reports','.browser-runtime','.venv','build')):continue
        if p.name.lower() in ('transcript.md',):continue
        pages+=1
        for target in re.findall(r'\]\(([^\n)]+)\)',p.read_text()):
            target=target.strip('<>').split('#')[0]
            if not target or re.match(r'[a-zA-Z]+:',target):continue
            if not (p.parent/unquote(target)).exists():broken.append((str(rel),target))
    assert not broken,broken
    print(f'PASS: {pages} reader-facing Markdown pages; six real-robot attempts and metric consistency.')

if __name__=='__main__':main()
