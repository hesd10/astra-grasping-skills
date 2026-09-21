"""Create muted 12x previews with a visible recording-gap card for Run 001."""
from pathlib import Path
import json,subprocess,os,hashlib,time,shutil
from concurrent.futures import ThreadPoolExecutor
ROOT=Path(__file__).resolve().parents[1]
WORK=ROOT/'work/video-processing'
WORK.mkdir(parents=True,exist_ok=True)
(ROOT/'videos/previews').mkdir(parents=True,exist_ok=True)
FF=os.environ.get('FFMPEG_BINARY') or shutil.which('ffmpeg')
if not FF:
 try:
  import imageio_ffmpeg
  FF=imageio_ffmpeg.get_ffmpeg_exe()
 except ImportError:
  raise SystemExit('Install FFmpeg or set FFMPEG_BINARY to an FFmpeg binary with libass and zscale support.')
SPEED=12

def sha256(path):
 h=hashlib.sha256()
 with path.open('rb') as f:
  while chunk:=f.read(8*1024*1024):h.update(chunk)
 return h.hexdigest()

def ass(path,title,gap=False):
 text=title if not gap else 'RECORDING INTERRUPTED\\NSeveral minutes of footage are missing.\\NPart 2 follows.\\NThis is not continuous footage.'
 path.write_text('[Script Info]\nScriptType: v4.00+\nPlayResX: 720\nPlayResY: 1280\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,DejaVu Sans,'+('28' if gap else '22')+',&H00FFFFFF,&H00FFFFFF,&H00000000,&H80000000,0,0,0,0,100,100,0,0,1,2,1,'+('5' if gap else '7')+',20,20,20,1\n[Events]\nFormat: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text\nDialogue: 0,0:00:00.00,9:59:59.00,Default,,0,0,0,,'+text+'\n')

def execute(args,log):
 with log.open('w') as f:subprocess.run([str(FF),'-hide_banner','-nostdin','-y',*args],stdout=f,stderr=f,check=True)

def process(item):
 n=item['run'];tag=f'run-{n:03}';pieces=[]
 for i,filename in enumerate(item['files'],1):
  source=ROOT/'videos/originals'/filename
  if not source.is_file():raise FileNotFoundError(source)
  label=WORK/f'{tag}-part{i}.ass';ass(label,f'Run {n:03} | 12x speed | muted'+(f' | part {i}/2' if n==1 else ''))
  out=WORK/f'{tag}-part{i}.mp4'
  vf=f'setpts=(PTS-STARTPTS)/{SPEED},fps=30,scale=720:1280:force_original_aspect_ratio=decrease,pad=720:1280:(ow-iw)/2:(oh-ih)/2,setsar=1,zscale=t=linear:npl=100,format=gbrpf32le,zscale=p=bt709,tonemap=tonemap=hable:desat=0,zscale=t=bt709:m=bt709:r=tv,format=yuv420p,ass={label}'
  execute(['-threads','4','-i',str(ROOT/'videos/originals'/filename),'-map','0:v:0','-an','-vf',vf,'-c:v','libx264','-threads','4','-preset','fast','-crf','25','-pix_fmt','yuv420p','-color_primaries','bt709','-color_trc','bt709','-colorspace','bt709','-map_metadata','-1','-movflags','+faststart',str(out)],WORK/f'{tag}-part{i}.log')
  pieces.append(out)
  print('ENCODED',out.name,flush=True)
  if n==1 and i==1:
   card=WORK/'gap.ass';ass(card,'',True);gap=WORK/'run-001-gap.mp4'
   execute(['-f','lavfi','-i','color=c=black:s=720x1280:r=30:d=3','-vf',f'ass={card}','-an','-c:v','libx264','-pix_fmt','yuv420p','-threads','2',str(gap)],WORK/'gap.log');pieces.append(gap)
 dest=ROOT/'videos/previews'/f'{tag}-12x-muted.mp4'
 if len(pieces)==1:os.replace(pieces[0],dest)
 else:
  concat=WORK/'concat.txt';concat.write_text(''.join(f"file '{p}'\n" for p in pieces))
  execute(['-f','concat','-safe','0','-i',str(concat),'-map','0:v:0','-an','-c','copy','-movflags','+faststart',str(dest)],WORK/'concat.log')
 print('PREVIEW READY',tag,dest.stat().st_size,flush=True)
 return {'run':n,'path':str(dest.relative_to(ROOT)),'speed':SPEED,'audio':False,'gap_card_seconds':3 if n==1 else 0,'size':dest.stat().st_size,'sha256':sha256(dest)}

if __name__=='__main__':
 mapping=json.loads((ROOT/'videos/processing.json').read_text())['runs']
 with ThreadPoolExecutor(max_workers=2) as pool:results=list(pool.map(process,mapping))
 (WORK/'preview_results.json').write_text(json.dumps(results,indent=2)+'\n')
