#!/usr/bin/env python3
from pathlib import Path
import json
from PIL import Image,ImageDraw,ImageFont
REPO=Path(__file__).resolve().parents[2]
L2=REPO/'experiments/photo_tailor_private_lab_02'
L3=REPO/'experiments/photo_tailor_private_lab_03'
P2=REPO/'prototypes/photo_tailor_private_lab_02'
OUT=REPO/'experiments/photo_tailor_final_comparison'
FONT=ImageFont.load_default()
V=('front','right','left','back')

def crop(im):
    b=im.getbbox()
    return im.crop(b) if b else im

def paste(can,im,box):
    x,y,w,h=box
    im=crop(im.convert('RGBA'))
    s=max(1,min(10,w//max(1,im.width),h//max(1,im.height)))
    im=im.resize((im.width*s,im.height*s),Image.Resampling.NEAREST)
    can.alpha_composite(im,(x+(w-im.width)//2,y+(h-im.height)//2))

def strip(paths,w=320,h=80):
    out=Image.new('RGBA',(w,h),(0,0,0,0))
    cw=w//4
    for i,p in enumerate(paths):
        paste(out,Image.open(p),(i*cw,0,cw,h))
    return out

def main():
    OUT.mkdir(parents=True,exist_ok=True)
    inputs=json.load(open(P2/'inputs.json'))['inputs']
    s2=json.load(open(L2/'summary.json'))
    s3=json.load(open(L3/'summary.json'))
    rows=[]
    for inp in inputs:
        rid=inp['id']
        r2=json.load(open(L2/rid/'result.json'))
        r3=json.load(open(L3/rid/'result.json'))
        rows.append({'input':inp,'lab2':r2,'lab3':r3})

    rh=210; W=1840; H=36+rh*len(rows)
    can=Image.new('RGBA',(W,H),(239,237,231,255))
    d=ImageDraw.Draw(can)
    heads=[('REFERENCE',0),('A GOLDEN',235),('B FULL PT',420),('C HYBRID',605),
           ('B 4-VIEW',790),('C 4-VIEW',1120),('A/B/C SCORE',1450)]
    for h,x in heads:
        d.text((x+4,10),h,fill=(15,15,15),font=FONT)
    for i,row in enumerate(rows):
        y=36+i*rh
        inp=row['input']; rid=inp['id']
        ref=Image.open(P2/inp['file']).convert('RGB')
        ref.thumbnail((215,165))
        can.alpha_composite(ref.convert('RGBA'),(8+(215-ref.width)//2,y+28))
        cid=inp['constructionHint']
        paste(can,Image.open(P2/'control_assets'/cid/'front.png'),(235,y+35,170,140))
        paste(can,Image.open(L2/rid/'front.png'),(420,y+35,170,140))
        paste(can,Image.open(L3/rid/'front.png'),(605,y+35,170,140))
        can.alpha_composite(strip([L2/rid/f'{v}.png' for v in V],310,135),(790,y+36))
        can.alpha_composite(strip([L3/rid/f'{v}.png' for v in V],310,135),(1120,y+36))
        b=row['lab2']['scores']; c=row['lab3']['scores']
        d.text((1455,y+40),f"A {b['baselineOverall']:.2f}",fill=(20,20,20),font=FONT)
        d.text((1455,y+62),f"B {b['enhancedOverall']:.2f}",fill=(20,20,20),font=FONT)
        d.text((1455,y+84),f"C {c['hybridOverall']:.2f}",fill=(20,20,20),font=FONT)
        d.text((1455,y+112),f"B-A {b['delta']:+.2f}",fill=(20,20,20),font=FONT)
        d.text((1455,y+134),f"C-A {c['delta']:+.2f}",fill=(20,20,20),font=FONT)
        d.text((8,y+6),rid+' '+inp['description'][:32],fill=(20,20,20),font=FONT)
    can.save(OUT/'FINAL_A_B_C_20_REFERENCE_CONTACT.png')
    dims=list(s2['dimensionAverages'])
    sc=Image.new('RGB',(1300,600),(245,243,237))
    sd=ImageDraw.Draw(sc)
    sd.text((20,15),'FINAL A/B/C: A GOLDEN vs B FULL PT LAB02 vs C HYBRID LAB03',fill=(15,15,15),font=FONT)
    y=60
    score_table={}
    for dim in dims:
        a=s2['dimensionAverages'][dim]['baseline']
        b=s2['dimensionAverages'][dim]['enhanced']
        c=s3['dimensionAverages'][dim]['hybrid']
        score_table[dim]={'A_golden':a,'B_full_pt':b,'C_hybrid':c,'C_minus_B':round(c-b,2)}
        sd.text((20,y),f'{dim:30} A {a:4.2f}   B {b:4.2f}   C {c:4.2f}   C-B {c-b:+4.2f}',fill=(20,20,20),font=FONT)
        y+=38
    sd.text((20,y+15),f"OVERALL proxy: A {s2['averageBaselineOverall']:.2f}   B {s2['averageEnhancedOverall']:.2f}   C {s3['averageHybridOverall']:.2f}   C-B {s3['averageHybridOverall']-s2['averageEnhancedOverall']:+.2f}",fill=(20,20,20),font=FONT)
    sd.text((20,y+55),'Proxy scores are diagnostics; human contact-sheet review is authoritative.',fill=(60,60,60),font=FONT)
    sc.save(OUT/'FINAL_A_B_C_SCORECARD.png')
    final={
      'schema':'photo-tailor-final-comparison/v1',
      'sameReferenceBenchmark':{
        'sampleCount':20,
        'A':'Golden/current copied source-respecting control',
        'B':'Lab02 full Photo Tailor-style compiler',
        'C':'Lab03 hybrid source-pixels-first + PT feature deltas',
        'overall':{
          'A':s2['averageBaselineOverall'],
          'B':s2['averageEnhancedOverall'],
          'C':s3['averageHybridOverall'],
          'C_minus_B':round(s3['averageHybridOverall']-s2['averageEnhancedOverall'],2)},
        'dimensions':score_table},
      'threeLabHistory':{
        'Lab01':{'role':'Capability proof','samples':8,'same20ReferenceBenchmark':False},
        'Lab02':{'role':'Full end-to-end PT compiler','samples':20,'decision':s2['prototypeDecision'],'deltaVsGolden':s2['averageDelta']},
        'Lab03':{'role':'Hybrid source-respecting + PT deltas','samples':20,'decision':s3['prototypeDecision'],'deltaVsGolden':s3['averageDelta'],'deltaVsLab02':round(s3['averageHybridOverall']-s2['averageEnhancedOverall'],2)}},
      'interpretation':'Lab03 is strongest overall proxy and recovers most cleanliness/coherence while retaining PT pattern/palette/motif gains. Lab01 is architectural only because it did not use the same 20 references.',
      'humanReviewRequired':True}
    (OUT/'FINAL_COMPARISON.json').write_text(json.dumps(final,indent=2)+'\n')
    md=f"""# Final Photo Tailor Prototype Comparison

## Apples-to-apples 20-reference benchmark
- **A — Golden/current:** {s2['averageBaselineOverall']:.2f}
- **B — Full PT Lab 02:** {s2['averageEnhancedOverall']:.2f} ({s2['averageDelta']:+.2f} vs A)
- **C — Hybrid Lab 03:** {s3['averageHybridOverall']:.2f} ({s3['averageDelta']:+.2f} vs A; {s3['averageHybridOverall']-s2['averageEnhancedOverall']:+.2f} vs B)

Lab 03 has the strongest proxy overall. It keeps source pixels authoritative and uses PT only for bounded pattern, region-palette/color-band, motif/facing-scope, overlay and occupancy-cleanup deltas.

## Three-lab history
- **Lab 01:** 8-design capability proof. Not the same 20-reference set, so no fake numeric comparison.
- **Lab 02:** full reference-driven PT compiler; stronger semantics but small cleanliness losses.
- **Lab 03:** hybrid; retains PT gains while recovering most cleanliness losses.

Human review of FINAL_A_B_C_20_REFERENCE_CONTACT.png remains the final art-quality decision.
"""
    (OUT/'FINAL_COMPARISON.md').write_text(md)
    print('FINAL A/B/C',s2['averageBaselineOverall'],s2['averageEnhancedOverall'],s3['averageHybridOverall'],'C-B',round(s3['averageHybridOverall']-s2['averageEnhancedOverall'],2))

if __name__=='__main__':
    main()
