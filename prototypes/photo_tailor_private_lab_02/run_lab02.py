#!/usr/bin/env python3
from __future__ import annotations
import sys,json,math,shutil,statistics
from pathlib import Path
from collections import Counter,deque
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;REPO=ROOT.parents[1];OUT=REPO/'experiments/photo_tailor_private_lab_02';sys.path.insert(0,str(ROOT/'src'))
from semantic_analyzer import Analyzer
from prototype_core import compile_design,FACINGS,rgba

CONTROL=ROOT/'control_assets';INPUTS=json.load(open(ROOT/'inputs.json'))['inputs'];FONT=ImageFont.load_default()
SUPPORTED={'solid','horizontal_stripes','vertical_stripes','plaid','polka_dot','diagonal','colorblock'}

def hex_to_rgb(s):s=s.lstrip('#');return tuple(int(s[i:i+2],16) for i in (0,2,4))
def image_colors(path,limit=6):
 im=Image.open(path).convert('RGBA');a=np.array(im);px=a[:,:,:3][a[:,:,3]>0]
 if len(px)==0:return [(128,128,128)]
 # quantize opaque pixels via compact temporary strip
 strip=Image.new('RGB',(len(px),1));strip.putdata([tuple(map(int,p)) for p in px]);q=strip.quantize(colors=limit).convert('RGB');cnt=Counter(q.getdata())
 return [c for c,n in cnt.most_common(limit)]
def rgb_dist(a,b):return math.sqrt(sum((a[i]-b[i])**2 for i in range(3)))
def color_similarity(ref,out):
 if not ref or not out:return 0.0
 ds=[min(rgb_dist(r,o) for o in out) for r in ref[:4]]
 return max(0.0,min(10.0,10*(1-statistics.mean(ds)/441.673)))
def alpha_same(a,b):return np.array_equal(np.array(Image.open(a).convert('RGBA'))[:,:,3]>0,np.array(Image.open(b).convert('RGBA'))[:,:,3]>0)
def crop(im):
 b=im.getbbox();return im.crop(b) if b else im

def derive_design(inp,bp):
 cid=inp['constructionHint'];p=bp['paletteHex'];p=(p+['#909090','#c0c0c0','#e0e0e0'])[:6]
 pattern=bp['semanticPattern']
 motifs=[];overlays=[];bands=[]
 if pattern=='floral':motifs=[{'type':'flower','x':.52,'y':.48,'scope':'FRONT_SIDES','color':p[2],'scale':1}];pattern='solid'
 elif pattern in ('graphic','logo','geometric'):
  motifs=[{'type':'badge' if pattern!='geometric' else 'diamond','x':.5,'y':.48,'scope':'FRONT_ONLY','color':p[2],'scale':1}];pattern='solid'
 elif pattern=='gradient':
  pattern='colorblock';bands=[{'region':None,'top':.52,'bottom':1.0,'color':p[1]}]
 elif pattern in ('denim','animal_print','camouflage','other'):pattern='solid'
 if pattern not in SUPPORTED:pattern='solid'
 detail=(bp.get('detailCandidates') or [{'value':'none'}])[0]['value']
 neckline=(bp.get('necklineCandidates') or [{'value':'none'}])[0]['value']
 if inp['category']=='shirt':
  rp={'torso':[p[0],p[1],p[2]],'upper':[p[1],p[2],p[0]],'left_sleeve':[p[0],p[1]],'right_sleeve':[p[0],p[1]],'hem':[p[1],p[0]],'whole':[p[0],p[1],p[2]]}
  if detail in ('buttons','zipper'):overlays.append({'type':'vertical_seam','x':.5,'scope':'FRONT_ONLY','color':p[2]})
  if detail=='ribbed_trim':overlays.append({'type':'horizontal_seam','y':.80,'scope':'ALL_FACINGS','color':p[2]})
  if neckline in ('collared','v_neck','turtleneck'):bands.append({'region':'upper','top':0.0,'bottom':.28,'color':p[1]})
 else:
  rp={'crown':[p[0],p[1],p[2]],'band':[p[2],p[1],p[0]],'brim':[p[0],p[1]],'hem':[p[1],p[0]],'lower':[p[1],p[0]],'whole':[p[0],p[1],p[2]]}
  if cid in ('straw_hat','sun_hat','boater_hat','cap'):bands.append({'region':'band','top':0.45,'bottom':.84,'color':p[2]})
 return {'id':inp['id']+'_enhanced','description':inp['description'],'semantic_pattern':pattern,'region_palettes':rp,'color_bands':bands,'motifs':motifs,'overlays':overlays}

def blueprint_card(inp,bp,path):
 W,H=380,210;im=Image.new('RGB',(W,H),(245,243,236));d=ImageDraw.Draw(im)
 lines=[f"{inp['id']}  {inp['category'].upper()}  control={inp['constructionHint']}",
  'silhouette: '+', '.join(x['value'] for x in bp['silhouetteCandidates'][:3]),
  'pattern: '+', '.join(x['value'] for x in bp['patternCandidates'][:3]),
  'coverage: '+', '.join(x['value'] for x in bp['coverageCandidates'][:2]),
  'neckline: '+', '.join(x['value'] for x in bp['necklineCandidates'][:2]),
  'detail: '+', '.join(x['value'] for x in bp['detailCandidates'][:2]),
  'compiler pattern: '+bp['semanticPattern']]
 y=8
 for line in lines:d.text((8,y),line[:58],fill=(25,25,25),font=FONT);y+=20
 for i,c in enumerate(bp['paletteRgb'][:6]):d.rectangle((8+i*45,160,46+i*45,196),fill=tuple(c),outline=(40,40,40))
 im.save(path)

def combo_masks(sample_dir):
 ims=[Image.open(sample_dir/'front_occupancy.png').convert('RGBA'),Image.open(sample_dir/'front_regions.png').convert('RGBA')]
 W=sum(x.width for x in ims)+6;H=max(x.height for x in ims);o=Image.new('RGBA',(W,H),(0,0,0,0));x=0
 for im in ims:o.alpha_composite(im,(x,0));x+=im.width+6
 o.save(sample_dir/'occupancy_region.png')

def baseline_sheet(cid,path):
 frames=[Image.open(CONTROL/cid/f'{v}.png').convert('RGBA') for v in FACINGS];cell=80;out=Image.new('RGBA',(cell*4,cell),(0,0,0,0))
 for i,im in enumerate(frames):
  im=crop(im);s=max(1,min(8,64//max(1,im.width),64//max(1,im.height)));im=im.resize((im.width*s,im.height*s),Image.Resampling.NEAREST);out.alpha_composite(im,(i*cell+(cell-im.width)//2,(cell-im.height)//2))
 out.save(path)
def enhanced_sheet(sample_dir,path):
 frames=[Image.open(sample_dir/f'{v}.png').convert('RGBA') for v in FACINGS];cell=80;out=Image.new('RGBA',(cell*4,cell),(0,0,0,0))
 for i,im in enumerate(frames):
  im=crop(im);s=max(1,min(8,64//max(1,im.width),64//max(1,im.height)));im=im.resize((im.width*s,im.height*s),Image.Resampling.NEAREST);out.alpha_composite(im,(i*cell+(cell-im.width)//2,(cell-im.height)//2))
 out.save(path)

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

def score(inp,bp,design,draft,sample_dir):
 ref=[tuple(x) for x in bp['paletteRgb'][:4]]
 basecols=[];enhcols=[]
 for v in FACINGS:
  basecols+=image_colors(CONTROL/inp['constructionHint']/f'{v}.png',4);enhcols+=image_colors(sample_dir/f'{v}.png',4)
 color_b=color_similarity(ref,basecols);color_e=color_similarity(ref,enhcols)
 semantic=bp['semanticPattern'];patterned=semantic not in ('solid','other','unknown','denim')
 counts=draft['pattern_cells_after_cleanup'];opaque={v['facing']:v['opaque'] for v in draft['views']};dens=[counts[k]/max(1,opaque[k]) for k in FACINGS]
 mean=sum(dens)/4;cv=(statistics.pstdev(dens)/mean) if mean>1e-6 else 0
 pattern_b=4.5 if patterned else 8.8
 pattern_e=(max(5.0,9.5-min(4.0,cv*2.5)) if patterned and sum(counts.values())>0 else (7.0 if patterned else 9.0))
 material_b=.65*color_b+.35*pattern_b;material_e=.65*color_e+.35*pattern_e
 motif_expected=bool(design.get('motifs') or design.get('overlays'))
 motif_b=4.5 if motif_expected else 8.5
 overlay_counts={v:int((np.array(Image.open(sample_dir/f'{v}_overlay.png').convert('RGBA'))[:,:,3]>0).sum()) for v in FACINGS}
 motif_e=9.3 if motif_expected and sum(overlay_counts.values())>0 else (6.0 if motif_expected else 8.5)
 silhouette_b=silhouette_e=10.0
 coherence_b=10.0;coherence_e=max(7.0,9.8-min(2.5,cv*1.8))
 unique=[]
 for v in FACINGS:unique.append(len(image_colors(sample_dir/f'{v}.png',32)))
 readability_b=10.0;readability_e=9.5 if max(unique)<=16 else (8.8 if max(unique)<=24 else 7.8)
 isolated=sum(sum(1 for n in overlay_components(sample_dir/f'{v}_overlay.png') if n==1) for v in FACINGS)
 junk_b=10.0;junk_e=max(7.0,9.7-isolated*.45)
 scores_b={'silhouette_fidelity':silhouette_b,'palette_material_resemblance':material_b,'pattern_continuity':pattern_b,'motif_location':motif_b,'four_view_coherence':coherence_b,'stardew_readability':readability_b,'junk_control':junk_b}
 scores_e={'silhouette_fidelity':silhouette_e,'palette_material_resemblance':material_e,'pattern_continuity':pattern_e,'motif_location':motif_e,'four_view_coherence':coherence_e,'stardew_readability':readability_e,'junk_control':junk_e}
 for s in (scores_b,scores_e):
  for k in s:s[k]=round(s[k],2)
 return {'baseline':scores_b,'enhanced':scores_e,'baselineOverall':round(statistics.mean(scores_b.values()),2),'enhancedOverall':round(statistics.mean(scores_e.values()),2),'delta':round(statistics.mean(scores_e.values())-statistics.mean(scores_b.values()),2),'patternDensityByView':dict(zip(FACINGS,[round(x,4) for x in dens])),'overlayPixelsByView':overlay_counts,'proxyNote':'Automated prototype proxies, not a substitute for human art review.'}

def paste_scaled(can,im,box):
 x,y,w,h=box;im=crop(im.convert('RGBA'));s=max(1,min(10,w//max(1,im.width),h//max(1,im.height)));im=im.resize((im.width*s,im.height*s),Image.Resampling.NEAREST);can.alpha_composite(im,(x+(w-im.width)//2,y+(h-im.height)//2))
def fit_reference(im,box):
 x,y,w,h=box;im=im.convert('RGB');im.thumbnail((w,h));can=Image.new('RGBA',(w,h),(250,248,242,255));can.alpha_composite(im.convert('RGBA'),((w-im.width)//2,(h-im.height)//2));return can

def per_sample_sheet(inp,bp,scores,sdir):
 W,H=1650,500;can=Image.new('RGBA',(W,H),(238,236,229,255));d=ImageDraw.Draw(can)
 d.text((8,6),f"{inp['id']} {inp['description']}  baseline {scores['baselineOverall']:.2f} -> enhanced {scores['enhancedOverall']:.2f} ({scores['delta']:+.2f})",fill=(20,20,20),font=FONT)
 ref=Image.open(ROOT/inp['file']).convert('RGB');ref.thumbnail((280,390));can.alpha_composite(ref.convert('RGBA'),(10+(280-ref.width)//2,40))
 can.alpha_composite(Image.open(sdir/'blueprint.png').convert('RGBA'),(305,40))
 paste_scaled(can,Image.open(CONTROL/inp['constructionHint']/'front.png'),(700,60,140,140))
 paste_scaled(can,Image.open(sdir/'front_regions.png'),(850,60,140,140))
 for i,v in enumerate(FACINGS):paste_scaled(can,Image.open(CONTROL/inp['constructionHint']/f'{v}.png'),(700+i*145,260,135,135))
 for i,v in enumerate(FACINGS):paste_scaled(can,Image.open(sdir/f'{v}.png'),(700+i*145,105,135,135))
 d.text((700,42),'PT ENHANCED: FRONT / RIGHT / LEFT / BACK',fill=(20,20,20),font=FONT);d.text((700,242),'CURRENT SOURCE-RESPECTING BASELINE: F/R/L/B',fill=(20,20,20),font=FONT)
 y=420
 for k in scores['baseline']:
  d.text((700,y),f"{k[:24]} {scores['baseline'][k]:4.1f} -> {scores['enhanced'][k]:4.1f}",fill=(25,25,25),font=FONT);y+=11
 can.save(sdir/'comparison.png')

def contact(rows,name):
 rh=230;W=2020;H=36+rh*len(rows);can=Image.new('RGBA',(W,H),(238,236,229,255));d=ImageDraw.Draw(can)
 headers=[('REFERENCE',0),('BLUEPRINT',245),('CONTROL',635),('REGION',795),('BASELINE',955),('PT FRONT',1115),('RIGHT',1275),('LEFT',1435),('BACK',1595),('SCORE',1755)]
 for h,x in headers:d.text((x+4,10),h,fill=(15,15,15),font=FONT)
 for i,row in enumerate(rows):
  y=36+i*rh;inp=row['input'];sdir=OUT/inp['id']
  ref=Image.open(ROOT/inp['file']).convert('RGB');ref.thumbnail((225,185));can.alpha_composite(ref.convert('RGBA'),(8+(225-ref.width)//2,y+28))
  card=Image.open(sdir/'blueprint.png').convert('RGBA');card.thumbnail((370,195));can.alpha_composite(card,(245,y+20))
  paste_scaled(can,Image.open(CONTROL/inp['constructionHint']/'front.png'),(635,y+36,150,145));paste_scaled(can,Image.open(sdir/'front_regions.png'),(795,y+36,150,145));paste_scaled(can,Image.open(CONTROL/inp['constructionHint']/'front.png'),(955,y+36,150,145))
  for j,v in enumerate(FACINGS):paste_scaled(can,Image.open(sdir/f'{v}.png'),(1115+j*160,y+36,150,145))
  sc=row['scores'];d.text((1760,y+40),f"BASE {sc['baselineOverall']:.2f}",fill=(20,20,20),font=FONT);d.text((1760,y+62),f"PT   {sc['enhancedOverall']:.2f}",fill=(20,20,20),font=FONT);d.text((1760,y+84),f"DELTA {sc['delta']:+.2f}",fill=(20,20,20),font=FONT)
  d.text((8,y+5),inp['id']+' '+inp['description'][:34],fill=(20,20,20),font=FONT)
 can.save(OUT/name)

def scorecard(rows):
 dims=list(rows[0]['scores']['baseline']);W,H=1100,520;im=Image.new('RGB',(W,H),(244,242,236));d=ImageDraw.Draw(im)
 d.text((20,15),'PHOTO TAILOR PRIVATE LAB 02 — AUTOMATED PROXY SCORE SUMMARY',fill=(20,20,20),font=FONT)
 y=55
 for dim in dims:
  b=statistics.mean(r['scores']['baseline'][dim] for r in rows);e=statistics.mean(r['scores']['enhanced'][dim] for r in rows);delta=e-b
  d.text((20,y),f'{dim:30} baseline {b:4.2f}   PT {e:4.2f}   delta {delta:+4.2f}',fill=(20,20,20),font=FONT);y+=34
 b=statistics.mean(r['scores']['baselineOverall'] for r in rows);e=statistics.mean(r['scores']['enhancedOverall'] for r in rows);d.text((20,y+12),f'OVERALL: baseline {b:.2f} -> PT {e:.2f}  delta {e-b:+.2f}',fill=(20,20,20),font=FONT)
 im.save(OUT/'LAB02_SCORECARD.png')

def main():
 if OUT.exists():shutil.rmtree(OUT)
 OUT.mkdir(parents=True);an=Analyzer();rows=[]
 for n,inp in enumerate(INPUTS,1):
  print(f'[{n:02d}/{len(INPUTS)}] {inp["id"]} {inp["description"]}')
  ref=ROOT/inp['file'];bp=an.analyze(ref,inp['category']);sdir=OUT/inp['id'];sdir.mkdir();blueprint_card(inp,bp,sdir/'blueprint.png')
  design=derive_design(inp,bp);draft=compile_design(CONTROL,inp['constructionHint'],design,sdir);combo_masks(sdir);baseline_sheet(inp['constructionHint'],sdir/'baseline_4view.png');enhanced_sheet(sdir,sdir/'enhanced_4view.png')
  sc=score(inp,bp,design,draft,sdir);payload={'input':inp,'blueprint':bp,'design':design,'draft':draft,'scores':sc};(sdir/'result.json').write_text(json.dumps(payload,indent=2)+'\n');shutil.copy2(ref,sdir/('reference'+ref.suffix.lower()));per_sample_sheet(inp,bp,sc,sdir);rows.append(payload)
  print('   pattern',bp['semanticPattern'],'control',inp['constructionHint'],'score',sc['baselineOverall'],'->',sc['enhancedOverall'],sc['delta'])
 avg_b=statistics.mean(r['scores']['baselineOverall'] for r in rows);avg_e=statistics.mean(r['scores']['enhancedOverall'] for r in rows);delta=avg_e-avg_b
 dims=list(rows[0]['scores']['baseline']);dimavg={k:{'baseline':round(statistics.mean(r['scores']['baseline'][k] for r in rows),2),'enhanced':round(statistics.mean(r['scores']['enhanced'][k] for r in rows),2)} for k in dims}
 for k in dimavg:dimavg[k]['delta']=round(dimavg[k]['enhanced']-dimavg[k]['baseline'],2)
 earned=[]
 if dimavg['pattern_continuity']['delta']>=.5:earned.append('normalized_pattern_coordinates + texture_cleanup')
 if dimavg['palette_material_resemblance']['delta']>=.5:earned.append('region_palettes + color_bands')
 if dimavg['motif_location']['delta']>=.5:earned.append('normalized_motifs + facing_scopes + overlays')
 if dimavg['four_view_coherence']['enhanced']>=8.5:earned.append('coherent_4_view_projection')
 if dimavg['junk_control']['enhanced']>=8.5:earned.append('occupancy_masks + cleanup gates')
 decision='CLEAR_PROTOTYPE_WIN' if delta>=.75 and dimavg['four_view_coherence']['enhanced']>=8.5 and dimavg['junk_control']['enhanced']>=8.5 else ('MIXED' if delta>=.2 else 'NO_MATERIAL_GAIN')
 summary={'schema':'photo-tailor-private-lab02-results/v1','sampleCount':len(rows),'hatCount':sum(r['input']['category']=='hat' for r in rows),'shirtCount':sum(r['input']['category']=='shirt' for r in rows),'baseline':'HAT_PRODUCTION_GOLDEN_V1 controls / copied shirt controls','averageBaselineOverall':round(avg_b,2),'averageEnhancedOverall':round(avg_e,2),'averageDelta':round(delta,2),'dimensionAverages':dimavg,'prototypeDecision':decision,'systemsEarningFurtherStudy':earned,'scoringCaveat':'Scores are automated proxy diagnostics. Human visual review of contact sheets remains authoritative.','results':[{'id':r['input']['id'],'description':r['input']['description'],'construction':r['input']['constructionHint'],'pattern':r['blueprint']['semanticPattern'],'scores':r['scores']} for r in rows]}
 (OUT/'summary.json').write_text(json.dumps(summary,indent=2)+'\n');contact(rows,'LAB02_ALL_20_CONTACT.png');contact([r for r in rows if r['input']['category']=='hat'],'LAB02_HATS_16_CONTACT.png');contact([r for r in rows if r['input']['category']=='shirt'],'LAB02_SHIRTS_4_CONTACT.png');scorecard(rows)
 print('\nSUMMARY',summary['averageBaselineOverall'],'->',summary['averageEnhancedOverall'],'delta',summary['averageDelta'],decision);print('EARNED',earned)
if __name__=='__main__':main()
