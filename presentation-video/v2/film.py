from PIL import Image,ImageDraw,ImageFont,ImageFilter
from pathlib import Path
import math,json,subprocess,sys,textwrap
P=Path(__file__).resolve().parent
W,H=1920,1080;FPS=30
BG=(6,13,17);FG=(238,244,238);MUT=(132,157,163);GREEN=(193,244,111);CYAN=(80,211,213);RED=(244,141,113);LINE=(31,58,66)
fonts={}
def font(n,b=False):
 k=(int(n),b)
 if k not in fonts:fonts[k]=ImageFont.truetype('/System/Library/Fonts/Supplemental/Arial'+(' Bold' if b else '')+'.ttf',int(n))
 return fonts[k]
def clamp(x):return max(0,min(1,x))
def ease(x):x=clamp(x);return x*x*(3-2*x)
def lerp(a,b,p):return a+(b-a)*p
def mix(a,b,p):return tuple(round(lerp(x,y,clamp(p))) for x,y in zip(a,b))
def text(d,x,y,s,n=30,c=FG,b=False,anchor=None):d.text((x,y),s,font=font(n,b),fill=c,anchor=anchor,spacing=12)
def center(d,y,s,n=40,c=FG,b=False):text(d,W/2,y,s,n,c,b,'mt')
def rule(d,pts,c=LINE,w=2):d.line(pts,fill=c,width=w)
def rect(d,xy,c=LINE,fill=None,r=12,w=2):d.rounded_rectangle(xy,r,outline=c,fill=fill,width=w)
def dot(d,x,y,r,c):d.ellipse((x-r,y-r,x+r,y+r),fill=c)
def pulse(d,x,y,r,c,p):
 dot(d,x,y,r+8,mix(BG,c,.15));dot(d,x,y,r,c)
 rr=r+30*p;d.ellipse((x-rr,y-rr,x+rr,y+rr),outline=mix(c,BG,p),width=2)
def arrow(d,a,b,c=GREEN,w=3):
 rule(d,[a,b],c,w);ang=math.atan2(b[1]-a[1],b[0]-a[0]);d.polygon([b,(b[0]-16*math.cos(ang-.5),b[1]-16*math.sin(ang-.5)),(b[0]-16*math.cos(ang+.5),b[1]-16*math.sin(ang+.5))],fill=c)
def flow(d,a,b,t,c=GREEN,speed=1):
 rule(d,[a,b],LINE,2)
 for k in range(3):
  p=(t*speed+k/3)%1;dot(d,lerp(a[0],b[0],p),lerp(a[1],b[1],p),5,c)
def label(d,x,y,s,c=CYAN):text(d,x,y,s,23,c,True)

SCENES=[
('A MODEL, TRANSFORMED',11,'Here’s how CompressKit makes an AI model smaller and faster, while measuring the accuracy it gives up. We start with a trained image classifier.'),
('FROM PIXELS TO PREDICTION',19,'An image enters the network as numbers. Convolution filters scan small regions, detecting patterns such as edges. Deeper layers combine patterns into useful features. The final classifier produces class scores. The highest score becomes the prediction.'),
('MEASURE THE ORIGINAL',14,'Before compression, we preserve the original model and measure its accuracy, latency, and file size. We also check the CPU, because lower precision is only useful for speed when the hardware and runtime support it.'),
('REMOVE CHANNELS, NOT JUST VALUES',18,'First, structured pruning. A channel represents a learned feature map. We remove selected channels and update the connected layers together. The tensors become smaller, so the network requires less computation. Simply replacing individual weights with zeros would not shrink those dimensions.'),
('CUT. RECOVER. REPEAT.',15,'Removing too much at once can damage accuracy. Instead, we can prune gradually and fine tune between cuts. Batch normalization recalibration updates the changed network’s activation statistics. These recovery steps can help, but they cannot guarantee the original accuracy.'),
('LET THE TEACHER GUIDE THE STUDENT',17,'Next, knowledge distillation. The untouched original model becomes the teacher. The smaller model is the student. The student learns from correct labels and the teacher’s class scores, helping it recover useful behavior. Only the student is needed for deployment.'),
('THE SAME WEIGHTS. FEWER BITS.',18,'Quantization reduces numerical precision. Thirty two bit floating point values are mapped to eight bit integers using calibrated scales. For the same weight count, raw weight storage can become about four times smaller. The complete file reduction varies, and some operations may stay in floating point.'),
('LEARN TO TOLERATE ROUNDING',13,'If rounding causes too much accuracy loss, quantization aware training simulates that error while the model is still trainable. The weights adapt before the final low precision model is exported.'),
('THE AUTOMATIC DECISION LOOP',21,'You can choose the stages manually, or give the toolkit a budget. Automatic search tries quantization first. If only accuracy fails, it can protect sensitive layers and try recovery. If latency or size fails, it explores pruning. Every candidate is measured. It stops when a configuration meets the requirements, if one is found.'),
('PROOF FROM A RECORDED RUN',20,'Here is one recorded result for ResNet fifty six on CIFAR ten. The model shrank from three point two eight to zero point five three megabytes, and inference became two point two five times faster. Accuracy changed from ninety three point one eight to ninety point five zero percent.'),
('DEPLOY THE COMPRESSED MODEL',12,'The final output is an ONNX model, with reports showing exactly what changed. A new image passes through the compressed network and produces a prediction. Less storage. Faster measured inference. An explicit accuracy trade off.'),
]
CAT=Image.open(P/'input-cat.png').convert('RGB');EDGE=Image.open(P/'input-edges.png').convert('RGB')

def prism(d,x,y,w,h,depth,c,hot=0):
 dx=depth*.7;dy=-depth*.45
 d.polygon([(x,y),(x+dx,y+dy),(x+w+dx,y+dy),(x+w,y)],fill=mix(BG,c,.2),outline=mix(BG,c,.5))
 d.polygon([(x+w,y),(x+w+dx,y+dy),(x+w+dx,y+h+dy),(x+w,y+h)],fill=mix(BG,c,.1),outline=mix(BG,c,.45))
 d.rectangle((x,y,x+w,y+h),fill=mix(BG,c,.13+hot*.3),outline=mix(BG,c,.65+hot*.35),width=2)

def model(d,t,x=380,y=520,scale=1,prune=0,depth=1,compact=False):
 # Stacked planes communicate channel widths, not literal architecture.
 for layer in range(6):
  xx=x+layer*205*scale;hh=(180+layer*34)*scale
  n=8 if not compact else 4
  for k in reversed(range(n)):
   rem=(k%2==1);off=prune*190*scale if rem else 0
   a=1-prune if rem else 1
   if a<.015:continue
   c=mix(BG,GREEN if layer<3 else CYAN,a)
   shift=math.sin(t*.6+layer*.25)*15*scale
   prism(d,xx+k*9*scale,y-hh/2-k*7*scale+off+shift,45*scale,hh,45*scale*depth,c,.25+.25*math.sin(t*2-layer))
  if layer<5:flow(d,(xx+100*scale,y+20),(xx+185*scale,y+20),t-layer*.12,GREEN,.6)

def image_card(im,d,img,x,y,size,c=CYAN):
 im.paste(img.resize((int(size),int(size)),Image.Resampling.NEAREST),(int(x),int(y)))
 d.rectangle((x-3,y-3,x+size+3,y+size+3),outline=c,width=3)

def graph(d,t,x,y,width,height,small=False,c=GREEN):
 ns=[4,6,6,3] if not small else [3,3,3,3]
 cols=[[(x+i*width/3,y+height/2+(j-(n-1)/2)*height/(max(ns)-1)) for j in range(n)] for i,n in enumerate(ns)]
 for i in range(3):
  for j,a in enumerate(cols[i]):
   for k,b in enumerate(cols[i+1]):
    rule(d,[a,b],mix(BG,c,.16),2)
    p=(t*.65+i*.2+j*.17+k*.13)%1
    if (j+k)%3==0:dot(d,lerp(a[0],b[0],p),lerp(a[1],b[1],p),3,c)
 for col in cols:
  for xx,yy in col:dot(d,xx,yy,9,c)
 return cols

def top(d,i,t):
 text(d,80,52,'COMPRESSKIT',23,FG,True)
 text(d,1840,52,f'{i+1:02} / {len(SCENES):02}',23,MUT,False,'ra')
 title=SCENES[i][0];center(d,120+20*(1-ease(t/.6)),title,37,FG,True)

def scene(i,t,duration):
 im=Image.new('RGB',(W,H),BG);d=ImageDraw.Draw(im)
 # Subtle moving perspective floor and particles unite all scenes.
 for j in range(12):
  xx=-900+j*340;rule(d,[(960+(xx-960)*.18,700),(xx,1080)],(13,27,34),1)
 for j in range(8):
  yy=700+((j*52+t*12)%380);rule(d,[(0,yy),(1920,yy)],(13,27,34),1)
 for j in range(30):
  x=(j*157.3+t*(3+j%4))%W;y=230+(j*91.7)%700;dot(d,x,y,1,(45,72,78))
 top(d,i,t)
 if i==0:
  p=ease((t-2)/5);z=1.12-.2*p
  model(d,t,x=290+80*p,y=540,scale=z,prune=p)
  center(d,830,'TRAINED MODEL  →  COMPRESSED MODEL',32,GREEN,True)
  center(d,900,'Size ↓     Latency: measured     Accuracy: checked',27,MUT)
 elif i==1:
  if t<7:
   image_card(im,d,CAT,230,310,420)
   label(d,230,775,'REAL CIFAR-10 INPUT / 32 × 32 PIXELS')
   # Moving receptive field, projected into an edge-map result.
   q=(t/5)%1;cx=230+int(q*5)*70;cy=310+int(t*1.5)%5*70
   rect(d,(cx,cy,cx+140,cy+140),GREEN,r=0,w=5)
   flow(d,(cx+140,cy+70),(1110,520),t,CYAN,.5)
   image_card(im,d,EDGE,1110,310,420,GREEN)
   label(d,1110,775,'EDGE RESPONSE / ILLUSTRATION')
   center(d,895,'Filters scan local regions and produce feature maps.',30)
  else:
   a=ease((t-7)/1.5)
   image_card(im,d,CAT,100,420,180)
   for j in range(5):
    xx=390+j*210;hh=180+j*28
    for k in reversed(range(4)):prism(d,xx+k*11,510-hh/2-k*10,52,hh,40,GREEN if j<2 else CYAN,((t-j*.4)%2)/2)
    flow(d,(xx+96,510),(xx+187,510),t-j*.1,CYAN,.7)
   label(d,100,690,'INPUT')
   label(d,390,760,'EDGES');label(d,800,760,'FEATURES');label(d,1260,760,'CLASS SCORES')
   for j,(s,v) in enumerate([('CAT',.85),('DOG',.11),('OTHER',.04)]):
    yy=400+j*115;text(d,1530,yy,s,24,GREEN if j==0 else MUT,True)
    rect(d,(1530,yy+40,1810,yy+65),LINE,LINE,4)
    rect(d,(1530,yy+40,1530+max(1,280*v*ease((t-10)/2)),yy+65),GREEN if j==0 else CYAN,GREEN if j==0 else CYAN,4)
   center(d,880,'Highest score → predicted class',33,GREEN,True)
   center(d,950,'Schematic network and example scores; not captured model activations.',20,MUT)
 elif i==2:
  if t<7:
   model(d,t,200,470,.62)
   for j,(a,b) in enumerate([('ACCURACY','93.18%'),('LATENCY','1.892 ms'),('SIZE','3.28 MB')]):
    yy=315+j*155;aa=ease((t-j*.4)/1.2)
    text(d,1180,yy,a,23,MUT,True);text(d,1180+35*(1-aa),yy+40,b,65,mix(BG,FG,aa),True)
   center(d,880,'Preserve the original. Establish the baseline.',33,GREEN)
   center(d,947,'Baseline numbers: recorded ResNet-56 / CIFAR-10 run.',20,MUT)
  else:
   x,y=810,350;rect(d,(x,y,x+300,y+300),CYAN,(11,32,40),20,3)
   for k in range(12):
    for side in [-1,1]:
     xx=x+side*30+(300 if side==1 else 0);rule(d,[(xx,y+20+k*24),(xx-side*30,y+20+k*24)],CYAN,4)
   center(d,445,'CPU',78,GREEN,True)
   sy=y+((t-7)*80)%300;rule(d,[(x+8,sy),(x+292,sy)],GREEN,3)
   for j,(s,xx,yy) in enumerate([('PRECISION',300,370),('INSTRUCTIONS',1310,370),('RUNTIME',300,620),('REAL LATENCY',1310,620)]):
    label(d,xx,yy,s);flow(d,(xx+100,yy+55),(960,500),t+j,CYAN,.4)
   center(d,860,'Hardware probe → precision choice → measured timing',33,FG)
 elif i==3:
  if t<5:
   center(d,240,'ZEROS DO NOT CHANGE TENSOR DIMENSIONS',26,RED,True)
   for j in range(100):
    x=420+(j%20)*54;y=340+(j//20)*70;v=0 if j%3==0 and t>1.5 else ((j*7)%9)+1
    text(d,x,y,str(v),35,RED if v==0 else MUT,True)
   center(d,820,'Unstructured sparsity still needs suitable execution support.',28,MUT)
  else:
   p=ease((t-6)/5)
   for layer in range(3):
    x=270+layer*550
    for j in range(8):
     remove=j in [1,3,5,7]; xx=x+j*43; yy=350
     if remove:
      yy+=p*400;c=mix(RED,BG,p)
      if p>.98:continue
     else:
      xx-=p*(j//2)*43;c=GREEN if layer<2 else CYAN
     prism(d,xx,yy,28,300,33,c,.3)
    if layer<2:flow(d,(x+360-170*p,500),(x+510,500),t,CYAN,.5)
    label(d,x,770,f'LAYER {layer+1} / '+('8 CHANNELS' if p<.5 else '4 CHANNELS'))
   center(d,875,'Remove complete channels. Update dependent layers.',35,GREEN,True)
   center(d,950,'Illustrative channel counts, not the exact ResNet-56 architecture.',20,MUT)
 elif i==4:
  vals=[.86,.50,.76,.44,.70,.42,.68,.40,.66]
  points=[(270+j*170,780-v*470) for j,v in enumerate(vals)]
  rule(d,[(230,280),(230,820),(1700,820)],LINE,3)
  text(d,110,260,'ACCURACY',23,MUT,True)
  q=clamp((t-1)/(duration-3))*8;n=min(7,int(q));part=q-n
  pp=points[:n+1]+[(lerp(points[n][0],points[n+1][0],part),lerp(points[n][1],points[n+1][1],part))]
  rule(d,pp,GREEN,5)
  for j,(x,y) in enumerate(pp[:-1]):dot(d,x,y,7,GREEN)
  x,y=pp[-1];pulse(d,x,y,10,GREEN,(t*.8)%1)
  cut=n%2==0;center(d,220,'PRUNE' if cut else 'FINE-TUNE',43,RED if cut else GREEN,True)
  for j in range(4):
   label(d,370+j*340,850,f'CYCLE {j+1}',MUT)
  center(d,930,'Conceptual recovery curve • recalibration updates normalization statistics',24,MUT)
 elif i==5:
  graph(d,t,220,300,510,340,False,CYAN);graph(d,t,1170,405,420,230,True,GREEN)
  label(d,220,235,'ORIGINAL / TEACHER',CYAN);label(d,1170,320,'COMPRESSED / STUDENT',GREEN)
  for j,v in enumerate([.75,.18,.07]):
   yy=735+j*45;end=290+370*v
   rule(d,[(290,yy),(end,yy)],CYAN,17)
   v2=lerp([.45,.35,.20][j],v,ease((t-3)/8));rule(d,[(1260,yy),(1260+370*v2,yy)],GREEN,17)
   text(d,200,yy-15,['CAT','DOG','OTHER'][j],20,MUT)
  for j in range(5):flow(d,(780,380+j*45),(1110,430+j*25),t+j*.2,CYAN,.3)
  center(d,650,'CLASS SCORES + CORRECT LABELS',24,FG,True)
  center(d,925,'The student learns behavior—not a copy of the teacher’s architecture.',28,MUT)
 elif i==6:
  if t<8:
   p=ease((t-1)/5)
   for j in range(32):
    x0=350+(j%8)*145;y0=310+(j//8)*100
    if j<8:x=lerp(x0,650+(j%4)*145,p);y=lerp(y0,410+(j//4)*100,p);a=1
    else:x=x0;y=y0+200*p;a=1-p
    if a>.01:rect(d,(x,y,x+112,y+65),mix(BG,GREEN,a),mix(BG,GREEN,.12*a),9,2);text(d,x+40,y+10,str(j%2),35,mix(BG,FG,a),True)
   center(d,780,'32 bits → 8 bits',62,GREEN,True)
   center(d,900,'~4× less raw weight storage at the same weight count',28,MUT)
  else:
   rule(d,[(230,520),(1690,520)],CYAN,3)
   for j in range(17):
    x=250+j*90;rule(d,[(x,495),(x,545)],MUT,2)
   for j in range(12):
    xx=300+j*112+math.sin(j)*25;target=250+round((xx-250)/90)*90;p=ease((t-9)/5);x=lerp(xx,target,p)
    dot(d,x,lerp(350+(j%3)*38,520,p),9,GREEN)
   center(d,245,'Calibrate the range. Map values. Round.',43,FG,True)
   center(d,720,'q = round(x / scale) + zero point',42,GREEN)
   center(d,865,'Illustrative levels • actual INT8 representation has 256 values',26,MUT)
 elif i==7:
  p=ease((t-2)/8)
  # Target signal and quantized simulation gradually approach.
  target=[];quant=[]
  for j in range(150):
   x=260+j*9.4;v=math.sin(j*.063)*110+math.sin(j*.12)*35;y=530+v
   target.append((x,y));quant.append((x,530+round((v+(1-p)*50*math.sin(j*.16))/30)*30))
  rule(d,target,LINE,6);rule(d,quant,GREEN,4)
  center(d,270,'FORWARD PASS: SIMULATE ROUNDING',28,GREEN,True)
  arrow(d,(1500,750),(400,750),CYAN,3)
  center(d,795,'TRAINING: ADAPT THE WEIGHTS',28,CYAN,True)
  center(d,925,'Training-time illustration; final deployment quantization follows.',25,MUT)
 elif i==8:
  nodes=[(960,285,'QUANTIZE FIRST'),(450,520,'ACCURACY MISS'),(1470,520,'LATENCY / SIZE MISS'),(450,735,'PROTECT / QAT / DISTILL'),(1470,735,'EXPLORE PRUNING'),(960,930,'MEASURE → CHECK BUDGET')]
  links=[(0,1),(0,2),(1,3),(2,4),(3,5),(4,5)]
  for a,b in links:
   aa=nodes[a];bb=nodes[b];flow(d,(aa[0],aa[1]+35),(bb[0],bb[1]-35),t*.8,CYAN,.3)
  phase=int(t/3)%6
  for j,(x,y,s) in enumerate(nodes):
   col=GREEN if j==phase else CYAN
   rect(d,(x-235,y-38,x+235,y+38),col,(9,25,32),14,2)
   text(d,x,y,s,25,col,True,'mm')
  text(d,90,205,'EXAMPLE BUDGET',22,MUT,True);text(d,90,247,'latency < 0.5 ms',27,FG);text(d,90,289,'accuracy drop < 1 pp',27,FG)
  text(d,1460,205,'EARLY EXIT',22,GREEN,True);text(d,1460,247,'Stop when met.',27,FG)
 elif i==9:
  # Sequential animated measured values; baseline appears first.
  entries=[('SIZE',3.28,.53,'MB',6.2),('LATENCY',1.892,.842,'ms',2.25),('ACCURACY',93.18,90.5,'%',None)]
  for j,(name,b,a,unit,gain) in enumerate(entries):
   y=300+j*210;p=ease((t-1-j*3)/3)
   text(d,180,y,name,24,MUT,True)
   rule(d,[(500,y+30),(1300,y+30)],LINE,23)
   rule(d,[(500,y+73),(500+800*lerp(1,a/b,p),y+73)],GREEN if j<2 else CYAN,23)
   text(d,500,y-30,f'{b:g} → {a:g} {unit}',42,FG,True)
   if gain:text(d,1460,y+5,f'{lerp(1,gain,p):.2f}×',67,GREEN,True)
   else:text(d,1430,y+5,f'−{2.68*p:.2f} pp',53,RED,True)
  center(d,940,'ResNet-56 / CIFAR-10 • Intel i5-11320H • recorded run, not a new benchmark',23,MUT)
 elif i==10:
  z=ease((t-1)/4)
  image_card(im,d,CAT,150,420,190)
  graph(d,t,570,350,640,340,True,GREEN)
  flow(d,(370,515),(530,515),t,CYAN,.8);flow(d,(1250,515),(1460,515),t,GREEN,.8)
  rect(d,(1500,430,1770,600),GREEN,(15,33,27),20,3);text(d,1635,515,'CAT',68,GREEN,True,'mm')
  label(d,150,680,'NEW IMAGE');label(d,640,760,'COMPRESSED ONNX MODEL');label(d,1480,680,'PREDICTION')
  center(d,870,'MODEL + HTML REPORT + JSON RESULTS',29,FG,True)
  center(d,950,'Less storage. Measured speed. Explicit trade-offs.',28,GREEN)
 # Minimal chapter progress, no explanatory slide paragraphs.
 d.rectangle((80,1030,1840,1033),fill=LINE)
 d.rectangle((80,1030,80+1760*clamp(t/duration),1033),fill=GREEN)
 return im

def main():
 total=sum(x[1] for x in SCENES);cursor=0;timeline=[]
 script='\n\n'.join(x[2] for x in SCENES)+'\n'
 (P/'VOICEOVER.txt').write_text(script)
 for i,(title,duration,narration) in enumerate(SCENES):
  timeline.append(dict(scene=i+1,start_seconds=cursor,end_seconds=cursor+duration,title=title,narration=narration));cursor+=duration
 (P/'timeline.json').write_text(json.dumps(timeline,indent=2))
 sheet=Image.new('RGB',(1920,1440),BG)
 for i,(_,dur,_) in enumerate(SCENES):
  im=scene(i,dur*.65,dur);im.save(P/f'frame-{i+1:02}.jpg');sheet.paste(im.resize((640,360)),((i%3)*640,(i//3)*360))
 sheet.save(P/'STORYBOARD.jpg')
 if '--stills' in sys.argv:return
 previous=None
 for i,(_,duration,_) in enumerate(SCENES):
  out=P/f'chapter-{i+1:02}.mp4'
  if not out.exists():
   cmd=['ffmpeg','-y','-loglevel','error','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','-','-an','-c:v','libx264','-preset','ultrafast','-crf','18','-pix_fmt','yuv420p',str(out)]
   proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
   for n in range(duration*FPS):
    t=n/FPS;im=scene(i,t,duration)
    if previous is not None and t<.4:im=Image.blend(previous,im,ease(t/.4))
    proc.stdin.write(im.tobytes())
   proc.stdin.close()
   if proc.wait()!=0:raise RuntimeError('encoding failed')
   print(f'Chapter {i+1}/{len(SCENES)} rendered',flush=True)
  previous=scene(i,duration-1/FPS,duration)
 (P/'chapters.txt').write_text('\n'.join(f"file 'chapter-{i+1:02}.mp4'" for i in range(len(SCENES))))
 subprocess.run(['ffmpeg','-y','-loglevel','error','-f','concat','-safe','0','-i',str(P/'chapters.txt'),'-c','copy','-movflags','+faststart',str(P/'CompressKit-Animated-Visual-Cut.mp4')],check=True)
 print(f'Complete: {total}s, silent visual cut',flush=True)
if __name__=='__main__':main()
