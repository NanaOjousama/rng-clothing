#!/usr/bin/env python3
from pathlib import Path
import json,hashlib,sys
ROOT=Path(__file__).resolve().parents[1]; sys.path.insert(0,str(ROOT))
from generator.png_utils import read_rgba_png
TD=ROOT/'authored/templates/bucket_sf01_rd8'
m=json.loads((TD/'frame_manifest.json').read_text()); c=json.loads((ROOT/'generator/data/templates/bucket_sf01_rd8.json').read_text()); lib=json.loads((ROOT/'generator/data/headwear/bucket_hat_approved_library.json').read_text())
assert m['id']==c['id']=='bucket_sf01_rd8'
assert m['runtimeAuthority']==['front','right','back','left']
assert set(m['evidenceOnly'])=={'front_right','back_right','back_left','front_left'}
assert c['geometryLock']['forbidResample'] is True
for name,rec in m['frames'].items():
    p=ROOT/rec['path']; im=read_rgba_png(p); assert (im['width'],im['height'])==(24,24); assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['sha256']
front_src=ROOT/m['frontAuthority']; assert hashlib.sha256(front_src.read_bytes()).hexdigest()==m['frames']['front']['sourceSha256']
g=lib['constructionGroups']['sf_contact_01']; assert g['status']=='DIRECTIONAL_PENDING_ESM_WEAR_QC' and g['rollWeight']==0 and g['authority']=='generator/data/templates/bucket_sf01_rd8.json'
reg=json.loads((ROOT/'generator/data/templates/index.json').read_text())['templates']['bucket_sf01_rd8']; assert reg['humanArtApproved'] is True and reg['esmWearApprovalRequired'] is True
print('PASS bucket_sf01_rd8: exact approved front + user-supplied RD8 cardinals locked at native pixels; production weight 0; ESM wear QC pending')
