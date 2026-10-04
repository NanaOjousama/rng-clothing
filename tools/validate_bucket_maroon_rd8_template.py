#!/usr/bin/env python3
from pathlib import Path
from PIL import Image
import hashlib,json
ROOT=Path('/run/media/deck/USD00/RNG_clothing'); TD=ROOT/'authored/templates/bucket_maroon_rd8'
m=json.loads((TD/'frame_manifest.json').read_text()); c=json.loads((ROOT/'generator/data/templates/bucket_maroon_rd8.json').read_text()); a=json.loads((TD/'attachments/chin_strap/manifest.json').read_text()); r=json.loads((ROOT/'generator/data/headwear/bucket_maroon_rd8_roll_matrix.json').read_text())
assert m['id']==c['id']=='bucket_maroon_rd8'; assert m['runtimeAuthority']==['front','right','back','left']; assert set(m['evidenceOnly'])=={'front_right','back_right','back_left','front_left'}
assert m['optionalAttachments']==['chin_strap']; assert c['optionalAttachments']['chin_strap']['baseRequired'] is False; assert r['axes']['attachment']=={'none':65,'chin_strap':35}
for name,rec in m['frames'].items():
 p=ROOT/rec['path']; im=Image.open(p).convert('RGBA'); assert im.size==(24,24); assert hashlib.sha256(p.read_bytes()).hexdigest()==rec['sha256']; assert hashlib.sha256(im.getchannel('A').tobytes()).hexdigest()==rec['alphaSha256']
for view in m['runtimeAuthority']:
 base=Image.open(TD/f'{view}.png').convert('RGBA'); ov=Image.open(TD/'attachments/chin_strap'/f'{view}.png').convert('RGBA'); full=Image.open(TD/f'{view}_with_strap_source.png').convert('RGBA'); recon=base.copy(); recon.alpha_composite(ov)
 assert recon.tobytes()==full.tobytes(), f'{view}: base+strap != approved full source'
 assert sum(1 for px in ov.getdata() if px[3])==a['views'][view]['overlayOpaqueCells']
reg=json.loads((ROOT/'generator/data/templates/index.json').read_text())['templates']['bucket_maroon_rd8']; assert reg['humanArtApproved'] is True and reg['humanArtApprovalRequired'] is False and reg['esmWearApprovalRequired'] is True
print('PASS bucket_maroon_rd8: strap-off base locked; chin_strap optional roll 35%; base+strap exactly reconstructs all 4 approved cardinals; diagonals evidence-only; wear QC still gated')
