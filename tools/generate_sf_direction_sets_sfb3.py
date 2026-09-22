#!/usr/bin/env python3
from pathlib import Path
import json, urllib.request, sys, time
ROOT=Path('/run/media/deck/USD00/RNG_clothing')
SRCMETA=ROOT/'experiments/spritefusion_beanie_material_rescale_test_01/metadata.json'
OUT=ROOT/'experiments/sfb3_spritefusion_directions'
OUT.mkdir(parents=True,exist_ok=True)
KEY=Path('/home/deck/Documents/spritefusionapi.txt').read_text().strip()
records=json.loads(SRCMETA.read_text())['records'][:8]

def request_direction_set(asset_id, outdir):
    outdir.mkdir(parents=True,exist_ok=True)
    body={'operation':'direction-set','inputs':[{'asset_id':asset_id}],'size':16}
    req=urllib.request.Request(
        'https://www.spritefusion.com/api/v1/generate',
        data=json.dumps(body).encode(),
        headers={'Authorization':'Bearer '+KEY,'Content-Type':'application/json',
                 'Accept':'text/event-stream','User-Agent':'RNG-Clothing-Generator/1.0'},
        method='POST')
    events=[]
    with urllib.request.urlopen(req,timeout=180) as resp:
        for raw in resp:
            line=raw.decode('utf-8','replace').strip()
            if not line.startswith('data:'): continue
            payload=line[5:].strip()
            if not payload: continue
            e=json.loads(payload); events.append(e)
            if e.get('type')=='started':
                print('START',asset_id,e.get('request_id'),flush=True)
            elif e.get('type')=='output':
                a=e.get('asset',{})
                print('OUT',a.get('action',{}).get('direction'),a.get('width'),a.get('height'),flush=True)
            elif e.get('type')=='completed':
                print('DONE',asset_id,e.get('credits',{}).get('remaining'),flush=True)
    (outdir/'events.json').write_text(json.dumps(events,indent=2)+'\n')
    return events

def download(events,outdir):
    items=[]
    for e in events:
        if e.get('type')!='output': continue
        a=e['asset']; direction=a.get('action',{}).get('direction')
        req=urllib.request.Request(a['assetUrl'],headers={
            'Authorization':'Bearer '+KEY,'User-Agent':'RNG-Clothing-Generator/1.0',
            'Accept':'image/png,*/*'})
        with urllib.request.urlopen(req,timeout=60) as rr:
            data=rr.read()
        dest=outdir/f'{direction}.png'
        dest.write_bytes(data)
        items.append({'direction':direction,'asset_id':a['id'],
                      'width':a['width'],'height':a['height'],
                      'path':str(dest.relative_to(ROOT))})
    (outdir/'metadata.json').write_text(json.dumps({
        'cardinalMap':{'front':'S','right':'E','left':'W','back':'N'},
        'items':items
    },indent=2)+'\n')
    return items

allsets=[]
for i,rec in enumerate(records):
    ddir=OUT/f'SF{i+1:02d}'
    if (ddir/'metadata.json').exists():
        print('SKIP existing',i+1,flush=True)
        cached=json.loads((ddir/'metadata.json').read_text())
        items=cached.get('items',cached.get('records',[]))
    else:
        events=request_direction_set(rec['asset_id'],ddir)
        items=download(events,ddir)
    allsets.append({'id':f'SF{i+1:02d}','source_asset_id':rec['asset_id'],'items':items})
(OUT/'manifest.json').write_text(json.dumps({
    'schema':'sfb3-spritefusion-direction-sets/v1',
    'operation':'direction-set',
    'requested_size':16,
    'cardinalMap':{'front':'S','right':'E','left':'W','back':'N'},
    'sets':allsets
},indent=2)+'\n')
print('COMPLETE',len(allsets),'direction sets',flush=True)
