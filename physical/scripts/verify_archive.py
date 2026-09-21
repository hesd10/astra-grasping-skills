"""Verify copied source files, keyframes and links in newly authored pages, offline."""
from pathlib import Path
from urllib.parse import unquote
import hashlib,json,re
ROOT=Path(__file__).resolve().parents[1]
manifest=json.loads((ROOT/'provenance/source-files.json').read_text())
for item in manifest:
    p=ROOT/item['archive_path']
    assert p.is_file(),p
    assert p.stat().st_size==item['size'],p
    assert hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],p
frames=json.loads((ROOT/'analysis/keyframes.json').read_text())
for f in frames:
    assert hashlib.sha256((ROOT/f['path']).read_bytes()).hexdigest()==f['source_sha256'],f['path']
    if 'associated_log_event' in f:
        assert (ROOT/f['associated_log_event']['path']).is_file()
broken=[];pages=0
for p in ROOT.rglob('*.md'):
    rel=p.relative_to(ROOT)
    if 'workspace' in rel.parts or 'skill-snapshots' in rel.parts or p.name=='transcript.md':continue
    pages+=1
    for target in re.findall(r'\]\(([^\n)]+)\)',p.read_text()):
        target=target.strip().strip('<>').split('#')[0]
        if not target or re.match(r'[a-z]+:',target):continue
        dest=(p.parent/unquote(target)).resolve()
        if not dest.exists():broken.append((str(rel),target))
assert not broken,broken
images=sum(1 for p in ROOT.glob('runs/run-*/workspace/**/*') if p.suffix.lower() in ['.jpg','.jpeg','.png'])
assert images==687,images
# Public export contains only allowed record categories, no raw runtime context records.
allowed={'message','custom_tool_call','function_call','custom_tool_call_output','function_call_output','token_usage_record','task_started','task_complete','turn_aborted'}
for p in ROOT.glob('runs/run-*/conversation/events.jsonl'):
    for line in p.open():
        e=json.loads(line);assert e['type'] in allowed
        if e['type']=='message':assert e['role'] in ['user','assistant']
video_files=0
video_manifest=ROOT/'videos/manifest.json'
if video_manifest.exists():
    for run in json.loads(video_manifest.read_text()):
        if run.get('status') != 'imported_and_processed': continue
        for item in run['originals']+[run['preview']]:
            p=ROOT/item['path']
            if not p.exists() and '/originals/' in item['path']:
                print('LOCAL-ONLY original not in clone:', item['path'])
                continue
            assert p.is_file() and p.stat().st_size==item['size'],p
            digest=hashlib.sha256()
            with p.open('rb') as f:
                while chunk:=f.read(8*1024*1024):digest.update(chunk)
            assert digest.hexdigest()==item['sha256'],p
            video_files+=1
        assert (ROOT/run['preview']['poster']).is_file()
print(f'PASS: {len(manifest)} copied files; {images} images; {len(frames)} keyframes; {video_files} verified video files; links in {pages} authored/index pages.')
