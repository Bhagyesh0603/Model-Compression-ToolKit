"""Sync each chapter to a numbered voice track; never change speech speed.
Usage: python3 sync_voice.py /absolute/path/to/audio_folder
Expected tracks: 01.wav/mp3/m4a, 02..., through 11...
"""
from pathlib import Path
import subprocess,json,sys
P=Path(__file__).resolve().parent

def duration(p):
 return float(json.loads(subprocess.check_output(['ffprobe','-v','error','-show_entries','format=duration','-of','json',str(p)]))['format']['duration'])

def main():
 folder=Path(sys.argv[1]).expanduser().resolve();timeline=json.loads((P/'timeline.json').read_text());tracks=[]
 for chapter in timeline:
  n=chapter['scene'];found=[p for p in folder.glob(f'{n:02}.*') if p.suffix.lower() in ['.wav','.mp3','.m4a','.aac','.flac']]
  if len(found)!=1:raise SystemExit(f'Expected one voice file for {n:02}, found {len(found)}. No rendering started.')
  tracks.append(found[0])
 outputs=[]
 for chapter,voice in zip(timeline,tracks):
  n=chapter['scene'];video=P/f'chapter-{n:02}.mp4';length=duration(voice)+.45;factor=length/duration(video);out=P/f'voiced-{n:02}.mp4'
  subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(video),'-i',str(voice),'-filter_complex',f'[0:v]setpts={factor}*PTS,fps=30[v];[1:a]adelay=100,apad[a]','-map','[v]','-map','[a]','-t',str(length),'-c:v','libx264','-preset','fast','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k',str(out)],check=True)
  outputs.append(out)
 (P/'voiced-list.txt').write_text('\n'.join(f"file '{p.name}'" for p in outputs))
 final=P/'CompressKit-Final-Voiced.mp4'
 subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(P/'voiced-list.txt'),'-c','copy','-movflags','+faststart',str(final)],check=True)
 print(final)
if __name__=='__main__':main()
