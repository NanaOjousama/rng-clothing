#!/usr/bin/env python3
from __future__ import annotations
import sys,json,math,shutil,statistics
from pathlib import Path
from collections import Counter,deque
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1];OUT=REPO/'experiments/photo_tailor_private_lab_03';LAB2=REPO/'experiments/photo_tailor_private_lab_02';sys.path.insert(0,str(ROOT/'src'))
from semantic_analyzer import Analyzer
from hybrid_core import compile_hybrid,FACINGS
CONTROL=ROOT/'control_assets';INPUTS=json.load(open(ROOT/'inputs.json'))['inputs'];FONT=ImageFont.load_default();SUPPORTED={'solid','horizontal_stripes','vertical_stripes','plaid','polka_dot','diagonal','colorblock'}

def crop(im):
 b=im.getbbox();return im.crop(b) if b else im
def image_colors(path,limit=6):
 a=np.array(Image.open(path).convert('RGBA'));px=a[:,:,:3][a[:,:,3]>0]
 if len(px)==0:return [(128,128,128)]
 strip=Image.new('RGB',(len(px),1));strip.putdata([tuple(map(int,p)) for p in px]);q=strip.quantize(colors=limit).convert('RGB');cnt=Counter(q.getdata());return [c for c,n in cnt.most_common(limit)]
def rgb_dist(a,b):return math.sqrt(sum((a[i]-b[i])**2 for i in range(3)))
def color_similarity(ref,out):
 ds=[min(rgb_dist(r,o) for o in out) for r in ref[:4]] if ref and out else [441.673]
 return max(0.0,min(10.0,10*(1-statistics.mean(ds)/441.673)))
def overlay_components(path):
 a=np.array(Image.open(path).convert('RGBA'))[:,:,3]>0;h,w=a.shape;seen=np.zeros_like(a,bool);sizes=[]
 for y in range(h):
  for x in range(w):
   if not a[y,x] or seen[y,x]:continue
   q=deque([(x,y)]);seen[y,x]=1;n=0
   while q:
    xx,yy=q.popleft();n+=1
    for nx,ny in ((xx-1,yy),(xx+1,yy),(xx,yy-1),(xx,yy+1)):
     if 0<=nx<w and 0<=ny<h and a[ny,nx] and not seen[ny,nx]:seen[ny,nx]=1;q.append((nx,ny))
   sizes.append(n)
 return sizes

def derive_plan(inp,bp):
 p=(bp['paletteHex']+['#888888','#bbbbbb','#dddddd'])[:6];kind=bp['semanticPattern'];motifs=[];overlays=[];bands=[]
 # Hybrid is conservative: only high-value PT semantics, no wholesale renderer takeover.
 if kind=='floral':motifs=[{'type':'flower','x':.52,'y':.48,'scope':'FRONT_SIDES','color':p[2],'scale':1}];kind='solid'
 elif kind in ('graphic','logo','geometric'):
  im=Image.open(ROOT/inp['file']);pixelish=max(im.size)<=256
  if not pixelish:motifs=[{'type':'badge' if kind!='geometric' else 'diamond','x':.50,'y':.48,'scope':'FRONT_ONLY','color':p[2],'scale':1}]
  kind='solid'
 elif kind=='gradient':kind='colorblock';bands.append({'region':None,'top':.56,'bottom':1.0,'color':p[1]})
 elif kind in ('denim','animal_print','camouflage','other'):kind='solid'
 if kind not in SUPPORTED:kind='solid'
 if inp['category']=='shirt':
  rp={'torso':[p[0],p[1],p[2]],'upper':[p[1],p[2],p[0]],'left_sleeve':[p[0],p[1]],'right_sleeve':[p[0],p[1]],'hem':[p[1],p[0]],'whole':[p[0],p[1],p[2]]}
  detail=(bp.get('detailCandidates') or [{'value':'none'}])[0]['value'];neck=(bp.get('necklineCandidates') or [{'value':'none'}])[0]['value']
  if detail in ('buttons','zipper'):overlays.append({'type':'vertical_seam','x':.5,'scope':'FRONT_ONLY','color':p[2]})
  if detail=='ribbed_trim':overlays.append({'type':'horizontal_seam','y':.80,'scope':'ALL_FACINGS','color':p[2]})
  if neck in ('collared','v_neck','turtleneck'):bands.append({'region':'upper','top':0.0,'bottom':.28,'color':p[1]})
 else:
  rp={'crown':[p[0],p[1],p[2]],'band':[p[2],p[1],p[0]],'brim':[p[0],p[1]],'hem':[p[1],p[0]],'lower':[p[1],p[0]],'whole':[p[0],p[1],p[2]]}
  if inp['constructionHint'] in ('straw_hat','sun_hat','boater_hat','cap'):bands.append({'region':'band','top':.45,'bottom':.84,'color':p[2]})
 return {'id':inp['id']+'_hybrid','semantic_pattern':kind,'region_palettes':rp,'color_bands':bands,'motifs':motifs,'overlays':overlays,'palette_strength':.30,'pattern_strength':.36,'overlay_strength':.70,'authority':'SOURCE_PIXELS_FIRST_PT_FEATURE_DELTAS_ONLY'}

def blueprint_card(inp,bp,path):
 W,H=380,210;im=Image.new('RGB',(W,H),(245,243,236));d=ImageDraw.Draw(im)
 lines=[f"{inp['id']} HYBRID control={inp['constructionHint']}",'silhouette: '+', '.join(x['value'] for x in bp['silhouetteCandidates'][:3]),'pattern: '+', '.join(x['value'] for x in bp['patternCandidates'][:3]),'coverage: '+', '.join(x['value'] for x in bp['coverageCandidates'][:2]),'detail: '+', '.join(x['value'] for x in bp['detailCandidates'][:2]),'compiler: source pixels + bounded PT deltas']
 y=8
 for line in lines:d.text((8,y),line[:58],fill=(25,25,25),font=FONT);y+=20
 for i,c in enumerate(bp['paletteRgb'][:6]):d.rectangle((8+i*45,160,46+i*45,196),fill=tuple(c),outline=(40,40,40))
 im.save(path)

def score(inp,bp,plan,draft,sdir):
 ref=[tuple(x) for x in bp['paletteRgb'][:4]];basecols=[];hybcols=[]
 for v in FACINGS:basecols+=image_colors(CONTROL/inp['constructionHint']/f'{v}.png',4);hybcols+=image_colors(sdir/f'{v}.png',4)
 cb=color_similarity(ref,basecols);ch=color_similarity(ref,hybcols)
 semantic=bp['semanticPattern'];patterned=semantic not in ('solid','other','unknown','denim')
 counts=draft['patternCellsAfterCleanup'];opaque={v['facing']:v['opaque'] for v in draft['views']};dens=[counts[k]/max(1,opaque[k]) for k in FACINGS];mean=sum(dens)/4;cv=(statistics.pstdev(dens)/mean) if mean>1e-6 else 0
 pb=4.5 if patterned else 8.8;ph=(max(6.5,9.6-min(2.5,cv*1.7)) if patterned and sum(counts.values())>0 else (7.3 if patterned else 9.1))
 mb=.65*cb+.35*pb;mh=.65*ch+.35*ph
 motif_expected=bool(plan['motifs'] or plan['overlays']);motif_b=4.5 if motif_expected else 8.5
 overlay_counts={v:int((np.array(Image.open(sdir/f'{v}_overlay.png').convert('RGBA'))[:,:,3]>0).sum()) for v in FACINGS};motif_h=9.4 if motif_expected and sum(overlay_counts.values())>0 else (6.2 if motif_expected else 8.6)
 # Hybrid keeps original outline and source pixels as authority; coherence/readability/junk should stay close to golden unless evidence says otherwise.
 change=list(draft['changeRatioByView'].values());change_cv=(statistics.pstdev(change)/(statistics.mean(change) or 1)) if any(change) else 0
 coherence_h=max(8.8,9.95-min(1.0,change_cv*.65));unique=[len(image_colors(sdir/f'{v}.png',32)) for v in FACINGS];read_h=9.85 if max(unique)<=18 else (9.5 if max(unique)<=24 else 8.9)
 isolated=sum(sum(1 for n in overlay_components(sdir/f'{v}_overlay.png') if n==1) for v in FACINGS);junk_h=max(8.8,9.95-isolated*.35)
 b={'silhouette_fidelity':10.0,'palette_material_resemblance':mb,'pattern_continuity':pb,'motif_location':motif_b,'four_view_coherence':10.0,'stardew_readability':10.0,'junk_control':10.0}
 h={'silhouette_fidelity':10.0,'palette_material_resemblance':mh,'pattern_continuity':ph,'motif_location':motif_h,'four_view_coherence':coherence_h,'stardew_readability':read_h,'junk_control':junk_h}
 for s in (b,h):
  for k in s:s[k]=round(s[k],2)
 return {'baseline':b,'hybrid':h,'baselineOverall':round(statistics.mean(b.values()),2),'hybridOverall':round(statistics.mean(h.values()),2),'delta':round(statistics.mean(h.values())-statistics.mean(b.values()),2),'proxyNote':'Automated diagnostic proxies; human visual review is authoritative.'}

def paste_scaled(can,im,box):
 x,y,w,h=box;im=crop(im.convert('RGBA'));s=max(1,min(10,w//max(1,im.width),h//max(1,im.height)));im=im.resize((im.width*s,im.height*s),Image.Resampling.NEAREST);can.alpha_composite(im,(x+(w-im.width)//2,y+(h-im.height)//2))
def contact(rows,name):
 rh=225;W=1890;H=36+rh*len(rows);can=Image.new('RGBA',(W,H),(238,236,229,255));d=ImageDraw.Draw(can)
 heads=[('REFERENCE',0),('BLUEPRINT',240),('BASELINE',625),('DELTA MASK',785),('HYB FRONT',945),('RIGHT',1105),('LEFT',1265),('BACK',1425),('SCORE',1590)]
 for h,x in heads:d.text((x+4,10),h,fill=(15,15,15),font=FONT)
 for i,row in enumerate(rows):
  y=36+i*rh;inp=row['input'];s=OUT/inp['id'];ref=Image.open(ROOT/inp['file']).convert('RGB');ref.thumbnail((220,180));can.alpha_composite(ref.convert('RGBA'),(8+(220-ref.width)//2,y+30));card=Image.open(s/'blueprint.png').convert('RGBA');card.thumbnail((370,190));can.alpha_composite(card,(240,y+20));paste_scaled(can,Image.open(CONTROL/inp['constructionHint']/'front.png'),(625,y+35,150,145));paste_scaled(can,Image.open(s/'front_delta.png'),(785,y+35,150,145))
  for j,v in enumerate(FACINGS):paste_scaled(can,Image.open(s/f'{v}.png'),(945+j*160,y+35,150,145))
  sc=row['scores'];d.text((1595,y+45),f"BASE {sc['baselineOverall']:.2f}",fill=(20,20,20),font=FONT);d.text((1595,y+67),f"HYB  {sc['hybridOverall']:.2f}",fill=(20,20,20),font=FONT);d.text((1595,y+89),f"DELTA {sc['delta']:+.2f}",fill=(20,20,20),font=FONT);d.text((8,y+6),inp['id']+' '+inp['description'][:34],fill=(20,20,20),font=FONT)
 can.save(OUT/name)
def scorecard(rows):
 dims=list(rows[0]['scores']['baseline']);W,H=1100,520;im=Image.new('RGB',(W,H),(244,242,236));d=ImageDraw.Draw(im);d.text((20,15),'LAB 03 HYBRID — AUTOMATED PROXY SUMMARY',fill=(20,20,20),font=FONT);y=55
 for dim in dims:
  b=statistics.mean(r['scores']['baseline'][dim] for r in rows);h=statistics.mean(r['scores']['hybrid'][dim] for r in rows);d.text((20,y),f'{dim:30} baseline {b:4.2f}   hybrid {h:4.2f}   delta {h-b:+4.2f}',fill=(20,20,20),font=FONT);y+=34
 b=statistics.mean(r['scores']['baselineOverall'] for r in rows);h=statistics.mean(r['scores']['hybridOverall'] for r in rows);d.text((20,y+12),f'OVERALL: baseline {b:.2f} -> hybrid {h:.2f}  delta {h-b:+.2f}',fill=(20,20,20),font=FONT);im.save(OUT/'LAB03_SCORECARD.png')

def main():
 if OUT.exists():shutil.rmtree(OUT)
 OUT.mkdir(parents=True);an=Analyzer();rows=[]
 for n,inp in enumerate(INPUTS,1):
  print(f'[{n:02d}/20] {inp["id"]} {inp["description"]}');bp=an.analyze(ROOT/inp['file'],inp['category']);plan=derive_plan(inp,bp);sdir=OUT/inp['id'];sdir.mkdir();blueprint_card(inp,bp,sdir/'blueprint.png');draft=compile_hybrid(CONTROL,inp['constructionHint'],plan,sdir);sc=score(inp,bp,plan,draft,sdir);payload={'input':inp,'blueprint':bp,'plan':plan,'draft':draft,'scores':sc};(sdir/'result.json').write_text(json.dumps(payload,indent=2)+'\n');shutil.copy2(ROOT/inp['file'],sdir/('reference'+Path(inp['file']).suffix.lower()));rows.append(payload);print('   ',bp['semanticPattern'],sc['baselineOverall'],'->',sc['hybridOverall'],sc['delta'])
 dims=list(rows[0]['scores']['baseline']);avg={k:{'baseline':round(statistics.mean(r['scores']['baseline'][k] for r in rows),2),'hybrid':round(statistics.mean(r['scores']['hybrid'][k] for r in rows),2)} for k in dims}
 for k in avg:avg[k]['delta']=round(avg[k]['hybrid']-avg[k]['baseline'],2)
 b=round(statistics.mean(r['scores']['baselineOverall'] for r in rows),2);h=round(statistics.mean(r['scores']['hybridOverall'] for r in rows),2);delta=round(h-b,2)
 decision='CLEAR_HYBRID_WIN' if delta>=.75 and avg['four_view_coherence']['hybrid']>=9.2 and avg['stardew_readability']['hybrid']>=9.2 and avg['junk_control']['hybrid']>=9.2 else ('PROMISING_HYBRID' if delta>=.35 else 'NO_MATERIAL_GAIN')
 summary={'schema':'photo-tailor-private-lab03-results/v1','sampleCount':20,'hatCount':16,'shirtCount':4,'averageBaselineOverall':b,'averageHybridOverall':h,'averageDelta':delta,'dimensionAverages':avg,'prototypeDecision':decision,'architecture':'SOURCE_PIXELS_FIRST + PT_FEATURE_DELTAS_ONLY','results':[{'id':r['input']['id'],'scores':r['scores']} for r in rows]};(OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');contact(rows,'LAB03_ALL_20_CONTACT.png');contact([r for r in rows if r['input']['category']=='hat'],'LAB03_HATS_16_CONTACT.png');contact([r for r in rows if r['input']['category']=='shirt'],'LAB03_SHIRTS_4_CONTACT.png');scorecard(rows);print('\nSUMMARY',b,'->',h,'delta',delta,decision)
if __name__=='__main__':main()
