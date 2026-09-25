#!/usr/bin/env python3
from pathlib import Path
import sys, json, hashlib
from PIL import Image, ImageDraw

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from v5.source_backed import read_fs_json, fs_views

OUT=ROOT/'experiments/cap_source_corpus_audit_01'
OUT.mkdir(parents=True,exist_ok=True)

VIEWS=('front','right','left','back')

CANDS=[
 {'id':'MAS_CAP2','label':'Cap 2','pack':'More Accessories / plurffle','kind':'Baseball','path':ROOT/'generator content/[FS] More Accessories and Stuff Pack/Hats/Cap2/hat.png','json':ROOT/'generator content/[FS] More Accessories and Stuff Pack/Hats/Cap2/hat.json','usage':'DIRECT BASE','note':'live-approved; Cap1 has the exact same alpha silhouette'},
 {'id':'MAS_SNAP','label':'Cap Snapback','pack':'More Accessories / plurffle','kind':'Snapback','path':ROOT/'generator content/[FS] More Accessories and Stuff Pack/Hats/CapSnapback/hat.png','json':ROOT/'generator content/[FS] More Accessories and Stuff Pack/Hats/CapSnapback/hat.json','usage':'DIRECT / PARTIAL','note':'live-approved source'},
 {'id':'RAGNAROK_BOYS','label':'Boys Cap','pack':'Ragnarok Online Hats / Seyph','kind':'Soft baseball / boys cap','path':Path('/home/deck/Downloads/[CP] Ragnarok Online Hats/assets/0_BoysCap.png'),'json':None,'usage':'PARTIAL DONOR','note':'4-view source/reference'},
 {'id':'JED_BACK','label':'Backwards Cap','pack':'Jedone Casual Hat Pack','kind':'Backwards baseball','path':Path("/home/deck/Downloads/[FS] Jedone's Casual Hat Pack/Hats/Backwards Cap/Backwards_Cap_01/hat.png"),'json':Path("/home/deck/Downloads/[FS] Jedone's Casual Hat Pack/Hats/Backwards Cap/Backwards_Cap_01/hat.json"),'usage':'PARTIAL DONOR','note':'5 style variants, identical alpha'},
 {'id':'JED_VINTAGE','label':'Vintage Cap','pack':'Jedone Casual Hat Pack','kind':'Low / vintage cap','path':Path("/home/deck/Downloads/[FS] Jedone's Casual Hat Pack/Hats/Vintage Cap/Vintage Cap_01/hat.png"),'json':Path("/home/deck/Downloads/[FS] Jedone's Casual Hat Pack/Hats/Vintage Cap/Vintage Cap_01/hat.json"),'usage':'DIRECT / PARTIAL','note':'3 style variants, identical alpha'},
 {'id':'JED_HEADPHONES','label':'Cap & Headphones','pack':'Jedone Casual Hat Pack','kind':'Structured cap','path':Path("/home/deck/Downloads/[FS] Jedone's Casual Hat Pack/Hats/Cap&Headphones/Cap&Headphones_01/hat.png"),'json':Path("/home/deck/Downloads/[FS] Jedone's Casual Hat Pack/Hats/Cap&Headphones/Cap&Headphones_01/hat.json"),'usage':'PARTIAL DONOR','note':'8 variants; cap shape + headphone attachment'},
 {'id':'JED_OFFICER','label':'Officer Cap','pack':'Jedone Casual Hat Pack','kind':'Officer / peaked','path':Path("/home/deck/Downloads/[FS] Jedone's Casual Hat Pack/Hats/Officer Cap/hat.png"),'json':Path("/home/deck/Downloads/[FS] Jedone's Casual Hat Pack/Hats/Officer Cap/hat.json"),'usage':'REFERENCE ONLY','note':'peaked brim/crown reference'},
 {'id':'MAS_PAPERBOY','label':'Paperboy Hat','pack':'More Accessories / plurffle','kind':'Paperboy / newsboy','path':ROOT/'generator content/[FS] More Accessories and Stuff Pack/Hats/PaperboyHat/hat.png','json':ROOT/'generator content/[FS] More Accessories and Stuff Pack/Hats/PaperboyHat/hat.json','usage':'REFERENCE ONLY','note':'previously failed live identity'},
 {'id':'MAID_CAP','label':'Maid Cap','pack':'Butlers & Maids','kind':'Maid / service cap','path':Path('/home/deck/Downloads/[FS] Butlers & Maids/Hats/Maid/Maid Cap/hat.png'),'json':Path('/home/deck/Downloads/[FS] Butlers & Maids/Hats/Maid/Maid Cap/hat.json'),'usage':'REFERENCE ONLY','note':'off-type cap; included for corpus completeness'},
 {'id':'OLD_DAD1','label':'Dad Cap V1','pack':'Project prior experiment','kind':'Dad cap','frames_dir':ROOT/'experiments/dad_cap/production_20x20','usage':'DIRECT CANDIDATE','note':'prior accepted front + tuned side/back'},
 {'id':'OLD_DAD2','label':'Dad Cap V2','pack':'Project prior experiment','kind':'Dad cap variant','frames_dir':ROOT/'experiments/dad_cap_v2/production_20x20','usage':'DIRECT CANDIDATE','note':'alternate prior experiment'},
 {'id':'OLD_TRUCKER','label':'Trucker old','pack':'Project prior experiment','kind':'Trucker','path':ROOT/'experiments/trucker_cap/source_16.png','json':None,'usage':'PARTIAL / REFERENCE','note':'old front source only'},
 {'id':'TRUCKER_REF','label':'Trucker ref','pack':'Downloads reference','kind':'Trucker front reference','path':Path('/home/deck/Downloads/front_view_trucker_h...-1938391056-0.png'),'json':None,'usage':'REFERENCE ONLY','note':'front-only 16px reference'},
]

def mirror(im): return im.transpose(Image.Transpose.FLIP_LEFT_RIGHT)

def blank(sz=(20,20)):
    return Image.new('RGBA',sz,(0,0,0,0))

def extract_fs(c):
    p=Path(c['path'])
    im=Image.open(p).convert('RGBA')
    if c.get('json') and Path(c['json']).exists():
        try:
            data=read_fs_json(str(c['json']))
            # common 20x80 explicit 4-view
            model_of={'front':'FrontHat','right':'RightHat','left':'LeftHat','back':'BackHat'}
            out={}
            for v,key in model_of.items():
                m=data.get(key)
                if not m: continue
                size=m.get('HatSize') or {'Width':20,'Length':20}
                w,h=int(size.get('Width',20)),int(size.get('Length',20))
                pos=m.get('StartingPosition') or {'X':0,'Y':0}
                x,y=int(pos.get('X',0)),int(pos.get('Y',0))
                fr=im.crop((x,y,x+w,y+h))
                if m.get('Flipped'): fr=mirror(fr)
                out[v]=fr
            # older FS packs may define only front/right/back and left as Flipped
            if out: 
                if 'left' not in out and 'right' in out: out['left']=mirror(out['right'])
                return out
        except Exception:
            pass
    # layout fallback
    if im.width==20 and im.height==80:
        return {v:im.crop((0,i*20,20,(i+1)*20)) for i,v in enumerate(VIEWS)}
    if im.width==20 and im.height==60:
        # More Accessories convention: front,right,back; left mirrors right
        fr=[im.crop((0,i*20,20,(i+1)*20)) for i in range(3)]
        return {'front':fr[0],'right':fr[1],'left':mirror(fr[1]),'back':fr[2]}
    # front only
    return {'front':im}

def extract(c):
    if c.get('frames_dir'):
        d=Path(c['frames_dir'])
        names={'front':'front_20.png','right':'right_20.png','left':'left_20.png','back':'back_20.png'}
        return {v:Image.open(d/n).convert('RGBA') for v,n in names.items() if (d/n).exists()}
    return extract_fs(c)

def bbox(fr):
    a=fr.getchannel('A')
    return a.getbbox()

# add shape metrics and quality scores (construction-only, not palette)
# Scores are audit judgments after existing live-QC evidence + silhouette completeness:
# 3 strong, 2 usable, 1 weak/missing.
scores={
 'MAS_CAP2':(3,3,3),'MAS_SNAP':(3,3,3),'RAGNAROK_BOYS':(3,3,3),
 'JED_BACK':(2,3,3),'JED_VINTAGE':(3,3,3),'JED_HEADPHONES':(2,2,2),
 'JED_OFFICER':(3,3,3),'MAS_PAPERBOY':(1,2,2),'MAID_CAP':(2,2,2),
 'OLD_DAD1':(3,3,3),'OLD_DAD2':(3,3,3),'OLD_TRUCKER':(2,0,0),'TRUCKER_REF':(2,0,0)
}
for c in CANDS:
    c['frames']=extract(c)
    c['quality']={'front':scores[c['id']][0],'side':scores[c['id']][1],'back':scores[c['id']][2]}
    c['bboxes']={v:bbox(fr) for v,fr in c['frames'].items()}

# audit JSON
serial=[]
for c in CANDS:
    serial.append({k:v for k,v in c.items() if k!='frames' and not isinstance(v,Path)})
    serial[-1]['path']=str(c.get('path',''))
    serial[-1]['json']=str(c.get('json','')) if c.get('json') else None
    serial[-1]['frames_dir']=str(c.get('frames_dir','')) if c.get('frames_dir') else None
(OUT/'cap_source_audit.json').write_text(json.dumps(serial,indent=2)+'\n')

# contact sheet
scale=10; tile=20*scale; gap=12; labelw=420; rowh=tile+48
W=labelw+4*(tile+gap)+30
H=70+len(CANDS)*rowh
sheet=Image.new('RGB',(W,H),'white'); dr=ImageDraw.Draw(sheet)
dr.text((10,8),'CAP SOURCE CORPUS AUDIT — unique construction candidates',fill='black')
dr.text((10,28),'Quality: F/S/B = 3 strong, 2 usable, 1 weak, 0 missing',fill='black')
for i,v in enumerate(('FRONT','RIGHT','LEFT','BACK')):
    dr.text((labelw+i*(tile+gap)+78,48),v,fill='black')
y=70
for c in CANDS:
    q=c['quality']
    dr.text((10,y+8),f"{c['label']}  [{c['kind']}]",fill='black')
    dr.text((10,y+30),c['pack'][:55],fill='black')
    dr.text((10,y+52),f"F/S/B {q['front']}/{q['side']}/{q['back']}   {c['usage']}",fill='black')
    dr.text((10,y+74),c['note'][:65],fill='black')
    for i,v in enumerate(VIEWS):
        fr=c['frames'].get(v)
        if fr is None: continue
        # center any non-20 frame onto 20x20 for fair scale without resizing
        canvas=blank()
        if fr.size==(20,20): canvas=fr
        else:
            fw,fh=fr.size
            if fw<=20 and fh<=20:
                canvas.alpha_composite(fr,((20-fw)//2,(20-fh)//2))
            else:
                tmp=fr.copy(); tmp.thumbnail((20,20),Image.Resampling.NEAREST)
                canvas.alpha_composite(tmp,((20-tmp.width)//2,(20-tmp.height)//2))
        big=canvas.resize((tile,tile),Image.Resampling.NEAREST)
        sheet.paste(big,(labelw+i*(tile+gap),y),big)
    y+=rowh
sheet.save(OUT/'CAP_SOURCE_AUDIT_CONTACT_X10.png')
chat=sheet.copy(); chat.thumbnail((1550,1900),Image.Resampling.LANCZOS); chat.save(OUT/'CAP_SOURCE_AUDIT_CONTACT_CHAT.png')
print(OUT/'CAP_SOURCE_AUDIT_CONTACT_CHAT.png')
