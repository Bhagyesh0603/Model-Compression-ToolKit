from PIL import Image, ImageDraw, ImageFont
from pathlib import Path
import math, subprocess, json, wave, textwrap
P=Path(__file__).resolve().parent
W,H=1920,1080
BG='#091411'; FG='#edf3e9'; MUT='#9aafa2'; GREEN='#c6f279'; TEAL='#59cab4'; RED='#e5927d'; LINE='#284137'
FONT='/System/Library/Fonts/Supplemental/Arial.ttf'; BOLD='/System/Library/Fonts/Supplemental/Arial Bold.ttf'
fonts={}
def ft(n,b=False):
 k=(n,b)
 if k not in fonts: fonts[k]=ImageFont.truetype(BOLD if b else FONT,n)
 return fonts[k]
scenes=[
('01 / THE CHALLENGE','Intelligence.\nWith less weight.','COMPRESSKIT', 'An image classifier can carry millions of learned weights. But deployment asks a different question. Can we keep useful intelligence, while using less storage and less time? This is CompressKit.'),
('02 / INSIDE A CNN','How an image\nbecomes a prediction.','IMAGE → FEATURES → CLASS', 'A convolutional neural network processes an image through layers. Early filters respond to simple patterns, such as edges. Deeper layers combine these patterns into features. A final classifier produces scores, and the highest score gives the prediction.'),
('03 / ESTABLISH THE BASELINE','Before changing anything,\nmeasure everything.','ACCURACY · LATENCY · SIZE', 'We load a trained model and preserve an untouched copy. We export the baseline to ONNX and measure accuracy, prediction latency, and file size. Training and calibration data stay separate from the test data used for evaluation.'),
('04 / HARDWARE AWARE','Smaller does not\nalways mean faster.','PROBE → CHOOSE → VERIFY', 'The toolkit checks the CPU for low precision instruction support. Eight bit arithmetic can reduce storage, but speed depends on the hardware and runtime. We use the hardware probe to guide precision, then verify performance with actual timing.'),
('05 / STRUCTURED PRUNING','Remove channels.\nReduce real computation.','STRUCTURE, NOT JUST ZEROS', 'Structured pruning removes entire feature channels. Unlike simply setting weights to zero, this changes the dimensions of the network. A dependency graph updates connected layers together, preserving compatible shapes, including around residual connections.'),
('06 / GRADUAL RECOVERY','Cut a little.\nLearn again.','PRUNE → FINE-TUNE → REPEAT', 'Large cuts can damage accuracy. Gradual pruning alternates smaller cuts with fine tuning. Batch normalization recalibration updates activation statistics using calibration data. It requires forward passes, without gradient based weight training. Recovery can help, but does not guarantee the original accuracy.'),
('07 / KNOWLEDGE DISTILLATION','The original model\nbecomes the teacher.','TEACHER → STUDENT', 'The original model teaches the compressed student. The student learns from correct labels and from the teacher’s output scores. These scores contain relationships between classes. Distillation can recover useful behavior lost during pruning. The teacher is not needed when the student is deployed.'),
('08 / QUANTIZATION','Fewer bits.\nA lighter model.','FP32 → INT8', 'Quantization represents values using fewer bits. Moving from thirty two bit floats to eight bit integers reduces raw weight storage by about four times, for the same number of weights. Calibration determines suitable ranges. Total file reduction varies, and some operations may remain in floating point.'),
('09 / QUANTIZATION AWARE TRAINING','Practice with\nrounding error.','SIMULATE → ADAPT → QUANTIZE', 'When rounding damages accuracy, quantization aware training simulates reduced precision during training. The weights adapt before final quantization. In our pipeline, the final deployment quantization comes after structural changes and training.'),
('10 / AUTOMATIC SEARCH','Give it a budget.\nLet measurements decide.','TRY THE CHEAPEST OPTION FIRST', 'Automatic mode starts with quantization. If only accuracy fails, it can protect sensitive layers, then try quantization aware training and distillation. If size or latency fails, it explores pruning. Each candidate is measured. The search stops when the requirements are met, if a suitable configuration is found.'),
('11 / RECORDED EVIDENCE','A real trade-off.\nMeasured, not assumed.','RESNET-56 / CIFAR-10', 'In our recorded ResNet fifty six run, model size fell from three point two eight to zero point five three megabytes. Latency improved by two point two five times. Accuracy changed from ninety three point one eight to ninety point five zero percent: a loss of two point six eight percentage points.'),
('12 / READY FOR INFERENCE','Same task.\nLess to carry.','COMPRESSKIT', 'The final output is an ONNX model, accompanied by an HTML report and machine readable results. A new image passes through the compressed model to produce a prediction. CompressKit connects established techniques with hardware awareness, automatic decisions, and honest measurement.'),
]
def ease(x): return 1-(1-max(0,min(1,x)))**3
def txt(d,xy,s,n=28,c=FG,b=False): d.text(xy,s,font=ft(n,b),fill=c,spacing=12)
def line(d,pts,c=LINE,w=3): d.line(pts,fill=c,width=w)
def box(d,r,c=LINE,fill=None,rad=20): d.rounded_rectangle(r,rad,fill=fill,outline=c,width=2)
def arrow(d,x,y,x2,y2,c=GREEN):
 line(d,[(x,y),(x2,y2)],c,3); a=math.atan2(y2-y,x2-x)
 d.polygon([(x2,y2),(x2-15*math.cos(a-.5),y2-15*math.sin(a-.5)),(x2-15*math.cos(a+.5),y2-15*math.sin(a+.5))],fill=c)
def grid(d,x,y,cols,rows,s=20,gap=8,color=GREEN,progress=1):
 for r in range(rows):
  for c in range(cols):
   col=color if (r*cols+c)/(rows*cols)<progress else LINE
   d.rounded_rectangle((x+c*(s+gap),y+r*(s+gap),x+c*(s+gap)+s,y+r*(s+gap)+s),4,fill=col)
def network(d,x,y,p,compact=False):
 ns=[5,7,7,4] if not compact else [3,4,4,4]
 coords=[[(x+i*155,y+(7-n)*27+j*54) for j in range(n)] for i,n in enumerate(ns)]
 for i in range(3):
  for a in coords[i]:
   for b in coords[i+1]: line(d,[a,b],LINE,2)
 for i,col in enumerate(coords):
  for j,(xx,yy) in enumerate(col):
   active=(p*3-i+j*.08)%3<.9
   d.ellipse((xx-12,yy-12,xx+12,yy+12),fill=GREEN if active else TEAL)

def visual(d,i,t,p):
 x=900;y=330
 if i==0:
  for j in range(6):
   xx=1000+j*105; yy=390+math.sin(t*.9+j*.5)*28
   grid(d,xx,yy,3,8,17,7,GREEN if j<3 else TEAL, .6+.4*math.sin(t*.5+j)**2)
  txt(d,(960,680),'LESS STORAGE.  LESS LATENCY.',25,GREEN,True)
  txt(d,(960,728),'The prediction still matters.',32)
 elif i==1:
  # Deliberately schematic input; not a claimed real activation map.
  box(d,(900,370,1070,540),TEAL)
  for r in range(8):
   for c in range(8):
    v=(r*13+c*7)%9
    d.rectangle((913+c*18,383+r*18,927+c*18,397+r*18),fill=[LINE,TEAL,GREEN][v%3])
  arrow(d,1088,450,1150,450)
  for j in range(3):
   for k in range(3): box(d,(1180+j*150+k*7,370-k*9,1270+j*150+k*7,530-k*9),TEAL if j%2 else GREEN,fill=BG,rad=6)
   grid(d,1202+j*150,370,3,6,12,9,TEAL if j%2 else GREEN,.35+.65*((t*.3+j*.2)%1))
  arrow(d,1610,450,1680,450)
  for k,v in enumerate([.82,.28,.13]):
   box(d,(1695,380+k*65,1830,412+k*65),LINE,fill=LINE,rad=5)
   d.rounded_rectangle((1695,380+k*65,1695+135*v*ease(t/2),412+k*65),5,fill=GREEN if k==0 else TEAL)
  for xx,s in [(900,'IMAGE'),(1170,'FILTERS'),(1440,'FEATURES'),(1680,'SCORES')]:txt(d,(xx,585),s,21,MUT,True)
  txt(d,(940,690),'Illustrative feature maps • not recorded activations',22,MUT)
 elif i==2:
  for j,(label,val,sub) in enumerate([('ACCURACY','93.18%','Correct predictions'),('LATENCY','1.892 ms','Time per inference'),('FILE SIZE','3.28 MB','Exported model')]):
   yy=325+j*150;box(d,(930,yy,1790,yy+125));txt(d,(965,yy+22),label,22,MUT,True);txt(d,(1300,yy+17),val,52,GREEN,True);txt(d,(965,yy+64),sub,25)
  txt(d,(940,810),'Recorded ResNet-56 baseline',24,MUT)
 elif i==3:
  box(d,(1130,350,1530,680),TEAL,fill='#10271e',rad=30)
  for j in range(10):
   xx=1150+j*39;line(d,[(xx,326),(xx,350)],TEAL,4);line(d,[(xx,680),(xx,704)],TEAL,4)
  txt(d,(1225,430),'CPU',75,GREEN,True);txt(d,(1205,545),'INT8 support?',28)
  txt(d,(970,780),'Hardware capability + measured execution',30,FG)
 elif i==4:
  cut=ease((t-2)/5)
  for j in range(8):
   gone=j%2==1; xx=980+j*97;yy=355+(150*cut if gone else 0)
   color=LINE if gone and cut>.3 else GREEN
   grid(d,xx,yy,2,7,22,7,color)
   if gone and cut>.3: line(d,[(xx,yy+85),(xx+51,yy+135)],RED,3)
  txt(d,(980,720),'ILLUSTRATION: 8 CHANNELS → 4 CHANNELS',26,GREEN,True)
  txt(d,(980,770),'Connected tensor shapes are updated together.',25,MUT)
 elif i==5:
  pts=[]
  vals=[.82,.47,.69,.43,.66,.40,.65,.43,.69]
  for j,v in enumerate(vals):pts.append((970+j*100,770-v*420))
  line(d,[(970,350),(970,800),(1810,800)],LINE,3)
  n=max(2,min(len(pts),int(p*len(pts))+2));line(d,pts[:n],GREEN,5)
  for xx,yy in pts[:n]:d.ellipse((xx-7,yy-7,xx+7,yy+7),fill=GREEN)
  txt(d,(990,330),'ACCURACY',22,MUT);txt(d,(1440,830),'PRUNING + RECOVERY STEPS',20,MUT)
  txt(d,(1000,880),'Conceptual curve • not experimental data',22,MUT)
 elif i==6:
  network(d,965,390,t*.3);network(d,1390,600,t*.3,True)
  txt(d,(965,320),'ORIGINAL / TEACHER',25,GREEN,True)
  txt(d,(1390,900),'COMPRESSED / STUDENT',25,TEAL,True)
  arrow(d,1200,730,1380,730)
  txt(d,(970,825),'Labels + teacher scores',24,MUT)
 elif i==7:
  grid(d,980,350,8,4,34,10,GREEN)
  txt(d,(980,580),'32 BITS',36,FG,True)
  arrow(d,1370,440,1515,440)
  grid(d,1570,350,2,4,34,10,TEAL)
  txt(d,(1550,580),'8 BITS',36,FG,True)
  txt(d,(980,700),'~4× less raw weight storage',42,GREEN,True)
  txt(d,(980,765),'Same weight count; total file reduction varies.',25,MUT)
 elif i==8:
  for j in range(7):
   yy=360+j*58;line(d,[(990,yy),(1790,yy)],LINE,2)
  for j in range(32):
   xx=1000+j*24;v=math.sin(j*.23)*2.4+3; yy=360+v*58; target=360+round(v)*58; a=ease((t-1)/5); Y=yy+(target-yy)*a
   d.ellipse((xx-7,Y-7,xx+7,Y+7),fill=GREEN)
  txt(d,(1000,820),'Simulated rounding during training',31,GREEN)
 elif i==9:
  items=[('QUANTIZE','Try first'),('ACCURACY MISS','Protect layers → QAT → distill'),('SIZE / LATENCY MISS','Explore pruning'),('MEASURE','Stop when budget is met')]
  for j,(a,b) in enumerate(items):
   yy=320+j*133; active=int(p*4)==j
   box(d,(930,yy,1800,yy+108),GREEN if active else LINE,fill='#10271e' if active else None)
   txt(d,(958,yy+17),a,22,GREEN,True);txt(d,(958,yy+55),b,29)
 elif i==10:
  vals=[('MODEL SIZE','3.28','0.53','MB',.53/3.28),('LATENCY','1.892','0.842','ms',.842/1.892),('ACCURACY','93.18','90.50','%',90.5/93.18)]
  for j,(label,a,b,u,r) in enumerate(vals):
   yy=320+j*177;txt(d,(950,yy),label,23,MUT,True);txt(d,(1220,yy-5),f'{a} → {b} {u}',38,FG,True)
   d.rounded_rectangle((950,yy+60,1770,yy+80),8,fill=LINE)
   d.rounded_rectangle((950,yy+95,950+max(1,820*r*ease(t/2)),yy+115),8,fill=GREEN)
  txt(d,(950,885),'Intel i5-11320H • saved run • accuracy loss: 2.68 pp',23,MUT)
 elif i==11:
  network(d,1040,350,t*.4,True)
  for j,(a,b) in enumerate([('MODEL','ONNX'),('EVIDENCE','HTML + JSON'),('DEPLOY','Image → prediction')]):
   yy=670+j*68;txt(d,(980,yy),a,23,MUT,True);txt(d,(1220,yy),b,30,GREEN)

def frame(i,t,dur,global_t,total,caption):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 for xx in range(60,W,80):
  for yy in range(50,920,80):d.ellipse((xx,yy,xx+2,yy+2),fill='#183025')
 txt(d,(88,55),'C / K',32,GREEN,True);txt(d,(1580,62),'MODEL COMPRESSION',19,MUT,True)
 line(d,[(88,113),(1832,113)],LINE,2)
 tag,title,sub,_=scenes[i]
 txt(d,(90,177),tag,24,GREEN,True)
 offset=int(35*(1-ease(t/.9)))
 title_size=70
 while max(d.textlength(row,font=ft(title_size,True)) for row in title.split('\n'))>760: title_size-=1
 txt(d,(86,300+offset),title,title_size,FG,True)
 txt(d,(90,535+offset),sub,23,GREEN,True)
 descriptions=['A hardware-aware compression toolkit.','Patterns become features. Features become decisions.','The original model is our reference.','Precision choices depend on the target machine.','Fewer channels. Smaller tensors.','Accuracy is a constraint, not an assumption.','Recover behavior through guided learning.','Keep useful information with fewer bits.','Adapt before final deployment quantization.','No need to run every stage every time.','6.2× smaller  /  2.25× faster','Built to make the trade-off visible.']
 for j,s in enumerate(textwrap.wrap(descriptions[i],38)):txt(d,(90,625+j*39),s,29,MUT)
 visual(d,i,t,t/dur)
 line(d,[(88,940),(1832,940)],LINE,2)
 lines=textwrap.wrap(caption,110)
 for j,s in enumerate(lines):
  width=d.textlength(s,font=ft(29));txt(d,((W-width)/2,963+j*37),s,29,FG)
 d.rectangle((0,1073,int(W*global_t/total),1080),fill=GREEN)
 return im

def main():
 manifest=[];allcaps=[];cursor=0
 for i,(tag,title,sub,narration) in enumerate(scenes):
  aiff=P/f'voice-{i:02}.aiff';wav=P/f'voice-{i:02}.wav'
  if not wav.exists():
   subprocess.run(['say','-v','Samantha','-r','158','-o',str(aiff),narration],check=True)
   subprocess.run(['ffmpeg','-y','-loglevel','error','-i',str(aiff),'-ar','48000','-ac','1',str(wav)],check=True)
  with wave.open(str(wav)) as f:vd=f.getnframes()/f.getframerate()
  dur=math.ceil((vd+1.4)*30)/30
  words=narration.split();chunks=[' '.join(words[j:j+16]) for j in range(0,len(words),16)]
  caps=[];st=.45
  for s in chunks:
   end=st+vd*len(s.split())/len(words);caps.append((st,end,s));allcaps.append((cursor+st,cursor+end,s));st=end
  manifest.append(dict(index=i,start=cursor,duration=dur,title=title.replace('\n',' '),narration=narration,captions=caps));cursor+=dur
 (P/'storyboard.json').write_text(json.dumps(manifest,indent=2))
 def stamp(s):
  ms=round(s*1000);return f'{ms//3600000:02}:{ms//60000%60:02}:{ms//1000%60:02},{ms%1000:03}'
 (P/'captions.srt').write_text('\n\n'.join(f'{j+1}\n{stamp(a)} --> {stamp(b)}\n{s}' for j,(a,b,s) in enumerate(allcaps)))
 for m in manifest:
  i=m['index'];dur=m['duration'];out=P/f'scene-{i:02}.mp4'
  preview=frame(i,min(6,dur*.5),dur,m['start']+dur*.5,cursor,'')
  preview.resize((960,540)).save(P/f'preview-{i:02}.jpg')
  if out.exists():continue
  cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-vcodec','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','-','-i',str(P/f'voice-{i:02}.wav'),'-filter_complex','[1:a]adelay=450|450,apad[a]','-map','0:v','-map','[a]','-c:v','libx264','-preset','ultrafast','-crf','19','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-t',str(dur),str(out)]
  proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
  for n in range(round(dur*30)):
   t=n/30;cap=next((s for a,b,s in m['captions'] if a<=t<b),'')
   im=frame(i,t,dur,m['start']+t,cursor,cap)
   proc.stdin.write(im.tobytes())
  proc.stdin.close()
  if proc.wait()!=0:raise RuntimeError('render failed')
  print(f'Scene {i+1}/12 rendered ({dur:.1f}s)',flush=True)
 (P/'concat.txt').write_text('\n'.join(f"file 'scene-{i:02}.mp4'" for i in range(len(scenes))))
 subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(P/'concat.txt'),'-c','copy','-movflags','+faststart',str(P/'CompressKit-Presentation.mp4')],check=True)
 sheet=Image.new('RGB',(1920,1620),BG)
 for i in range(12):
  im=Image.open(P/f'preview-{i:02}.jpg').resize((640,540//(960//640))) if False else Image.open(P/f'preview-{i:02}.jpg').resize((640,360))
  sheet.paste(im,((i%3)*640,(i//3)*405))
 sheet.save(P/'storyboard.jpg')
 print(f'DONE: {cursor:.1f} seconds',flush=True)
if __name__=='__main__':main()
